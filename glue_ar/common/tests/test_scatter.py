from glue.core import Data
from glue_qt.app import GlueApplication
from glue_vispy_viewers.scatter.qt.scatter_viewer import VispyScatterViewer
from itertools import product
from math import sqrt
from numpy import array, array_equal, nan, ones
import pytest
from typing import cast

from glue_ar.common.scatter import scatter_layer_mask


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


# TODO: Making this a fixture caused problems the wrapped C/C++ object
# defining the viewer being deleted. Can we fix that?
def _scatter_mask_viewer(application: GlueApplication, scatter_mask_data: Data) -> VispyScatterViewer:
    application.data_collection.append(scatter_mask_data)
    viewer = cast(VispyScatterViewer, application.new_data_viewer(VispyScatterViewer, data=scatter_mask_data))
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


@pytest.mark.parametrize("clip,size,color", product((True, False), repeat=3))
def test_scatter_mask_bounds(scatter_mask_data, clip, size, color):
    application = GlueApplication()
    viewer = _scatter_mask_viewer(application, scatter_mask_data)
    expected = ones(30).astype(bool)
    if clip:
        valid_x = lambda value: value >= 10 and value <= 35
        expected_x = array([valid_x(t) for t in scatter_mask_data['x']])
        valid_y = lambda value: value >= 100 and value <= 150 
        expected_y = array([valid_y(t) for t in scatter_mask_data['y']])
        valid_z = lambda value: value >= -45 and value <= -20
        expected_z = array([valid_z(t) for t in scatter_mask_data['z']])
        expected &= (expected_x & expected_y & expected_z)
    if size:
        viewer.layers[0].state.size_attribute = scatter_mask_data.id['size']
        viewer.layers[0].state.size_mode = "Linear"
        expected &= array([i not in (2, 5, 6, 11) for i in range(scatter_mask_data.size)])
    if color:
        viewer.layers[0].state.cmap_attribute = scatter_mask_data.id['color']
        viewer.layers[0].state.color_mode = "Linear"
        expected &= array([i not in (1, 5, 6, 24) for i in range(scatter_mask_data.size)])
    viewer_state = viewer.state
    bounds = [
        (viewer_state.x_min, viewer_state.x_max),
        (viewer_state.y_min, viewer_state.y_max),
        (viewer_state.z_min, viewer_state.z_max)]
    mask = scatter_layer_mask(viewer.state,
                              viewer.layers[0].state,
                              bounds=bounds,
                              clip_to_bounds=clip)
    if any((clip, size, color)):
        assert array_equal(expected, mask)
    else:
        assert mask is None
