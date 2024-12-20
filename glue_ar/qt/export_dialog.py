from math import floor, log
import os
from typing import List, Tuple

from echo import CallbackProperty, HasCallbackProperties, add_callback
from echo.core import remove_callback
from echo.qt import autoconnect_callbacks_to_qt, connect_checkable_button, connect_value
from glue.core.state_objects import State
from glue_qt.utils import load_ui
from qtpy.QtGui import QCursor, QEnterEvent, QIcon
from glue_ar.common.export_dialog_base import ARExportDialogBase

from qtpy.QtCore import Qt, QEvent
from qtpy.QtWidgets import QCheckBox, QDialog, QFormLayout, QHBoxLayout, QLayoutItem, QPushButton, QSpacerItem, QToolTip, QVBoxLayout, QLabel, QLayout, QSizePolicy, QSlider, QWidget

from glue_ar.utils import RESOURCES_DIR


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

    def _doc_button(self, cb_property: CallbackProperty) -> QPushButton:
        button = QPushButton()
        button.setCheckable(False)
        button.setFlat(True)
        icon_path = os.path.join(RESOURCES_DIR, "info.png")
        icon = QIcon(icon_path)
        button.setIcon(icon)
        button.setSizePolicy(QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum))

        # We want the tooltip to show immediately, rather than have a delay
        button.enterEvent = lambda event: self._doc_enter_event(event, cb_property=cb_property)
        button.leaveEvent = self._doc_leave_event
        
        return button 

    def _doc_enter_event(self, event: QEnterEvent, cb_property: CallbackProperty):
        # Make the tooltip be rich text so that it will line wrap
        QToolTip.showText(QCursor.pos(), f"<qt>{cb_property.__doc__}</qt>" or "")

    def _doc_leave_event(self, _event: QEvent):
        QToolTip.hideText()

    def _horizontal_spacer(self) -> QSpacerItem:
        return QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

    def _widgets_for_property(self,
                              instance: HasCallbackProperties,
                              property: str,
                              display_name: str) -> List[Tuple[QWidget]]:
        value = getattr(instance, property)
        instance_type = type(instance)
        cb_property = getattr(instance_type, property)
        t = type(value)
        widgets: List[Tuple[QWidget]] = []
        if t is bool:
            widget = QCheckBox()
            widget.setChecked(value)
            widget.setText(display_name)
            self._layer_connections.append(connect_checkable_button(instance, property, widget))
            if cb_property.__doc__:
                button = self._doc_button(cb_property)
                spacer = self._horizontal_spacer()
                widgets.append((widget, spacer, button))
            else:
                widgets.append((widget,))
        elif t in (int, float):
            widgets: List[Tuple[QWidget]] = []
            label = QLabel()
            prompt = f"{display_name}:"
            label.setText(prompt)
            if cb_property.__doc__:
                info_button = self._doc_button(cb_property)
                spacer = self._horizontal_spacer()
                widgets.append((label, spacer, info_button))
            else:
                widgets.append((label,))
            widget = QSlider()
            policy = QSizePolicy()
            policy.setHorizontalPolicy(QSizePolicy.Policy.Expanding)
            policy.setVerticalPolicy(QSizePolicy.Policy.Fixed)
            widget.setOrientation(Qt.Orientation.Horizontal)

            widget.setSizePolicy(policy)

            value_label = QLabel()
            min = getattr(cb_property, 'min_value', 1 if t is int else 0.01)
            max = getattr(cb_property, 'max_value', 100 * min)
            step = getattr(cb_property, 'resolution', None)
            if step is None:
                step = 1 if t is int else 0.01
            places = -floor(log(step, 10))

            def update_label(value):
                value_label.setText(f"{value:.{places}f}")

            def remove_label_callback(widget, update_label=update_label):
                try:
                    remove_callback(instance, property, update_label)
                except ValueError:
                    pass

            def on_widget_destroyed(widget, cb=remove_label_callback):
                cb(widget)

            update_label(value)
            add_callback(instance, property, update_label)
            widget.destroyed.connect(on_widget_destroyed)

            steps = round((max - min) / step)
            widget.setMinimum(0)
            widget.setMaximum(steps)
            self._layer_connections.append(connect_value(instance, property, widget, value_range=(min, max)))
            widgets.append((widget, value_label))

        return widgets

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
        self._layer_connections = []

    def _on_layer_change(self, layer_name: str):
        super()._on_layer_change(layer_name)
        multiple_methods = len(self.state.method_helper.choices) > 1
        self.ui.label_method.setVisible(multiple_methods)
        self.ui.combosel_method.setVisible(multiple_methods)
        self.ui.line_2.setVisible(multiple_methods)

    def _update_layer_ui(self, state: State):
        self._clear_layer_layout()
        for property in state.callback_properties():
            row = QVBoxLayout()
            name = self.display_name(property)
            widget_tuples = self._widgets_for_property(state, property, name)
            for widgets in widget_tuples:
                subrow = QHBoxLayout()     
                for widget in widgets:
                    if isinstance(widget, QWidget):
                        subrow.addWidget(widget)
                    elif isinstance(widget, QLayoutItem):
                        subrow.addItem(widget)
                row.addLayout(subrow)
            self.ui.layer_layout.addLayout(row)

    def _on_filetype_change(self, filetype: str):
        super()._on_filetype_change(filetype)
        gl = filetype.lower() in ("gltf", "glb")
        self.ui.combosel_compression.setVisible(gl)
        self.ui.label_compression_message.setVisible(gl)
        self.ui.bool_modelviewer.setVisible(gl)

    def _on_method_change(self, method_name: str):
        super()._on_method_change(method_name)
        state = self._layer_export_states[self.state.layer][method_name]
        self._update_layer_ui(state)
