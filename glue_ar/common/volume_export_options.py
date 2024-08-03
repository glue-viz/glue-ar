from echo import CallbackProperty
from glue.core.state_objects import State


__all__ = ["ARIsosurfaceExportOptions", "ARVoxelExportOptions"]


class ARIsosurfaceExportOptions(State):
    isosurface_count = CallbackProperty(5)


class ARVoxelExportOptions(State):
    opacity_cutoff = CallbackProperty(0.05) 
