from pytest import importorskip
from unittest.mock import MagicMock
from typing import cast


importorskip("glue_jupyter")

from glue_jupyter import JupyterApplication
# We can't use the Jupyter vispy widget for these tests until
# https://github.com/glue-viz/glue-vispy-viewers/pull/388 is released
from glue_jupyter.ipyvolume.volume import IpyvolumeVolumeView

from glue_ar.common.tests.test_base_dialog import BaseExportDialogTest, DummyState
from glue_ar.jupyter.export_dialog import JupyterARExportDialog
from glue_ar.tests.helpers import DRACOPY_INSTALLED


class TestJupyterExportDialog(BaseExportDialogTest):

    app: JupyterApplication
    dialog: JupyterARExportDialog

    def setup_method(self, method):
        self.app = JupyterApplication()
        self._setup_data()

        # We use a volume viewer because it can support both volume and scatter layers
        self.viewer: IpyvolumeVolumeView = cast(IpyvolumeVolumeView,
                                                self.app.volshow(widget="ipyvolume", data=self.volume_data))
        self.viewer.add_data(self.scatter_data)

        self.on_cancel = MagicMock()
        self.on_export = MagicMock()
        self.dialog = JupyterARExportDialog(viewer=self.viewer, display=True,
                                            on_cancel=self.on_cancel, on_export=self.on_export)

    def teardown_method(self, method):
        self.dialog.dialog_open = False

    def test_default_ui(self):
        assert self.dialog.dialog_open
        assert self.dialog.layer_items == [
            {"text": "Volume Data", "value": 0},
            {"text": "Scatter Data", "value": 1}
        ]
        assert self.dialog.layer_selected == 0
        compression_items = [{"text": "None", "value": 0}]
        if DRACOPY_INSTALLED:
            compression_items.append({"text": "Draco", "value": 1})
        assert self.dialog.compression_items == compression_items
        assert self.dialog.compression_selected == 0
        assert self.dialog.filetype_items == [
            {"text": "glB", "value": 0},
            {"text": "glTF", "value": 1},
            {"text": "USDZ", "value": 2},
            {"text": "USDC", "value": 3},
            {"text": "USDA", "value": 4},
            {"text": "STL", "value": 5},
        ]
        assert self.dialog.filetype_selected == 0
        assert set([item["text"] for item in self.dialog.method_items]) == {"Isosurface", "Voxel"}
        assert self.dialog.method_selected == 0
        assert self.dialog.has_layer_options

    def test_filetype_change(self):
        state = self.dialog.state

        state.filetype = "USDC"
        assert not self.dialog.show_compression
        assert not self.dialog.show_modelviewer

        state.filetype = "USDA"
        assert not self.dialog.show_compression
        assert not self.dialog.show_modelviewer

        state.filetype = "glTF"
        assert self.dialog.show_modelviewer
        assert self.dialog.show_compression == DRACOPY_INSTALLED

        state.filetype = "USDA"
        assert not self.dialog.show_compression
        assert not self.dialog.show_modelviewer

        state.filetype = "STL"
        assert not self.dialog.show_compression
        assert not self.dialog.show_modelviewer

        state.filetype = "glTF"
        assert self.dialog.show_modelviewer
        assert self.dialog.show_compression == DRACOPY_INSTALLED

    def test_update_layer_ui(self):
        state = DummyState()
        self.dialog._update_layer_ui(state)
        assert len(self.dialog.layer_layout.children) == 3

    def test_layer_change_ui(self):
        state = self.dialog.state

        state.layer = "Scatter Data"
        assert self.dialog.method_selected == 0
        assert self.dialog.method_items == [{"text": "Scatter", "value": 0}]
        assert self.dialog.has_layer_options

        state.layer = "Volume Data"
        assert self.dialog.method_items[self.dialog.method_selected]["text"] == state.method
        assert set([item["text"] for item in self.dialog.method_items]) == {"Isosurface", "Voxel"}
        assert self.dialog.has_layer_options

        state.layer = "Scatter Data"
        assert self.dialog.method_selected == 0
        assert self.dialog.method_items == [{"text": "Scatter", "value": 0}]
        assert self.dialog.has_layer_options

    def test_on_cancel(self):
        self.dialog.vue_cancel_dialog()
        assert len(self.dialog.state_dictionary) == 0
        assert not self.dialog.dialog_open
        self.on_cancel.assert_called_once_with()

    def test_on_export(self):
        self.dialog.vue_export_viewer()
        assert not self.dialog.dialog_open
        self.on_export.assert_called_once_with()
