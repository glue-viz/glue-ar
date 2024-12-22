from pytest import importorskip

importorskip("glue_qt")

from echo import CallbackProperty
from echo.qt import connect_checkable_button, connect_value
from qtpy.QtWidgets import QPushButton, QSpacerItem, QCheckBox, QLabel, QSlider

from glue_ar.common.tests.test_base_dialog import DummyState
from glue_ar.qt.widgets import boolean_callback_widgets, horizontal_spacer, \
                               info_button, info_tooltip, widgets_for_callback_property


def test_info_tooltip(qtbot):
    assert info_tooltip(DummyState.cb_int) == "<qt>Integer callback property</qt>"
    assert info_tooltip(DummyState.cb_float) == "<qt>Float callback property</qt>"
    assert info_tooltip(DummyState.cb_bool) == "<qt>Boolean callback property</qt>"


def test_horizontal_spacer(qtbot):
    spacer = horizontal_spacer(width=60, height=80)
    assert isinstance(spacer, QSpacerItem)


def test_info_button(qtbot):
    state = DummyState()
    for property in state.callback_properties():
        cb_property: CallbackProperty = getattr(DummyState, property)
        button = info_button(cb_property)
        assert isinstance(button, QPushButton)


def test_boolean_callback_widgets(qtbot):
    state = DummyState()

    widget_tuples, connection = boolean_callback_widgets(state, "cb_bool", "Bool CB")
    assert isinstance(connection, connect_checkable_button)

    assert len(widget_tuples) == 1
    box, spacer, info_button = widget_tuples[0]
    assert isinstance(box, QCheckBox)
    assert box.text() == "Bool CB"
    assert not box.isChecked()
    assert isinstance(spacer, QSpacerItem)
    assert isinstance(info_button, QPushButton)


def test_integer_callback_widgets(qtbot):
    state = DummyState()
    widget_rows, connection = widgets_for_callback_property(state, "cb_int", "Int CB")

    assert isinstance(connection, connect_value)

    assert len(widget_rows) == 2
    label, spacer, info_button = widget_rows[0]
    assert isinstance(label, QLabel)
    assert label.text() == "Int CB:"
    assert isinstance(spacer, QSpacerItem)
    assert isinstance(info_button, QPushButton)

    slider, value_label = widget_rows[1]
    assert isinstance(slider, QSlider)
    assert slider.value() == 1  # 2 is the second (index 1) step value
    assert isinstance(value_label, QLabel)
    assert value_label.text() == "2"


def test_float_callback_widgets():
    state = DummyState()
    widget_rows, connection = widgets_for_callback_property(state, "cb_float", "Float CB")

    assert isinstance(connection, connect_value)
    assert len(widget_rows) == 2

    label, spacer, info_button = widget_rows[0]
    assert isinstance(label, QLabel)
    assert label.text() == "Float CB:"
    assert isinstance(spacer, QSpacerItem)
    assert isinstance(info_button, QPushButton)

    slider, value_label = widget_rows[1]
    assert isinstance(slider, QSlider)
    assert slider.value() == 69  # Another value -> index thing (see above comment)
    assert isinstance(value_label, QLabel)
    assert value_label.text() == "0.70"


def test_widgets_for_callback_property(qtbot):
    state = DummyState()

    int_widget_rows, connection = widgets_for_callback_property(state, "cb_int", "Int CB")
    assert isinstance(connection, connect_value)
    assert len(int_widget_rows) == 2

    label, spacer, info_button = int_widget_rows[0]
    assert isinstance(label, QLabel)
    assert label.text() == "Int CB:"
    assert isinstance(spacer, QSpacerItem)
    assert isinstance(info_button, QPushButton)

    slider, value_label = int_widget_rows[1]
    assert isinstance(slider, QSlider)
    assert slider.value() == 1  # 2 is the second (index 1) step value
    assert isinstance(value_label, QLabel)
    assert value_label.text() == "2"

    float_widget_rows, connection = widgets_for_callback_property(state, "cb_float", "Float CB")
    assert isinstance(connection, connect_value)
    assert len(float_widget_rows) == 2

    label, spacer, info_button = float_widget_rows[0]
    assert isinstance(label, QLabel)
    assert label.text() == "Float CB:"
    assert isinstance(spacer, QSpacerItem)
    assert isinstance(info_button, QPushButton)

    slider, value_label = float_widget_rows[1]
    assert isinstance(slider, QSlider)
    assert slider.value() == 69  # Another value -> index thing (see above comment)
    assert isinstance(value_label, QLabel)
    assert value_label.text() == "0.70"

    bool_widget_rows, connection = widgets_for_callback_property(state, "cb_bool", "Bool CB")
    assert isinstance(connection, connect_checkable_button)
    assert len(bool_widget_rows) == 1

    box, spacer, info_button = bool_widget_rows[0]
    assert isinstance(box, QCheckBox)
    assert box.text() == "Bool CB"
    assert not box.isChecked()
    assert isinstance(spacer, QSpacerItem)
    assert isinstance(info_button, QPushButton)
