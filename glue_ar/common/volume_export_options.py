from echo import CallbackProperty
from glue.core.state_objects import State
from glue_ar.common.export_state import ar_layer_export
from glue_vispy_viewers.volume.layer_state import VolumeLayerState

__all__ = ["ARVolumeExportOptions"]


@ar_layer_export(VolumeLayerState)
class ARVolumeExportOptions(State):

    use_gaussian_filter = CallbackProperty(False)
    smoothing_iterations = CallbackProperty(0)
    isosurface_count = CallbackProperty(5)
