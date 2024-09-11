import os
from typing import List

from echo import HasCallbackProperties
from echo.qt import autoconnect_callbacks_to_qt, connect_checkable_button, connect_float_text
from glue.core.state_objects import State
from glue_qt.utils import load_ui
from glue_ar.common.export_dialog_base import ARExportDialogBase

from qtpy.QtWidgets import QCheckBox, QDialog, QFormLayout, QHBoxLayout, QLabel, QLayout, QLineEdit, QWidget
from qtpy.QtGui import QIntValidator, QDoubleValidator


__all__ = ['QtARExportDialog']


class QtARExportDialog(ARExportDialogBase, QDialog):

    def __init__(self, parent=None, viewer=None):

        ARExportDialogBase.__init__(self, viewer=viewer)
        QDialog.__init__(self, parent=parent)

        self.ui = load_ui('export_dialog.ui', self, directory=os.path.dirname(__file__))

        self._connections = autoconnect_callbacks_to_qt(self.state, self.ui)
        self._layer_connections = []
        self._on_layer_change(self.state.layer)

        self.ui.button_cancel.clicked.connect(self.reject)
        self.ui.button_ok.clicked.connect(self.accept)

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
        elif t in (int, float):
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

                layout.removeItem(item)

            if isinstance(layout, QFormLayout):
                self._clear_form_rows(layout)

    def _clear_form_rows(self, layout: QFormLayout):
        if layout is not None:
            while layout.rowCount():
                layout.removeRow(0)

    def _clear_layer_layout(self):
        self._clear_layout(self.ui.layer_layout)

    def _on_layer_change(self, layer_name: str):
        super()._on_layer_change(layer_name)
        multiple_methods = len(self.state.method_helper.choices) > 1
        self.ui.label_method.setVisible(multiple_methods)
        self.ui.combosel_method.setVisible(multiple_methods)

    def _update_layer_ui(self, state: State):
        self._clear_layer_layout()
        self._layer_connections = []
        for property in state.callback_properties():
            row = QHBoxLayout()
            name = self.display_name(property)
            widgets = self._widgets_for_property(state, property, name)
            for widget in widgets:
                row.addWidget(widget)
            self.ui.layer_layout.addRow(row)

    def _on_filetype_change(self, filetype: str):
        super()._on_filetype_change(filetype)
        gl = filetype.lower() in ("gltf", "glb")
        self.ui.combosel_compression.setVisible(gl)
        self.ui.label_compression_message.setVisible(gl)

    def _on_method_change(self, method_name: str):
        super()._on_method_change(method_name)
        state = self._layer_export_states[self.state.layer][method_name]
        self._update_layer_ui(state)
