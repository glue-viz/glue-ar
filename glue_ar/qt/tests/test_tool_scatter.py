from itertools import product
import pytest
from random import randint, random, seed
from typing import cast
from unittest.mock import patch

from glue.core import Data
from glue.core.link_helpers import LinkSame
from glue_qt.app import GlueApplication
from glue_vispy_viewers.scatter.qt.scatter_viewer import VispyScatterViewer

from glue_ar.common.export import export_viewer
from glue_ar.common.scatter_export_options import ARVispyScatterExportOptions
from glue_ar.qt.export_dialog import QtARExportDialog
from glue_ar.qt.export_tool import QtARExportTool
from glue_ar.qt.tests.utils import dialog_auto_accept_with_options


class TestScatterExportTool:

    def setup_method(self, method):
        seed(1607)
        self.app = GlueApplication()
        size_1 = 20
        self.data_1 = Data(x=[random() for _ in range(size_1)],
                           y=[random() for _ in range(size_1)],
                           z=[random() for _ in range(size_1)],
                           label="Scatter Data 1")
        self.app.data_collection.append(self.data_1)
        size_2 = 35
        self.data_2 = Data(x=[randint(0, 10) for _ in range(size_2)],
                           y=[randint(-5, 5) for _ in range(size_2)],
                           z=[randint(100, 200) for _ in range(size_2)],
                           label="Scatter Data 2")
        self.app.data_collection.append(self.data_2)

        for c in ('x', 'y', 'z'):
            c1 = self.data_1.id[c]
            c2 = self.data_2.id[c]
            self.app.data_collection.add_link(LinkSame(c1, c2))

        self.viewer: VispyScatterViewer = cast(VispyScatterViewer,
                                               self.app.new_data_viewer(VispyScatterViewer, data=self.data_1))
        self.viewer.add_data(self.data_2)

    def teardown_method(self):
        self.viewer.close(warn=False)
        self.app.close()

    def test_toolbar(self):
        toolbar = self.viewer.toolbar
        assert toolbar is not None
        assert "save" in toolbar.tools
        tool = toolbar.tools["save"]
        assert len([subtool for subtool in tool.subtools if isinstance(subtool, QtARExportTool)]) == 1

    @pytest.mark.parametrize("extension,compression",
                             product(("glB", "glTF", "USDA", "USDC"), ("None", "Draco", "Meshoptimizer")))
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
                (self.viewer.state.x_min, self.viewer.state.x_max),
                (self.viewer.state.y_min, self.viewer.state.y_max),
                (self.viewer.state.z_min, self.viewer.state.z_max),
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
            assert tuple(state_dict.keys()) == ("Scatter Data 1", "Scatter Data 2")
            for value in state_dict.values():
                assert len(value) == 2
                assert value[0] == "Scatter"
                assert isinstance(value[1], ARVispyScatterExportOptions)
                assert value[1].theta_resolution == 8
                assert value[1].phi_resolution == 8
