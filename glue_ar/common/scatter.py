from types import NoneType
from typing import Union


from glue_vispy_viewers.scatter.layer_state import ScatterLayerState
try:
    from glue_jupyter.ipyvolume.scatter import Scatter3DLayerState
except ImportError:
    Scatter3DLayerState = NoneType

ScatterLayerState3D = Union[ScatterLayerState, Scatter3DLayerState]

VECTOR_OFFSETS = {
    'tail': 0.5,
    'middle': 0,
    'tip': -0.5,
}


def radius_for_scatter_layer(layer_state: ScatterLayerState3D) -> float:
    # This feels like a bit of a magic calculation, and it kind of is.
    # The motivation is as follows:
    # 30 is the largest size that we use in the vispy viewer - if the sizing of
    # a point would take it above 30, it's clipped to 30.
    # Looking at the vispy viewer, one can fit about 16 size-30 spheres
    # across one edge of the cube.
    # Hence we take the size of the vispy cube for scatter purposes to be 480
    return min(layer_state.size_scaling * layer_state.size, 30) / 480
