from echo import CallbackProperty
from glue.core.state_objects import State
from glue_ar.common.export_state import ar_layer_export
from glue_vispy_viewers.scatter.layer_state import ScatterLayerState

__all__ = ["ARScatterExportOptions"]


@ar_layer_export(ScatterLayerState, "Scatter")
class ARScatterExportOptions(State):

    theta_resolution = CallbackProperty(8)
    phi_resolution = CallbackProperty(8)
