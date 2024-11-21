from glue.core.state_objects import State
from glue_ar.common.ranged_callback import RangedCallbackProperty


class TestState(State):
    int_value = RangedCallbackProperty(default=10, min_value=5, max_value=25, resolution=1)
    float_value = RangedCallbackProperty(default=0.7, min_value=0.2, max_value=3.6, resolution=0.02)


def test_ranged_callback():
    state = TestState()

    assert state.int_value == 10
    state.int_value = -4
    assert state.int_value == 5
    state.int_value = 30
    assert state.int_value == 25
    state.int_value = 12.7
    assert state.int_value == 13

    assert state.float_value == 0.7
    state.float_value = 0
    assert state.float_value == 0.2
    state.float_value = 18
    assert state.float_value == 3.6
    state.float_value = 0.35
    assert state.float_value == 0.36
