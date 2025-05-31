from typing import cast

from pytest import importorskip

importorskip("glue_qt")

from glue_qt.app import GlueApplication
from glue_vispy_viewers.volume.qt.volume_viewer import VispyVolumeViewer

from glue_ar.common.tests.test_base_dialog import BaseExportDialogTest, DummyState
from glue_ar.common.scatter_export_options import ARVispyScatterExportOptions
from glue_ar.qt.export_dialog import QtARExportDialog
from glue_ar.qt.tests.utils import combobox_options


class TestQtExportDialog(BaseExportDialogTest):

    app: GlueApplication
    dialog: QtARExportDialog

    def setup_method(self, method):
        self.app = GlueApplication()
        self._setup_data()

        # We use a volume viewer because it can support both volume and scatter layers
        self.viewer: VispyVolumeViewer = cast(VispyVolumeViewer,
                                              self.app.new_data_viewer(VispyVolumeViewer, data=self.volume_data))
        self.viewer.add_data(self.scatter_data)

        self.dialog = QtARExportDialog(parent=self.viewer, viewer=self.viewer)
        self.dialog.show()

    def teardown_method(self, method):
        self.dialog.close()

    def test_default_ui(self):
        ui = self.dialog.ui
        assert ui.button_cancel.isVisible()
        assert ui.button_ok.isVisible()
        assert ui.combosel_compression.isVisible()
        assert ui.label_compression_message.isVisible()

        compression_options = combobox_options(ui.combosel_compression)
        assert compression_options == ["None", "Draco", "Meshoptimizer"]

    def test_filetype_change(self):
        state = self.dialog.state
        ui = self.dialog.ui

        state.filetype = "USDC"
        assert not ui.combosel_compression.isVisible()
        assert not ui.label_compression_message.isVisible()

        state.filetype = "USDA"
        assert not ui.combosel_compression.isVisible()
        assert not ui.label_compression_message.isVisible()

        state.filetype = "glTF"
        assert ui.combosel_compression.isVisible()
        assert ui.label_compression_message.isVisible()

        state.filetype = "USDA"
        assert not ui.combosel_compression.isVisible()
        assert not ui.label_compression_message.isVisible()

        state.filetype = "STL"
        assert not ui.combosel_compression.isVisible()
        assert not ui.label_compression_message.isVisible()

        state.filetype = "glTF"
        assert ui.combosel_compression.isVisible()
        assert ui.label_compression_message.isVisible()

    def test_update_layer_ui(self):
        state = DummyState()
        self.dialog._update_layer_ui(state)
        assert self.dialog.ui.layer_layout.count() == 3

        state = ARVispyScatterExportOptions()
        self.dialog._update_layer_ui(state)
        assert self.dialog.ui.layer_layout.count() == 2

    def test_clear_layout(self):
        self.dialog._clear_layer_layout()
        assert self.dialog.ui.layer_layout.isEmpty()
        assert self.dialog._layer_connections == []

    def test_layer_change_ui(self):
        state = self.dialog.state
        ui = self.dialog.ui

        state.layer = "Scatter Data"
        assert ui.combosel_method.currentText() == state.method
        assert combobox_options(ui.combosel_method) == ["Scatter", "Points"]
        assert ui.label_method.isVisible()
        assert ui.combosel_method.isVisible()

        state.layer = "Volume Data"
        assert set(combobox_options(ui.combosel_method)) == {"Isosurface", "Voxel"}
        assert ui.combosel_method.currentText() == state.method
        assert ui.label_method.isVisible()
        assert ui.combosel_method.isVisible()

        state.layer = "Scatter Data"
        assert ui.combosel_method.currentText() == state.method
        assert combobox_options(ui.combosel_method) == ["Scatter", "Points"]
        assert ui.label_method.isVisible()
        assert ui.combosel_method.isVisible()
