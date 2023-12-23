from echo import CallbackProperty
from glue.core.state_objects import State
from glue_ar.export_dialog import ar_layer_export
from glue_vispy_viewers.volume.layer_state import VolumeLayerState

__all__ = ["ARVolumeExportOptions"]


@ar_layer_export(VolumeLayerState)
class ARVolumeExportOptions(State):

    use_gaussian_filter = CallbackProperty(False)
    smoothing_iterations = CallbackProperty(0)
