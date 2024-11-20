from echo.core import CallbackProperty
from typing import Callable, Optional

from glue_ar.utils import clamp, clamp_with_resolution


class RangedCallbackProperty(CallbackProperty):

    def __init__(self,
                 default: Optional[float] = None,
                 min_value: float = 0,
                 max_value: float = 1,
                 resolution: Optional[float] = None,
                 **kwargs):
        super().__init__(default=default, **kwargs)
        self.min_value = min_value
        self.max_value = max_value
        self.resolution = resolution

    def __set__(self, instance, value):
        if value is not None:
            if self.resolution is not None:
                value = clamp_with_resolution(value, self.min_value, self.max_value, self.resolution)
            else:
                value = clamp(value, self.min_value, self.max_value)

        super().__set__(instance, value)
