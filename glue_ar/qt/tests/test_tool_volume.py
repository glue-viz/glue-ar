from itertools import product
from random import random, seed
from typing import cast
from unittest.mock import patch

from glue.core import Data
from glue.core.link_helpers import LinkSame
from glue_qt.app import GlueApplication
from glue_vispy_viewers.volume.qt.volume_viewer import VispyVolumeViewer
from numpy import arange, ones
import pytest

from glue_ar.common.export import export_viewer
from glue_ar.common.scatter_export_options import ARVispyScatterExportOptions
from glue_ar.common.volume_export_options import ARIsosurfaceExportOptions
from glue_ar.qt.export_dialog import QtARExportDialog
from glue_ar.qt.export_tool import QtARExportTool
from glue_ar.qt.tests.utils import dialog_auto_accept_with_options
from glue_ar.utils import export_label_for_layer

class TestVolumeExportTool:

    def setup_method(self, method):
        seed(18)
        self.app = GlueApplication()
        scatter_size = 18
        self.scatter_data = Data(x=[random() for _ in range(scatter_size)],
                                 y=[random() for _ in range(scatter_size)],
                                 z=[random() for _ in range(scatter_size)],
                                 label="Scatter Data")
        self.app.data_collection.append(self.scatter_data)

        self.volume_data = Data(
                label='Volume Data',
                x=arange(24).reshape((2, 3, 4)),
                y=ones((2, 3, 4)),
                z=arange(100, 124).reshape((2, 3, 4)))
        self.app.data_collection.append(self.volume_data)

        # Link pixel axes to scatter
        for i, c in enumerate(('x', 'y', 'z')):
            ri = 2 - i
            c1 = self.volume_data.id[f"Pixel Axis {ri} [{c}]"]
            c2 = self.scatter_data.id[c]
            self.app.data_collection.add_link(LinkSame(c1, c2))
        
        self.viewer: VispyVolumeViewer = cast(VispyVolumeViewer, self.app.new_data_viewer(VispyVolumeViewer, data=self.volume_data))
        self.viewer.add_data(self.scatter_data)

    def teardown_method(self):
        self.viewer.close(warn=False)
        self.app.close()

    def test_toolbar(self):
        toolbar = self.viewer.toolbar
        assert toolbar is not None
        assert "save" in toolbar.tools
        tool = toolbar.tools["save"]
        assert len([subtool for subtool in tool.subtools if isinstance(subtool, QtARExportTool)]) == 1

    @pytest.mark.parametrize("extension,compression", product(("glB", "glTF", "USDA", "USDC"), ("None", "Draco", "Meshoptimizer")))
    def test_tool_export_call(self, extension, compression):
        auto_accept = dialog_auto_accept_with_options(filetype=extension, compression=compression)
        with patch("qtpy.compat.getsavefilename") as fd, \
             patch.object(QtARExportDialog, "exec_", auto_accept), \
             patch.object(QtARExportTool, "_start_worker") as start_worker:
                ext = extension.lower()
                filepath = f"test.{ext}"
                fd.return_value = filepath, ext
                save_tool = self.viewer.toolbar.tools["save"]
                ar_subtool = next(subtool for subtool in save_tool.subtools if isinstance(subtool, QtARExportTool))
                ar_subtool.activate()

                bounds = [
                    (self.viewer.state.x_min, self.viewer.state.x_max, self.viewer.state.resolution),
                    (self.viewer.state.y_min, self.viewer.state.y_max, self.viewer.state.resolution),
                    (self.viewer.state.z_min, self.viewer.state.z_max, self.viewer.state.resolution),
                ]

                # We can't use assert_called_once_with because the state dictionaries
                # aren't recognized as equal
                start_worker.assert_called_once()
                call = start_worker.call_args_list[0]
                assert call.args == (export_viewer,)
                kwargs = call.kwargs
                assert kwargs["viewer_state"] == self.viewer.state
                assert kwargs["bounds"] == bounds
                assert kwargs["filepath"] == filepath
                assert kwargs["compression"] == compression
                state_dict = kwargs["state_dictionary"]
                assert tuple(state_dict.keys()) == ("Volume Data", "Scatter Data")

                scatter_method, scatter_state = state_dict["Scatter Data"]
                assert scatter_method == "Scatter"
                assert isinstance(scatter_state, ARVispyScatterExportOptions)
                assert scatter_state.theta_resolution == 8
                assert scatter_state.phi_resolution == 8

                volume_method, volume_state = state_dict["Volume Data"]
                assert volume_method == "Isosurface"
                assert isinstance(volume_state, ARIsosurfaceExportOptions)
                assert volume_state.isosurface_count == 20
