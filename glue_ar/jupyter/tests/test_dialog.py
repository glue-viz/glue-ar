from pytest import importorskip
from unittest.mock import MagicMock
from typing import cast

importorskip("glue_jupyter")

from glue_jupyter import JupyterApplication
# We can't use the Jupyter vispy widget for these tests until
# https://github.com/glue-viz/glue-vispy-viewers/pull/388 is released
from glue_jupyter.ipyvolume.volume import IpyvolumeVolumeView
from ipyvuetify import Checkbox

from glue_ar.common.tests.test_base_dialog import BaseExportDialogTest, DummyState
from glue_ar.jupyter.export_dialog import JupyterARExportDialog, NumberField


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
        assert self.dialog.compression_items == [
            {"text": "None", "value": 0},
            {"text": "Draco", "value": 1},
            {"text": "Meshoptimizer", "value": 2}
        ]
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
        assert self.dialog.show_compression
        assert self.dialog.show_modelviewer

        state.filetype = "USDA"
        assert not self.dialog.show_compression
        assert not self.dialog.show_modelviewer

        state.filetype = "STL"
        assert not self.dialog.show_compression
        assert not self.dialog.show_modelviewer

        state.filetype = "glTF"
        assert self.dialog.show_compression
        assert self.dialog.show_modelviewer

    def test_widgets_for_property(self):
        state = DummyState()

        int_widgets = self.dialog.widgets_for_property(state, "cb_int", "Int CB")
        assert len(int_widgets) == 1
        widget = int_widgets[0]
        assert isinstance(widget, NumberField)
        assert widget.label == "Int CB"
        assert widget.value == "0"
        assert widget.number_type is int
        assert widget.error_message == "You must enter a valid integer"

        float_widgets = self.dialog.widgets_for_property(state, "cb_float", "Float CB")
        assert len(float_widgets) == 1
        widget = float_widgets[0]
        assert isinstance(widget, NumberField)
        assert widget.label == "Float CB"
        assert widget.value == "1.7"
        assert widget.number_type is float
        assert widget.error_message == "You must enter a valid number"

        bool_widgets = self.dialog.widgets_for_property(state, "cb_bool", "Bool CB")
        assert len(bool_widgets) == 1
        widget = bool_widgets[0]
        assert isinstance(widget, Checkbox)
        assert widget.label == "Bool CB"
        assert widget.value is False

    def test_update_layer_ui(self):
        state = DummyState()
        self.dialog._update_layer_ui(state)
        assert len(self.dialog.layer_layout.children) == 3

    def test_layer_change_ui(self):
        state = self.dialog.state

        state.layer = "Scatter Data"
        assert self.dialog.method_selected == 0
        assert self.dialog.method_items == [{"text": "Scatter", "value": 0}]
        assert not self.dialog.has_layer_options

        state.layer = "Volume Data"
        assert self.dialog.method_items[self.dialog.method_selected]["text"] == state.method
        assert set([item["text"] for item in self.dialog.method_items]) == {"Isosurface", "Voxel"}
        assert self.dialog.has_layer_options

        state.layer = "Scatter Data"
        assert self.dialog.method_selected == 0
        assert self.dialog.method_items == [{"text": "Scatter", "value": 0}]
        assert not self.dialog.has_layer_options

    def test_on_cancel(self):
        self.dialog.vue_cancel_dialog()
        assert len(self.dialog.state_dictionary) == 0
        assert not self.dialog.dialog_open
        self.on_cancel.assert_called_once_with()

    def test_on_export(self):
        self.dialog.vue_export_viewer()
        assert not self.dialog.dialog_open
        self.on_export.assert_called_once_with()
