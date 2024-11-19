from echo import CallbackProperty
from glue.core.state_objects import State


__all__ = ["ARVispyScatterExportOptions"]


class ARVispyScatterExportOptions(State):
    resolution = CallbackProperty(10)


class ARIpyvolumeScatterExportOptions(State):
    pass
