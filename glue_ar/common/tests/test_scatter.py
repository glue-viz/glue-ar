from inspect import getfullargspec
from itertools import product
from math import sqrt
from numpy import array, array_equal, nan, ones
from os import remove
import pytest
from random import random, randint, seed
from typing import cast, Dict, Tuple, Type, Union

from glue.core import Data
from glue.core.state_objects import State
from glue.viewers.common.viewer import Viewer
from glue_ar.common.tests.helpers import APP_VIEWER_OPTIONS
from glue_ar.utils import NoneType

try:
    from glue_jupyter import JupyterApplication
    from glue_jupyter.ipyvolume.scatter import IpyvolumeScatterView
    from glue_vispy_viewers.scatter.jupyter import JupyterVispyScatterViewer
except ImportError:
    JupyterApplication = NoneType
    IpyvolumeScatterView = NoneType
    JupyterVispyScatterViewer = NoneType
try:
    from glue_qt.app import GlueApplication
    from glue_vispy_viewers.scatter.qt.scatter_viewer import VispyScatterViewer
except ImportError:
    GlueApplication = NoneType
    VispyScatterViewer = NoneType


Application = Union[GlueApplication, JupyterApplication]
ScatterViewer = Union[Type[VispyScatterViewer], Type[JupyterVispyScatterViewer], Type[IpyvolumeScatterView]]

from glue_ar.common.scatter import scatter_layer_mask
from glue_ar.common.scatter_export_options import ARIpyvolumeScatterExportOptions, ARVispyScatterExportOptions
from glue_ar.utils import export_label_for_layer


@pytest.fixture
def scatter_mask_data():
    x_values = range(10, 40)
    y_values = range(130, 160)
    z_values = range(-50, -20)
    n = 30

    color_nan_indices = (1, 5, 6, 24)
    color_values = array([sqrt(t) for t in x_values])
    for index in color_nan_indices:
        color_values[index] = nan

    size_nan_indices = (2, 5, 6, 11)
    size_values = [t / n for t in x_values]
    for index in size_nan_indices:
        size_values[index] = nan

    return Data(x=x_values, y=y_values, z=z_values,
                color=color_values, size=size_values)


def _create_application(app_type: str) -> Application:
    if app_type == "qt":
        return GlueApplication()
    elif app_type == "jupyter":
        return JupyterApplication()
    else:
        raise ValueError("Application type should be either qt or jupyter")


def _viewer_class(app_type: str, viewer_type: str) -> ScatterViewer:
    if viewer_type == "vispy":
        return VispyScatterViewer if app_type == "qt" else JupyterVispyScatterViewer
    elif viewer_type == "ipyvolume":
        return IpyvolumeScatterView
    else:
        raise ValueError("Viewer type should be either vispy or ipyvolume")


# TODO: Making this a fixture caused problems with the wrapped C/C++ object
# defining the viewer being deleted. Can we fix that?
def _scatter_mask_viewer(application: Application,
                         scatter_mask_data: Data,
                         app_type: str,
                         viewer_type: str) -> ScatterViewer:
    application.data_collection.append(scatter_mask_data)
    viewer_cls = _viewer_class(app_type, viewer_type)
    viewer = cast(viewer_cls, application.new_data_viewer(viewer_cls, data=scatter_mask_data))
    viewer.state.x_att = scatter_mask_data.id['x']
    viewer.state.y_att = scatter_mask_data.id['y']
    viewer.state.z_att = scatter_mask_data.id['z']
    viewer.state.x_min = 10
    viewer.state.x_max = 35
    viewer.state.y_min = 100
    viewer.state.y_max = 150
    viewer.state.z_min = -45
    viewer.state.z_max = -20
    return viewer


scatter_mask_options = product(product((True, False), repeat=3), APP_VIEWER_OPTIONS)
scatter_mask_options = [[item for lst in lsts for item in lst] for lsts in scatter_mask_options]


@pytest.mark.parametrize("clip,size,color,app_type,viewer_type", scatter_mask_options)
def test_scatter_mask_bounds(scatter_mask_data, clip, size, color, app_type, viewer_type):
    application = _create_application(app_type)
    viewer = _scatter_mask_viewer(application, scatter_mask_data, app_type, viewer_type)
    vispy = viewer_type == "vispy"
    expected = ones(30).astype(bool)
    layer_state = viewer.layers[0].state
    if clip:
        expected_x = array([(t >= 10 and t <= 35) for t in scatter_mask_data['x']])
        expected_y = array([(t >= 100 and t <= 150) for t in scatter_mask_data['y']])
        expected_z = array([t >= -45 and t <= -20 for t in scatter_mask_data['z']])
        expected &= (expected_x & expected_y & expected_z)
    if size:
        size_att = "size_attribute" if vispy else "size_att"
        setattr(layer_state, size_att, scatter_mask_data.id['size'])
        layer_state.size_mode = "Linear"
        expected &= array([i not in (2, 5, 6, 11) for i in range(scatter_mask_data.size)])
    if color:
        cmap_att = "cmap_attribute" if vispy else "cmap_att"
        cmap_mode_att = "color_mode" if vispy else "cmap_mode"
        setattr(layer_state, cmap_att, scatter_mask_data.id['color'])
        setattr(layer_state, cmap_mode_att, "Linear")
        layer_state.color_mode = "Linear"
        expected &= array([i not in (1, 5, 6, 24) for i in range(scatter_mask_data.size)])
    viewer_state = viewer.state
    bounds = [
        (viewer_state.x_min, viewer_state.x_max),
        (viewer_state.y_min, viewer_state.y_max),
        (viewer_state.z_min, viewer_state.z_max)]
    mask = scatter_layer_mask(viewer.state,
                              layer_state,
                              bounds=bounds,
                              clip_to_bounds=clip)
    if any((clip, size, color)):
        assert array_equal(expected, mask)
    else:
        assert mask is None


class BaseScatterTest:

    # We manually invoke this function in both downstream `test_basic_export` methods
    # which is bad, but is to work around an issue with the CI on Windows.
    # I will look for a better solution to this.
    def basic_setup(self, app_type: str, viewer_type: str):
        self.app_type = app_type
        self.viewer_type = viewer_type

        seed(186)
        self.n = 40
        x1 = [random() * 5 for _ in range(self.n)]
        y1 = [random() for _ in range(self.n)]
        z1 = [randint(1, 30) for _ in range(self.n)]
        self.data1 = Data(x=x1, y=y1, z=z1, label="Scatter Data 1")
        self.data1.style.color = "#fedcba"
        self.app = _create_application(self.app_type)
        self.app.data_collection.append(self.data1)
        self.viewer: Viewer = self.app.new_data_viewer(_viewer_class(self.app_type, self.viewer_type))
        self.viewer.add_data(self.data1)

        x2 = [random() * 7 for _ in range(self.n)]
        y2 = [randint(100, 200) for _ in range(self.n)]
        z2 = [random() for _ in range(self.n)]
        self.data2 = Data(x=x2, y=y2, z=z2, label="Scatter Data 2")

        self.viewer.state.x_att = self.data1.id['x']
        self.viewer.state.y_att = self.data1.id['y']
        self.viewer.state.z_att = self.data1.id['z']
        self.state_dictionary = self._basic_state_dictionary(viewer_type)

    def teardown_method(self, method):
        if getattr(self, "tmpfile", None) is not None:
            self.tmpfile.close()
            remove(self.tmpfile.name)
        if hasattr(self, 'viewer'):
            if hasattr(self.viewer, "close"):
                spec = getfullargspec(self.viewer.close)
                kwargs = spec[4]
                try:
                    if "warn" in kwargs:
                        self.viewer.close(warn=False)
                    else:
                        self.viewer.close()
                except NotImplementedError:
                    pass
            self.viewer = None
        if hasattr(self, 'app'):
            if hasattr(self.app, 'close'):
                self.app.close()
        self.app = None

    def _basic_state_dictionary(self, viewer_type: str) -> Dict[str, Tuple[str, State]]:
        if viewer_type == "vispy":
            def state_maker():
                return ARVispyScatterExportOptions(resolution=15,
                                                   log_points_per_mesh=0)
        elif viewer_type == "ipyvolume":
            def state_maker():
                return ARIpyvolumeScatterExportOptions(log_points_per_mesh=0)
        else:
            raise ValueError("Viewer type should be either vispy or ipyvolume")

        return {
            export_label_for_layer(layer): ("Scatter", state_maker())
            for layer in self.viewer.layers
        }

    def _export_state_class(self, viewer_type: str):
        return ARIpyvolumeScatterExportOptions if viewer_type == "ipyvolume" else ARVispyScatterExportOptions
