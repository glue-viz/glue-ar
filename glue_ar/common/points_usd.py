from glue_vispy_viewers.common.viewer_state import Vispy3DViewerState
from glue_vispy_viewers.scatter.layer_state import ScatterLayerState

from glue_ar.common.export_options import ar_layer_export
from glue_ar.common.scatter import Scatter3DLayerState, ScatterLayerState3D, scatter_layer_mask
from glue_ar.utils import Bounds, NoneType, Viewer3DState, hex_to_components, layer_color, \
        unique_id, xyz_bounds, xyz_for_layer
from glue_ar.common.usd_builder import USDBuilder
from glue_ar.common.scatter_export_options import ARPointExportOptions

try:
    from glue_jupyter.common.state3d import ViewerState3D
except ImportError:
    ViewerState3D = NoneType


def add_points_layer_usd(builder: USDBuilder,
                         viewer_state: Viewer3DState,
                         layer_state: ScatterLayerState3D,
                         bounds: Bounds,
                         clip_to_bounds: bool = True):

    if layer_state is None:
        return

    bounds = xyz_bounds(viewer_state, with_resolution=False)

    vispy_layer_state = isinstance(layer_state, ScatterLayerState)
    color_mode_attr = "color_mode" if vispy_layer_state else "cmap_mode"
    fixed_color = getattr(layer_state, color_mode_attr, "Fixed") == "Fixed"

    mask = scatter_layer_mask(viewer_state, layer_state, bounds, clip_to_bounds)
    data = xyz_for_layer(viewer_state, layer_state,
                         preserve_aspect=viewer_state.native_aspect,
                         mask=mask,
                         scaled=True)
    data = data[:, [1, 2, 0]]

    identifier = f"layer_{unique_id()}"

    if fixed_color:
        color = layer_color(layer_state)
        components = hex_to_components(color)[:3]
        colors = [components for _ in range(data.shape[0])]
    else:
        cmap = layer_state.cmap
        cmap_attr = "cmap_attribute" if vispy_layer_state else "cmap_att"
        cmap_att = getattr(layer_state, cmap_attr)
        cmap_vals = layer_state.layer[cmap_att][mask]
        crange = layer_state.cmap_vmax - layer_state.cmap_vmin

        def get_color(cval):
            normalized = max(min((cval - layer_state.cmap_vmin) / crange, 1), 0)
            cindex = int(normalized * 255)
            return cmap(cindex)[:3]

        colors = [get_color(cval) for cval in cmap_vals]

    builder.add_points(data, colors, identifier)


@ar_layer_export(ScatterLayerState, "Points", ARPointExportOptions, ("usdz", "usdc", "usda"))
def add_vispy_points_layer_usd(builder: USDBuilder,
                               viewer_state: Vispy3DViewerState,
                               layer_state: ScatterLayerState,
                               options: ARPointExportOptions,
                               bounds: Bounds,
                               clip_to_bounds: bool = True):
    add_points_layer_usd(builder=builder,
                         viewer_state=viewer_state,
                         layer_state=layer_state,
                         bounds=bounds,
                         clip_to_bounds=clip_to_bounds)


@ar_layer_export(Scatter3DLayerState, "Points", ARPointExportOptions, ("usdz", "usdc", "usda"))
def add_ipyvolume_points_layer_usd(builder: USDBuilder,
                                   viewer_state: ViewerState3D,
                                   layer_state: ScatterLayerState,
                                   options: ARPointExportOptions,
                                   bounds: Bounds,
                                   clip_to_bounds: bool = True):
    add_points_layer_usd(builder=builder,
                         viewer_state=viewer_state,
                         layer_state=layer_state,
                         bounds=bounds,
                         clip_to_bounds=clip_to_bounds)
