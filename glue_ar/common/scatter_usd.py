from collections import defaultdict
from typing import List, Optional, Tuple

from glue_vispy_viewers.scatter.layer_state import ScatterLayerState
from glue_vispy_viewers.scatter.viewer_state import Vispy3DViewerState
from numpy import array, ndarray
from numpy.linalg import norm

from glue_ar.common.export_options import ar_layer_export
from glue_ar.common.scatter import IPYVOLUME_POINTS_GETTERS, IPYVOLUME_TRIANGLE_GETTERS, VECTOR_OFFSETS, PointsGetter, \
                                   ScatterLayerState3D, box_points_getter, radius_for_scatter_layer, \
                                   scatter_layer_mask, sizes_for_scatter_layer, sphere_points_getter
from glue_ar.common.scatter_export_options import ARIpyvolumeScatterExportOptions, ARVispyScatterExportOptions
from glue_ar.common.usd_builder import USDBuilder
from glue_ar.common.shapes import cone_triangles, cone_points, cylinder_points, cylinder_triangles, \
                                  normalize, rectangular_prism_triangulation, sphere_triangles
from glue_ar.utils import Viewer3DState, export_label_for_layer, iterable_has_nan, hex_to_components, \
                          layer_color, offset_triangles, xyz_for_layer, Bounds, NoneType
from glue_ar.usd_utils import material_for_color

try:
    from glue_jupyter.common.state3d import ViewerState3D
    from glue_jupyter.ipyvolume.scatter import Scatter3DLayerState
except ImportError:
    ViewerState3D = NoneType
    Scatter3DLayerState = NoneType


def add_vectors_usd(builder: USDBuilder,
                    viewer_state: Viewer3DState,
                    layer_state: ScatterLayerState3D,
                    data: ndarray,
                    bounds: Bounds,
                    tip_height: float,
                    shaft_radius: float,
                    tip_radius: float,
                    tip_resolution: int = 10,
                    shaft_resolution: int = 10,
                    colors: Optional[List[Tuple[int, int, int]]] = None,
                    mask: Optional[ndarray] = None):

    if isinstance(layer_state, ScatterLayerState):
        atts = [layer_state.vx_attribute, layer_state.vy_attribute, layer_state.vz_attribute]
    else:
        atts = [layer_state.vx_att, layer_state.vy_att, layer_state.vz_att]
    vector_data = [layer_state.layer[att].ravel()[mask] for att in atts]

    if viewer_state.native_aspect:
        factor = max((abs(b[1] - b[0]) for b in bounds))
        vector_data = [[0.5 * t / factor for t in v] for v in vector_data]
    else:
        bound_factors = [abs(b[1] - b[0]) for b in bounds]
        vector_data = [[0.5 * t / b for t in v] for v, b in zip(vector_data, bound_factors)]
    vector_data = array(list(zip(*vector_data)))

    offset = VECTOR_OFFSETS[layer_state.vector_origin]
    if layer_state.vector_origin == "tip":
        offset += tip_height

    triangles = cylinder_triangles(theta_resolution=shaft_resolution)
    if layer_state.vector_arrowhead:
        tip_triangles = cone_triangles(theta_resolution=tip_resolution)

    for i, (pt, v) in enumerate(zip(data, vector_data)):
        if iterable_has_nan(v):
            continue
        adjusted_v = v * layer_state.vector_scaling
        length = norm(adjusted_v)
        half_length = 0.5 * length

        adjusted_v = [adjusted_v[i] for i in (1, 2, 0)]
        adjusted_pt = [c + offset * vc for c, vc in zip(pt, adjusted_v)]
        points = cylinder_points(center=adjusted_pt,
                                 radius=shaft_radius,
                                 length=length,
                                 central_axis=adjusted_v,
                                 theta_resolution=shaft_resolution)

        fixed_color = tuple(hex_to_components(layer_color(layer_state)))
        color = colors[i] if colors is not None else fixed_color
        builder.add_mesh(points, triangles, color=color, opacity=layer_state.alpha)

        if layer_state.vector_arrowhead:
            normalized_v = normalize(adjusted_v)
            tip_center_base = [p + half_length * v for p, v in zip(adjusted_pt, normalized_v)]

            tip_points = cone_points(base_center=tip_center_base,
                                     radius=tip_radius,
                                     height=tip_height,
                                     central_axis=adjusted_v,
                                     theta_resolution=tip_resolution)

            builder.add_mesh(tip_points, tip_triangles, color=color, opacity=layer_state.alpha)


def add_scatter_layer_usd(
    builder: USDBuilder,
    viewer_state: Viewer3DState,
    layer_state: ScatterLayerState3D,
    points_getter: PointsGetter,
    triangles: List[Tuple[int, int, int]],
    bounds: Bounds,
    clip_to_bounds: bool = True,
):

    vispy_layer_state = isinstance(layer_state, ScatterLayerState)
    fixed_size = layer_state.size_mode == "Fixed"
    color_mode_attr = "color_mode" if vispy_layer_state else "cmap_mode"
    fixed_color = getattr(layer_state, color_mode_attr, "Fixed") == "Fixed"

    identifier = export_label_for_layer(layer_state).replace(" ", "_")

    mask = scatter_layer_mask(viewer_state, layer_state, bounds, clip_to_bounds)
    data = xyz_for_layer(viewer_state, layer_state,
                         preserve_aspect=viewer_state.native_aspect,
                         mask=mask,
                         scaled=True)
    data = data[:, [1, 2, 0]]
    color = layer_color(layer_state)
    color_components = tuple(hex_to_components(color))

    # We calculate this even if we aren't using fixed size as we might also use this for vectors
    radius = radius_for_scatter_layer(layer_state)
    sizes = sizes_for_scatter_layer(layer_state, bounds, mask)

    if not fixed_color:
        cmap = layer_state.cmap
        cmap_attr = "cmap_attribute" if vispy_layer_state else "cmap_att"
        cmap_att = getattr(layer_state, cmap_attr)
        cmap_vals = layer_state.layer[cmap_att][mask]
        crange = layer_state.cmap_vmax - layer_state.cmap_vmin
        normalized = [max(min((cval - layer_state.cmap_vmin) / crange, 1), 0) for cval in cmap_vals]
        colors = [tuple(int(256 * c) for c in cmap(norm)[:3]) for norm in normalized]

    # If we're in fixed-color mode, we can use one mesh for everything
    opacity = float(layer_state.alpha)
    triangle_offset = 0
    if fixed_color:
        points = []
        tris = []
        for point in data:
            size = radius if fixed_size else sizes[i]
            pts = points_getter(point, size)
            points.append(pts)
            pt_triangles = offset_triangles(triangles, triangle_offset)
            triangle_offset += len(pts)
            triangles.append(pt_triangles)

        mesh_points = [pt for pts in points for pt in pts]
        mesh_triangles = [tri for sphere in tris for tri in sphere] 
        builder.add_mesh(mesh_points,
                         mesh_triangles,
                         color=color_components,
                         opacity=opacity,
                         identifier=identifier)
    else:
        points_by_color = defaultdict(list)
        triangles_by_color = defaultdict(list)
        for point, color in zip(data, colors):
            size = radius if fixed_size else sizes[i]
            pts = points_getter(point, size)
            pt_triangles = offset_triangles(triangles, triangle_offset)
            triangle_offset += len(pts)
            points_by_color[color].append(pts)
            triangles_by_color[color].append(pt_triangles)

        for color, points in points_by_color.items():
            tris = triangles_by_color[color]
            mesh_points = [pt for pts in points for pt in pts]
            mesh_triangles = [tri for sphere in tris for tri in sphere] 
            builder.add_mesh(mesh_points,
                             mesh_triangles,
                             color=color,
                             opacity=opacity,
                             identifier=identifier)

    for axis in ("x", "y", "z"):
        if getattr(layer_state, f"{axis}err_visible", False):
            # TODO: Add error bars here
            pass

    if layer_state.vector_visible:
        tip_height = radius / 2
        shaft_radius = radius / 8
        tip_radius = tip_height / 2
        add_vectors_usd(
            builder=builder,
            viewer_state=viewer_state,
            layer_state=layer_state,
            data=data,
            bounds=bounds,
            tip_height=tip_height,
            shaft_radius=shaft_radius,
            tip_radius=tip_radius,
            shaft_resolution=10,
            tip_resolution=10,
            colors=colors if not fixed_color else None,
            mask=mask,
        )


@ar_layer_export(ScatterLayerState, "Scatter", ARVispyScatterExportOptions, ("usdz", "usdc", "usda"))
def add_vispy_scatter_layer_usd(builder: USDBuilder,
                                viewer_state: Vispy3DViewerState,
                                layer_state: ScatterLayerState,
                                options: ARVispyScatterExportOptions,
                                bounds: Bounds,
                                clip_to_bounds: bool = True):

    theta_resolution = int(options.theta_resolution)
    phi_resolution = int(options.phi_resolution)
    triangles = sphere_triangles(theta_resolution=theta_resolution,
                                 phi_resolution=phi_resolution)

    points_getter = sphere_points_getter(theta_resolution=theta_resolution,
                                         phi_resolution=phi_resolution)

    add_scatter_layer_usd(builder=builder,
                          viewer_state=viewer_state,
                          layer_state=layer_state,
                          points_getter=points_getter,
                          triangles=triangles,
                          bounds=bounds,
                          clip_to_bounds=clip_to_bounds)


@ar_layer_export(Scatter3DLayerState, "Scatter", ARIpyvolumeScatterExportOptions, ("usdz", "usdc", "usda"))
def add_ipyvolume_scatter_layer_usd(builder: USDBuilder,
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

    add_scatter_layer_usd(builder=builder,
                          viewer_state=viewer_state,
                          layer_state=layer_state,
                          points_getter=points_getter,
                          triangles=triangles,
                          bounds=bounds,
                          clip_to_bounds=clip_to_bounds)
