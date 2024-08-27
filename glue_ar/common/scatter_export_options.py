from echo import CallbackProperty
from glue.core.state_objects import State


__all__ = ["ARVispyScatterExportOptions"]


class ARVispyScatterExportOptions(State):

    theta_resolution = CallbackProperty(8)
    phi_resolution = CallbackProperty(8)
