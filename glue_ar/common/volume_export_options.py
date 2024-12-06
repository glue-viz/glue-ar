from glue.core.state_objects import State

from glue_ar.common.ranged_callback import RangedCallbackProperty


__all__ = ["ARIsosurfaceExportOptions", "ARVoxelExportOptions"]


class ARIsosurfaceExportOptions(State):
    isosurface_count = RangedCallbackProperty(default=20, min_value=1, max_value=50)


class ARVoxelExportOptions(State):
    opacity_cutoff = RangedCallbackProperty(default=0.1, min_value=0.01, max_value=1, resolution=0.01)
    opacity_resolution = RangedCallbackProperty(default=0.02, min_value=0.005, max_value=1, resolution=0.005)
