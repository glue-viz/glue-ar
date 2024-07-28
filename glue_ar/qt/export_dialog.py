import os
from typing import Dict, List, Tuple

from echo import HasCallbackProperties
from echo.qt import autoconnect_callbacks_to_qt, connect_checkable_button, connect_float_text
from glue.core.state_objects import State
from glue_qt.utils import load_ui
from glue_vispy_viewers.common.vispy_data_viewer import delay_callback
from glue_vispy_viewers.scatter.layer_artist import VispyLayerArtist

from glue_ar.common.export_state import ARExportDialogState, ar_layer_export

from qtpy.QtWidgets import QCheckBox, QDialog, QHBoxLayout, QLabel, QLayout, QLineEdit, QWidget
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

        # TODO: This all feels kinda convoluted
        self._layer_export_states: Dict[str, Dict[str, State]] = {
            layer.layer.label: { name: state_cls() for name, state_cls in ar_layer_export.members[type(layer.state)].items() }
            for layer in layers
        }
        self.state_dictionary = {
            label: list(states.items())[0] for label, states in self._layer_export_states.items()
        }
        self._on_layer_change(layers[0].layer.label)

        self._connections = autoconnect_callbacks_to_qt(self.state, self.ui)
        self._layer_connections = []

        self.ui.button_cancel.clicked.connect(self.reject)
        self.ui.button_ok.clicked.connect(self.accept)

        self.state.add_callback('layer', self._on_layer_change)
        self.state.add_callback('filetype', self._on_filetype_change)
        self.state.add_callback('method', self._on_method_change)

    def _layer_for_label(self, label: str) -> VispyLayerArtist:
        return next(layer for layer in self.viewer.layers if layer.layer.label == label)

    def _widgets_for_property(self,
                              instance: HasCallbackProperties,
                              property: str,
                              display_name: str) -> List[QWidget]:
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

    def _clear_layout(self, layout: QLayout):
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

    def _on_layer_change(self, layer_name: str):
        method, state = self.state_dictionary[layer_name]
        layer = self._layer_for_label(layer_name)
        method_names = list(ar_layer_export.members[type(layer.state)].keys())

        with delay_callback(self.state, 'method'):
            self.state.method_helper.choices = method_names
            method_change = method != self.state.method
            self.state.method = method
        multiple_methods = len(method_names) > 1
        self.ui.label_method.setVisible(multiple_methods)
        self.ui.combosel_method.setVisible(multiple_methods)
        if not method_change:
            self._update_layer_ui(state)

    def _update_layer_ui(self, state: State):
        self._clear_layer_layout()
        self._layer_connections = []
        for property in state.callback_properties():
            row = QHBoxLayout()
            name = display_name(property)
            widgets = self._widgets_for_property(state, property, name)
            for widget in widgets:
                row.addWidget(widget)
            self.ui.layer_layout.addRow(row)

    def _on_filetype_change(self, filetype: str):
        gl = filetype.lower() in ["gltf", "glb"]
        self.ui.combosel_compression.setVisible(gl)
        self.ui.label_compression_message.setVisible(gl)

    def _on_method_change(self, method_name: str):
        state = self._layer_export_states[self.state.layer][method_name]
        self.state_dictionary[self.state.layer] = (method_name, state)
        self._update_layer_ui(state)
