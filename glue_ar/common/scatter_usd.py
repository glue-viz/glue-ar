from typing import List, Optional, Tuple

from glue.utils import ensure_numerical
from glue_vispy_viewers.scatter.layer_state import ScatterLayerState
from glue_vispy_viewers.scatter.viewer_state import Vispy3DScatterViewerState
from numpy import array, clip, isfinite, isnan, ndarray, ones, sqrt
from numpy.linalg import norm

from glue_ar.common.export_options import ar_layer_export
from glue_ar.common.scatter import radius_for_scatter_layer, VECTOR_OFFSETS
from glue_ar.common.scatter_export_options import ARVispyScatterExportOptions
from glue_ar.common.usd_builder import USDBuilder
from glue_ar.common.shapes import cone_triangles, cone_points, cylinder_points, cylinder_triangles, \
                                  normalize, sphere_points, sphere_triangles
from glue_ar.utils import export_label_for_layer, iterable_has_nan, hex_to_components, \
                          layer_color, mask_for_bounds, xyz_for_layer, Bounds
from glue_ar.usd_utils import material_for_color


def add_vectors_usd(builder: USDBuilder,
                    viewer_state: Vispy3DScatterViewerState,
                    layer_state: ScatterLayerState,
                    data: ndarray,
                    bounds: Bounds,
                    tip_height: float,
                    shaft_radius: float,
                    tip_radius: float,
                    tip_resolution: int = 10,
                    shaft_resolution: int = 10,
                    colors: Optional[List[Tuple[int, int, int]]] = None,
                    mask: Optional[ndarray] = None):

    atts = [layer_state.vx_attribute, layer_state.vy_attribute, layer_state.vz_attribute]
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


@ar_layer_export(ScatterLayerState, "Scatter", ARVispyScatterExportOptions, ("usdc", "usda"))
def add_scatter_layer_usd(
    builder: USDBuilder,
    viewer_state: Vispy3DScatterViewerState,
    layer_state: ScatterLayerState,
    options: ARVispyScatterExportOptions,
    bounds: Bounds,
    clip_to_bounds: bool = True,
):

    theta_resolution = options.theta_resolution
    phi_resolution = options.phi_resolution
    if clip_to_bounds:
        mask = mask_for_bounds(viewer_state, layer_state, bounds)
    else:
        mask = None

    fixed_size = layer_state.size_mode == "Fixed"
    fixed_color = layer_state.color_mode == "Fixed"

    identifier = export_label_for_layer(layer_state).replace(" ", "_")

    if not fixed_size:
        size_mask = isfinite(layer_state.layer[layer_state.size_attribute])
        mask = size_mask if mask is None else (mask & size_mask)
    if not fixed_color:
        color_mask = isfinite(layer_state.layer[layer_state.cmap_attribute])
        mask = color_mask if mask is None else (mask & color_mask)

    data = xyz_for_layer(viewer_state, layer_state,
                         preserve_aspect=viewer_state.native_aspect,
                         mask=mask,
                         scaled=True)
    data = data[:, [1, 2, 0]]
    factor = max((abs(b[1] - b[0]) for b in bounds))
    color = layer_color(layer_state)
    color_components = tuple(hex_to_components(color))

    # We calculate this even if we aren't using fixed size as we might also use this for vectors
    radius = radius_for_scatter_layer(layer_state)
    # TODO: Remove the fixed_size condition
    if not fixed_size:
        # The specific size calculation is taken from the scatter layer artist
        size_data = ensure_numerical(layer_state.layer[layer_state.size_attribute][mask].ravel())
        size_data = clip(size_data, layer_state.size_vmin, layer_state.size_vmax)
        if layer_state.size_vmax == layer_state.size_vmin:
            sizes = sqrt(ones(size_data.shape) * 10)
        else:
            sizes = sqrt(((size_data - layer_state.size_vmin) /
                         (layer_state.size_vmax - layer_state.size_vmin)))
        sizes *= (layer_state.size_scaling / (2 * factor))
        sizes[isnan(sizes)] = 0.

    triangles = sphere_triangles(theta_resolution=theta_resolution, phi_resolution=phi_resolution)

    if not fixed_color:
        cmap = layer_state.cmap
        cmap_att = layer_state.cmap_attribute
        cmap_vals = layer_state.layer[cmap_att][mask]
        crange = layer_state.cmap_vmax - layer_state.cmap_vmin
        normalized = [max(min((cval - layer_state.cmap_vmin) / crange, 1), 0) for cval in cmap_vals]
        colors = [tuple(int(256 * c) for c in cmap(norm)[:3]) for norm in normalized]

    # If we're in fixed-size mode, we can reuse the same prim and translate it
    if fixed_size:
        first_point = data[0]
        points = sphere_points(center=first_point, radius=radius,
                               theta_resolution=theta_resolution,
                               phi_resolution=phi_resolution)
        sphere_mesh = builder.add_mesh(points,
                                       triangles,
                                       color=color_components,
                                       opacity=layer_state.alpha,
                                       identifier=identifier)

        for i in range(1, len(data)):
            point = data[i]
            translation = tuple(p - fp for p, fp in zip(point, first_point))
            if fixed_color:
                material = None
            else:
                material = material_for_color(builder.stage, colors[i], layer_state.alpha)
            builder.add_translated_reference(sphere_mesh,
                                             translation,
                                             material=material,
                                             identifier=identifier)

    else:
        for i, point in enumerate(data):
            points = sphere_points(center=point, radius=sizes[i],
                                   theta_resolution=theta_resolution,
                                   phi_resolution=phi_resolution)
            color = color_components
            if not fixed_color:
                cval = cmap_vals[i]
                normalized = max(min((cval - layer_state.cmap_vmin) / crange, 1), 0)
                color = tuple(int(256 * c) for c in cmap(normalized)[:3])
            builder.add_mesh(points, triangles, color=color, opacity=layer_state.alpha)

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
