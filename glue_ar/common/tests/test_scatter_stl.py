from sys import platform
from tempfile import NamedTemporaryFile

import pytest
from stl import Mesh

from glue_ar.common.export import export_viewer
from glue_ar.common.tests.helpers import APP_VIEWER_OPTIONS
from glue_ar.common.tests.test_scatter import BaseScatterTest
from glue_ar.utils import layers_to_export, mask_for_bounds, xyz_bounds, xyz_for_layer


class TestScatterSTL(BaseScatterTest):

    @pytest.mark.parametrize("app_type,viewer_type", APP_VIEWER_OPTIONS)
    def test_basic_export(self, app_type: str, viewer_type: str):
        if app_type == "jupyter" and viewer_type == "vispy" and platform == "win32":
            return
        self.basic_setup(app_type, viewer_type)
        bounds = xyz_bounds(self.viewer.state, with_resolution=False)
        self.tmpfile = NamedTemporaryFile(suffix=".stl", delete=False)
        self.tmpfile.close()
        layer_states = [layer.state for layer in layers_to_export(self.viewer)]
        export_viewer(self.viewer.state,
                      layer_states=layer_states,
                      bounds=bounds,
                      state_dictionary=self.state_dictionary,
                      filepath=self.tmpfile.name,
                      compression=None)

        stl = Mesh.from_file(self.tmpfile.name)

        mask = mask_for_bounds(self.viewer.state, layer.state, bounds)
        data = xyz_for_layer(self.viewer.state, layer.state,
                             preserve_aspect=self.viewer.state.native_aspect,
                             mask=mask,
                             scaled=True)

        print(self.data1['x'][0], self.data1['y'][0], self.data1['z'][0])
        print(stl.points[:82])
        assert False
