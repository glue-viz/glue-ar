from numpy import isfinite

from glue_vispy_viewers.volume.layer_state import VolumeLayerState
from glue_vispy_viewers.volume.viewer_state import Vispy3DVolumeViewerState

from glue_ar.utils import hex_to_components, isomin_for_layer, isomax_for_layer, layer_color
from glue_ar.gltf_utils import *

def create_marching_cubes_export(
    viewer_state: Vispy3DVolumeViewerState,
    layer_state: VolumeLayerState,
):

    n_opacities = 100
    color = layer_color(layer_state)
    color_components = hex_to_components(color)
    materials = [create_material_for_color(color_components, i / n_opacities) for i in range(n_opacities + 1)]

    # resolution = int(viewer_state.resolution)
    resolution = 256
    bounds = [
        (viewer_state.z_min, viewer_state.z_max, resolution),
        (viewer_state.y_min, viewer_state.y_max, resolution),
        (viewer_state.x_min, viewer_state.x_max, resolution)
    ]

    # For now, only consider one layer
    # shape = (resolution, resolution, resolution)
    data = layer_state.layer.compute_fixed_resolution_buffer(
            target_data=layer_state.layer,
            bounds=bounds,
            target_cid=layer_state.attribute)

    isomin = isomin_for_layer(viewer_state, layer_state) 
    isomax = isomax_for_layer(viewer_state, layer_state) 

    data[~isfinite(data)] = isomin - 1
