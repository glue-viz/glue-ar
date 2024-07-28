from echo import CallbackProperty
from glue.core.state_objects import State
from glue_ar.common.export_state import ar_layer_export
from glue_vispy_viewers.volume.layer_state import VolumeLayerState


__all__ = ["ARIsosurfaceExportOptions", "ARVoxelExportOptions"]


@ar_layer_export(VolumeLayerState, "Isosurface")
class ARIsosurfaceExportOptions(State):
    isosurface_count = CallbackProperty(5)


@ar_layer_export(VolumeLayerState, "Voxel")
class ARVoxelExportOptions(State):
    opacity_cutoff = CallbackProperty(0.05) 
