import os

from echo import ignore_callback
from echo.qt import autoconnect_callbacks_to_qt, connect_checkable_button, connect_float_text
from glue_qt.utils import load_ui

from glue_ar.common.export_state import ARExportDialogState, ar_layer_export

from qtpy.QtWidgets import QCheckBox, QDialog, QHBoxLayout, QLabel, QLineEdit
from qtpy.QtGui import QIntValidator, QDoubleValidator


__all__ = ['ARExportDialog']


def display_name(prop):
    return prop.replace("_", " ").capitalize()


class ARExportDialog(QDialog):

    def __init__(self, parent=None, viewer=None):

        super(ARExportDialog, self).__init__(parent=parent)

        self.viewer = viewer
        layers = [layer for layer in self.viewer.layers if layer.enabled and layer.state.visible]
        self.state = ARExportDialogState(layers)
        self.ui = load_ui('export_dialog.ui', self, directory=os.path.dirname(__file__))

        self._layer_methods = {
            layer.layer.label: list(ar_layer_export.members[type(layer.state)].keys())
            for layer in layers
        }
        self.state_dictionary = {
            layer.layer.label: ar_layer_export.members[type(layer.state)][self._layer_methods[layer.layer.label][0]]()
            for layer in layers
        }
        self._update_layer_ui(self.state_dictionary[layers[0].layer.label])

        self._connections = autoconnect_callbacks_to_qt(self.state, self.ui)
        self._layer_connections = []

        self.ui.button_cancel.clicked.connect(self.reject)
        self.ui.button_ok.clicked.connect(self.accept)

        self.state.add_callback('layer', self._on_layer_change)
        self.state.add_callback('filetype', self._on_filetype_change)
        self.state.add_callback('method', self._on_method_change)

    def _widgets_for_property(self, instance, property, display_name):
        value = getattr(instance, property)
        t = type(value)
        if t is bool:
            widget = QCheckBox()
            widget.setChecked(value)
            widget.setText(display_name)
            self._layer_connections.append(connect_checkable_button(instance, property, widget))
            return [widget]
        elif t in [int, float]:
            label = QLabel()
            prompt = f"{display_name}:"
            label.setText(prompt)
            widget = QLineEdit()
            validator = QIntValidator() if t is int else QDoubleValidator()
            widget.setText(str(value))
            widget.setValidator(validator)
            self._layer_connections.append(connect_float_text(instance, property, widget))
            return [label, widget]
        else:
            return []

    def _clear_layout(self, layout):
        if layout is not None:
            while layout.count():
                item = layout.takeAt(0)
                widget = item.widget()
                if widget is not None:
                    widget.deleteLater()
                else:
                    self._clear_layout(item.layout())

    def _clear_layer_layout(self):
        self._clear_layout(self.ui.layer_layout)

    def _on_layer_change(self, layer):
        state = self.state_dictionary[layer]
        method_options = ar_layer_export.members[type(layer.state)].values()
        method_names = [option.name for option in method_options]
        self.state.method = self._layer_methods.get(layer, method_names[0])
        print(method_names)
        self.state.method_helper.choices = method_names
        self._update_layer_ui(state)

    def _update_layer_ui(self, state):
        self._clear_layer_layout()
        self._layer_connections = []
        for property in state.callback_properties():
            row = QHBoxLayout()
            name = display_name(property)
            widgets = self._widgets_for_property(state, property, name)
            for widget in widgets:
                row.addWidget(widget)
            self.ui.layer_layout.addRow(row)

    def _on_filetype_change(self, filetype):
        gl = filetype.lower() in ["gltf", "glb"]
        self.ui.combosel_compression.setVisible(gl)

    def _on_method_change(self, method_name):
        self._layer_methods[self.state.layer] = method_name
        state = self.state_dictionary[self.state.layer]
        self._update_layer_ui(state)
