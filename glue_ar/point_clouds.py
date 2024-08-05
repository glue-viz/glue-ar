from numpy import isfinite, linspace, transpose
import struct

from glue_vispy_viewers.volume.layer_state import VolumeLayerState
from glue_vispy_viewers.volume.viewer_state import Vispy3DVolumeViewerState

from glue_ar.utils import isomin_for_layer


def create_points_export(
    viewer_state: Vispy3DVolumeViewerState,
    layer_state: VolumeLayerState
):
    resolution = int(viewer_state.resolution)
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
    # isomax = isomax_for_layer(viewer_state, layer_state)

    data[~isfinite(data)] = isomin - 10

    data = transpose(data, (1, 0, 2))

    x = linspace(viewer_state.x_min, viewer_state.x_max, resolution)
    y = linspace(viewer_state.y_min, viewer_state.y_max, resolution)
    z = linspace(viewer_state.z_min, viewer_state.z_max, resolution)

    barr = bytearray()
    for c in (x, y, z):
        for v in c:
            barr.extend(struct.pack('f', v))
