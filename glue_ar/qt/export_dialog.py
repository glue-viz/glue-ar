import os
from typing import Dict, List, Tuple

from echo import HasCallbackProperties
from echo.qt import autoconnect_callbacks_to_qt, connect_checkable_button, connect_float_text
from glue.core.state_objects import State
from glue_qt.utils import load_ui
from glue_vispy_viewers.common.vispy_data_viewer import delay_callback
from glue_vispy_viewers.scatter.layer_artist import VispyLayerArtist

from glue_ar.common.export_options import ar_layer_export
from glue_ar.common.export_state import ARExportDialogState

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

        self._layer_export_states: Dict[str, Dict[str, State]] = {
            self.state.label_for_layer(layer): {}
            for layer in layers
        }

        self.state_dictionary: Dict[str, Tuple[str, State]] = {}
        self._on_layer_change(self.state.layer)
        for layer in layers:
            method = self.state.method
            label = self.state.label_for_layer(layer)
            if label in self.state_dictionary:
                _, state = self.state_dictionary[label]
            else:
                states = ar_layer_export.export_state_classes(type(layer.state))
                state_cls = next((t[1] for t in states if t[0] == self.state.method), None)
                if state_cls is None:
                    method_names = ar_layer_export.method_names(type(layer.state), self.state.filetype)
                    method = method_names[0]
                    state_cls = next(t[1] for t in states if t[0] == method)
                state = state_cls()
                self.state_dictionary[label] = (method, state)
            self._layer_export_states[label][method] = state

        self._connections = autoconnect_callbacks_to_qt(self.state, self.ui)
        self._layer_connections = []

        self.ui.button_cancel.clicked.connect(self.reject)
        self.ui.button_ok.clicked.connect(self.accept)

        self.state.add_callback('layer', self._on_layer_change)
        self.state.add_callback('filetype', self._on_filetype_change)
        self.state.add_callback('method', self._on_method_change)

    def _layer_for_label(self, label: str) -> VispyLayerArtist:
        return next(layer for layer in self.state.layers if self.state.label_for_layer(layer) == label)

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
        layer = self._layer_for_label(layer_name)
        layer_state_cls = type(layer.state)
        method_names = ar_layer_export.method_names(layer_state_cls, self.state.filetype)
        if layer_name in self.state_dictionary:
            method, state = self.state_dictionary[layer_name]
        else:
            method = method_names[0]
            state = ar_layer_export.options_class(layer_state_cls, method)()
            self.state_dictionary[layer_name] = (method, state)

        print(method_names)
        print(method)
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
        if method_name in self._layer_export_states[self.state.layer]:
            state = self._layer_export_states[self.state.layer][method_name]
        else:
            layer = self._layer_for_label(self.state.layer)
            states = ar_layer_export.export_state_classes(type(layer.state))
            state_cls = next(t[1] for t in states if t[0] == method_name)
            state = state_cls()
            self._layer_export_states[self.state.layer][method_name] = state
        self.state_dictionary[self.state.layer] = (method_name, state)
        self._update_layer_ui(state)
