from typing import List, Tuple

from glue_vispy_viewers.common.viewer_state import Vispy3DViewerState
from glue_vispy_viewers.scatter.layer_state import ScatterLayerState

from glue_ar.common.export_options import ar_layer_export
from glue_ar.common.scatter import IPYVOLUME_POINTS_GETTERS, IPYVOLUME_TRIANGLE_GETTERS, VECTOR_OFFSETS, PointsGetter, \
                                   ScatterLayerState3D, box_points_getter, radius_for_scatter_layer, \
                                   scatter_layer_mask, sizes_for_scatter_layer, sphere_points_getter
from glue_ar.common.scatter_export_options import ARIpyvolumeScatterExportOptions, ARVispyScatterExportOptions
from glue_ar.common.shapes import rectangular_prism_triangulation, sphere_triangles
from glue_ar.common.stl_builder import STLBuilder
from glue_ar.utils import Bounds, NoneType, Viewer3DState, xyz_bounds, xyz_for_layer

try:
    from glue_jupyter.common.state3d import ViewerState3D
    from glue_jupyter.ipyvolume.scatter import Scatter3DLayerState
except ImportError:
    ViewerState3D = NoneType
    Scatter3DLayerState = NoneType


def add_scatter_layer_stl(builder: STLBuilder,
                          viewer_state: Viewer3DState,
                          layer_state: ScatterLayerState3D,
                          points_getter: PointsGetter,
                          triangles: List[Tuple[int, int, int]],
                          bounds: Bounds,
                          clip_to_bounds: bool = True):

    if layer_state is None:
        return

    bounds = xyz_bounds(viewer_state, with_resolution=False)

    fixed_size = layer_state.size_mode == "Fixed"
    radius = radius_for_scatter_layer(layer_state)
    mask = scatter_layer_mask(viewer_state, layer_state, bounds, clip_to_bounds)

    data = xyz_for_layer(viewer_state, layer_state,
                         preserve_aspect=viewer_state.native_aspect,
                         mask=mask,
                         scaled=True)
    data = data[:, [1, 2, 0]]

    sizes = sizes_for_scatter_layer(layer_state, bounds, mask)
    for i, point in enumerate(data):

        size = radius if fixed_size else sizes[i]
        pts = points_getter(point, size)
        builder.add_mesh(pts, triangles)


@ar_layer_export(ScatterLayerState, "Scatter", ARVispyScatterExportOptions, ("stl",))
def add_vispy_scatter_layer_stl(builder: STLBuilder,
                                viewer_state: Vispy3DViewerState,
                                layer_state: ScatterLayerState,
                                options: ARVispyScatterExportOptions,
                                bounds: Bounds,
                                clip_to_bounds: bool = True):
    triangles = sphere_triangles(theta_resolution=options.theta_resolution,
                                 phi_resolution=options.phi_resolution)

    points_getter = sphere_points_getter(theta_resolution=options.theta_resolution,
                                         phi_resolution=options.phi_resolution)

    add_scatter_layer_stl(builder=builder,
                          viewer_state=viewer_state,
                          layer_state=layer_state,
                          points_getter=points_getter,
                          triangles=triangles,
                          bounds=bounds,
                          clip_to_bounds=clip_to_bounds)


@ar_layer_export(Scatter3DLayerState, "Scatter", ARIpyvolumeScatterExportOptions, ("stl",))
def add_ipyvolume_scatter_layer_usd(builder: STLBuilder,
                                    viewer_state: ViewerState3D,
                                    layer_state: Scatter3DLayerState,
                                    options: ARIpyvolumeScatterExportOptions,
                                    bounds: Bounds,
                                    clip_to_bounds: bool = True):
    # TODO: What to do for circle2d?
    geometry = str(layer_state.geo)
    triangle_getter = IPYVOLUME_TRIANGLE_GETTERS.get(geometry, rectangular_prism_triangulation)
    triangles = triangle_getter()
    points_getter = IPYVOLUME_POINTS_GETTERS.get(geometry, box_points_getter)

    add_scatter_layer_stl(builder=builder,
                          viewer_state=viewer_state,
                          layer_state=layer_state,
                          points_getter=points_getter,
                          triangles=triangles,
                          bounds=bounds,
                          clip_to_bounds=clip_to_bounds)
