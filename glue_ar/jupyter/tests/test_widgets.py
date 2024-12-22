from pytest import importorskip

importorskip("glue_jupyter")

from echo import CallbackProperty
from ipyvuetify import Checkbox, Img, Slider, Tooltip

from glue_ar.common.tests.test_base_dialog import DummyState
from glue_ar.jupyter.widgets import boolean_callback_widgets, info_icon, \
                                    info_tooltip, number_callback_widgets, \
                                    widgets_for_callback_property


def test_info_tooltip():
    assert info_tooltip(DummyState.cb_int) == ["Integer callback property"]
    assert info_tooltip(DummyState.cb_float) == ["Float callback property"]
    assert info_tooltip(DummyState.cb_bool) == ["Boolean callback property"]


def test_info_button():
    state = DummyState()
    for property in state.callback_properties():
        cb_property: CallbackProperty = getattr(DummyState, property)
        icon = info_icon(cb_property)
        assert isinstance(icon, Tooltip)
        assert len(icon.children) == 1
        assert len(icon.v_slots) == 1
        slot = icon.v_slots[0]
        assert slot["name"] == "activator"
        assert slot["variable"] == "tooltip"
        assert len(slot["children"]) == 1
        img = slot["children"][0]
        assert isinstance(img, Img)


def test_boolean_callback_widgets():
    state = DummyState()
    widgets = boolean_callback_widgets(state, "cb_bool", "Bool CB")
    assert len(widgets) == 2
    checkbox, icon = widgets

    assert isinstance(checkbox, Checkbox)
    assert checkbox.label == "Bool CB"

    assert not checkbox.value
    assert isinstance(icon, Tooltip)


def test_integer_callback_widgets():
    state = DummyState()
    widgets = number_callback_widgets(state, "cb_int", "Int CB")
    assert len(widgets) == 2
    slider, icon = widgets

    assert isinstance(slider, Slider)
    assert slider.label == "Int CB"
    assert slider.v_model == 2

    assert isinstance(icon, Tooltip)


def test_float_callback_widgets():
    state = DummyState()
    widgets = number_callback_widgets(state, "cb_float", "Float CB")
    assert len(widgets) == 2
    slider, icon = widgets

    assert isinstance(slider, Slider)
    assert slider.label == "Float CB"
    assert slider.v_model == 0.7

    assert isinstance(icon, Tooltip)


def test_widgets_for_property():
    state = DummyState()

    int_widgets = widgets_for_callback_property(state, "cb_int", "Int CB")
    assert len(int_widgets) == 2
    slider, icon = int_widgets
    assert isinstance(slider, Slider)
    assert slider.label == "Int CB"
    assert slider.v_model == 2
    assert isinstance(icon, Tooltip)

    float_widgets = widgets_for_callback_property(state, "cb_float", "Float CB")
    assert len(float_widgets) == 2
    slider, icon = float_widgets
    assert isinstance(slider, Slider)
    assert slider.label == "Float CB"
    assert slider.v_model == 0.7
    assert isinstance(icon, Tooltip)

    bool_widgets = widgets_for_callback_property(state, "cb_bool", "Bool CB")
    assert len(bool_widgets) == 2
    checkbox, icon = bool_widgets
    assert isinstance(checkbox, Checkbox)
    assert checkbox.label == "Bool CB"
    assert not checkbox.value
    assert isinstance(icon, Tooltip)
