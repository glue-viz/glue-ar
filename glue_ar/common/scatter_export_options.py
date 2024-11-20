from glue.core.state_objects import State

from glue_ar.common.ranged_callback import RangedCallbackProperty


__all__ = ["ARVispyScatterExportOptions"]


class ARVispyScatterExportOptions(State):
    resolution = RangedCallbackProperty(default=10, min_value=3, max_value=50, resolution=1)


class ARIpyvolumeScatterExportOptions(State):
    pass
