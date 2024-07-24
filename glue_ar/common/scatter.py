from gltflib import AccessorType, BufferTarget, ComponentType, PrimitiveMode
from glue_vispy_viewers.scatter.layer_state import ScatterLayerState
from glue_vispy_viewers.scatter.viewer_state import Vispy3DScatterViewerState
from glue_vispy_viewers.volume.viewer_state import Vispy3DViewerState
from numpy import array, clip, isfinite, isnan, ndarray, ones, sqrt
from numpy.linalg import norm
import pyvista as pv

from typing import List, Literal, Optional, Tuple

from glue.utils import ensure_numerical
from glue_ar.common.shapes import cone_triangles, cone_points, cylinder_points, cylinder_triangles, \
                           normalize, sphere_points, sphere_triangles
from glue_ar.gltf_utils import add_points_to_bytearray, add_triangles_to_bytearray, index_mins, index_maxes
from glue_ar.usd_utils import material_for_color
from glue_ar.utils import iterable_has_nan, hex_to_components, layer_color, mask_for_bounds, \
                          unique_id, xyz_bounds, xyz_for_layer, Bounds
from glue_ar.common.gltf_builder import GLTFBuilder
from glue_ar.common.usd_builder import USDBuilder


# For the 3D scatter viewer
def scatter_layer_as_points(viewer_state, layer_state):
    xyz = xyz_for_layer(viewer_state, layer_state)
    return {
        "mesh": xyz,
        "color": layer_color(layer_state),
        "opacity": layer_state.alpha,
        "style": "points_gaussian",
        "point_size": 5 * layer_state.size,
        "render_points_as_spheres": True
    }


def scatter_layer_as_spheres(viewer_state, layer_state):
    data = xyz_for_layer(viewer_state, layer_state)
    return {
        "mesh": [pv.Sphere(center=p) for p in data]
    }


def scatter_layer_as_glyphs(viewer_state, layer_state, glyph):
    data = xyz_for_layer(viewer_state, layer_state, scaled=True)
    points = pv.PointSet(data)
    glyphs = points.glyph(geom=glyph, orient=False, scale=False)
    return {
        "mesh": glyphs,
        "color": layer_color(layer_state),
        "opacity": layer_state.alpha,
    }


_VECTOR_OFFSETS = {
    'tail': 0,
    'middle': -0.5,
    'tip': -1,
}

_VECTOR_OFFSETS_GLTF = {
    'tail': 0.5,
    'middle': 0,
    'tip': -0.5,
}


def vector_meshes_for_layer(viewer_state, layer_state,
                            data, bounds,
                            tip_resolution=10,
                            shaft_resolution=10,
                            mask=None):
    atts = [layer_state.vx_attribute, layer_state.vy_attribute, layer_state.vz_attribute]
    tip_factor = 0.25 if layer_state.vector_arrowhead else 0
    vector_data = [layer_state.layer[att].ravel()[mask] for att in atts]
    if viewer_state.native_aspect:
        factor = max((abs(b[1] - b[0]) for b in bounds))
        vector_data = [[0.5 * t / factor for t in v] for v in vector_data]
    else:
        bound_factors = [abs(b[1] - b[0]) for b in bounds]
        vector_data = [[0.5 * t / b for t in v] for v, b in zip(vector_data, bound_factors)]
    vector_data = array(list(zip(*vector_data)))

    arrows = []
    offset = _VECTOR_OFFSETS[layer_state.vector_origin]
    for pt, v in zip(data, vector_data):
        adjusted_v = v * layer_state.vector_scaling
        length = norm(adjusted_v)
        tip_length = tip_factor * length
        adjusted_pt = [c + offset * vc for c, vc in zip(pt, adjusted_v)]
        arrow = pv.Arrow(
                start=adjusted_pt,
                direction=v,
                shaft_resolution=shaft_resolution,
                tip_resolution=tip_resolution,
                shaft_radius=0.002,
                tip_radius=0.01,
                scale=length,
                tip_length=tip_length)
        arrows.append(arrow)

    return arrows


def meshes_for_error_bars(viewer_state, layer_state, axis, data, bounds, mask=None):
    att = getattr(layer_state, f"{axis}err_attribute")
    err_values = layer_state.layer[att].ravel()[mask]
    index = ['x', 'y', 'z'].index(axis)
    axis_range = abs(bounds[index][1] - bounds[index][0])
    if viewer_state.native_aspect:
        max_range = max((abs(b[1] - b[0]) for b in bounds))
        factor = 1 / max_range
    else:
        factor = 1 / axis_range
    err_values *= factor
    lines = []
    for pt, err in zip(data, err_values):
        start = [c - err if idx == index else c for idx, c in enumerate(pt)]
        end = [c + err if idx == index else c for idx, c in enumerate(pt)]
        lines.append(pv.Line(start, end))

    return lines


# This function creates a multiblock mesh for a given scatter layer
# Everything is scaled into clip space for better usability with e.g. model-viewer
def scatter_layer_as_multiblock(viewer_state, layer_state,
                                theta_resolution=8,
                                phi_resolution=8,
                                clip_to_bounds=True,
                                scaled=True):
    meshes = []
    bounds = xyz_bounds(viewer_state, with_resolution=False)
    if clip_to_bounds:
        mask = mask_for_bounds(viewer_state, layer_state, bounds)
    else:
        mask = None

    theta_resolution = int(theta_resolution)
    phi_resolution = int(phi_resolution)
    fixed_color = layer_state.color_mode == "Fixed"
    data = xyz_for_layer(viewer_state, layer_state,
                         preserve_aspect=viewer_state.native_aspect,
                         mask=mask,
                         scaled=scaled)
    factor = max((abs(b[1] - b[0]) for b in bounds))
    if layer_state.size_mode == "Fixed":
        radius = layer_state.size_scaling * sqrt(layer_state.size) / (10 * factor)
        spheres = [pv.Sphere(center=p, radius=radius,
                             phi_resolution=phi_resolution,
                             theta_resolution=theta_resolution) for p in data]
    else:
        # The specific size calculation is taken from the scatter layer artist
        size_data = ensure_numerical(layer_state.layer[layer_state.size_attribute][mask].ravel())
        size_data = clip(size_data, layer_state.size_vmin, layer_state.size_vmax)
        if layer_state.size_vmax == layer_state.size_vmin:
            sizes = sqrt(ones(size_data.shape) * 10)
        else:
            sizes = sqrt((20 * (size_data - layer_state.size_vmin) /
                         (layer_state.size_vmax - layer_state.size_vmin)))
        sizes *= (layer_state.size_scaling / factor)
        sizes[isnan(sizes)] = 0.
        spheres = [pv.Sphere(center=p, radius=r,
                             phi_resolution=phi_resolution,
                             theta_resolution=theta_resolution) for p, r in zip(data, sizes)]

    if not fixed_color:
        points_per_sphere = 2 + (phi_resolution - 2) * theta_resolution
        cmap_values = ensure_numerical(layer_state.layer[layer_state.cmap_attribute][mask].ravel())
        point_cmap_values = [y for x in cmap_values for y in (x,) * points_per_sphere]

    blocks = pv.MultiBlock(spheres)

    # Create the meshes for vectors, if necessary
    if layer_state.vector_visible:
        shaft_resolution = 10
        tip_resolution = 10
        arrows = vector_meshes_for_layer(viewer_state, layer_state,
                                         data, bounds,
                                         tip_resolution=tip_resolution,
                                         shaft_resolution=shaft_resolution,
                                         mask=mask)
        points_per_arrow = (4 * shaft_resolution) + tip_resolution + 1
        point_cmap_values.extend([y for x in cmap_values for y in (x,) * points_per_arrow])
        blocks.extend(arrows)

    geometry = blocks.extract_geometry()
    info = {
        "mesh": geometry,
        "opacity": layer_state.alpha
    }
    meshes.append(info)
    if fixed_color:
        info["color"] = layer_color(layer_state)
    else:
        geometry.point_data["colors"] = point_cmap_values
        cmap = layer_state.cmap.name  # This assumes that we're using a matplotlib colormap
        clim = [layer_state.cmap_vmin, layer_state.cmap_vmax]
        if clim[0] > clim[1]:
            clim = [clim[1], clim[0]]
            cmap = f"{cmap}_r"
        info["cmap"] = cmap
        info["clim"] = clim
        info["scalars"] = "colors"

    # Add error bars
    # We make these their own mesh because (for some reason) they disrupt the coloring of the
    # points and arrows if they're together in one MultiBlock
    # TODO: Why is this?
    if any((layer_state.xerr_visible, layer_state.yerr_visible, layer_state.zerr_visible)):
        bars = pv.MultiBlock()
        bars_info = {}
        bars_cmap_values = []
        for axis in ['x', 'y', 'z']:
            if getattr(layer_state, f"{axis}err_visible"):
                axis_bars = meshes_for_error_bars(viewer_state, layer_state,
                                                  axis, data, bounds, mask=mask)
                bars.extend(axis_bars)
                if not fixed_color:
                    bars_cmap_values.extend([y for x in cmap_values for y in (x,) * 2])  # Each line has just two points

        bars_geometry = bars.extract_geometry()
        bars_info["mesh"] = bars_geometry
        if fixed_color:
            bars_info["color"] = layer_color(layer_state)
        else:
            bars_geometry.point_data["colors"] = bars_cmap_values
            bars_info["cmap"] = cmap
            bars_info["clim"] = clim
            bars_info["scalars"] = "colors"

        meshes.append(bars_info)

    return meshes


def add_vectors_gltf(builder: GLTFBuilder,
                     viewer_state: Vispy3DViewerState,
                     layer_state: ScatterLayerState,
                     data: ndarray,
                     bounds: Bounds,
                     tip_height: float,
                     shaft_radius: float,
                     tip_radius: float,
                     tip_resolution: int = 10,
                     shaft_resolution: int = 10,
                     materials: Optional[List[int]] = None,
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

    offset = _VECTOR_OFFSETS_GLTF[layer_state.vector_origin]
    if layer_state.vector_origin == "tip":
        offset += tip_height

    barr = bytearray()
    triangles = cylinder_triangles(theta_resolution=shaft_resolution)
    triangle_count = len(triangles)
    max_index = max(idx for tri in triangles for idx in tri)
    add_triangles_to_bytearray(barr, triangles)

    if layer_state.vector_arrowhead:
        tip_triangles = cone_triangles(theta_resolution=tip_resolution, start_index=max_index + 1)
        add_triangles_to_bytearray(barr, tip_triangles)
        max_index = max(idx for tri in tip_triangles for idx in tri)
        triangle_count += len(tip_triangles)

    triangles_len = len(barr)
    buffer = builder.buffer_count

    builder.add_buffer_view(
        buffer=buffer,
        byte_length=triangles_len,
        byte_offset=0,
        target=BufferTarget.ELEMENT_ARRAY_BUFFER,
    )
    builder.add_accessor(
        buffer_view=builder.buffer_view_count-1,
        component_type=ComponentType.UNSIGNED_INT,
        count=triangle_count*3,
        type=AccessorType.SCALAR,
        mins=[0],
        maxes=[max_index],
    )
    triangles_accessor = builder.accessor_count - 1

    point_mins = None
    point_maxes = None
    for i, (pt, v) in enumerate(zip(data, vector_data)):
        if iterable_has_nan(v):
            continue
        material_index = materials[i] if materials else builder.material_count - 1
        prev_len = len(barr)
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
        add_points_to_bytearray(barr, points)
        point_count = len(points)
        point_mins = index_mins(points)
        point_maxes = index_maxes(points)

        if layer_state.vector_arrowhead:
            normalized_v = normalize(adjusted_v)
            tip_center_base = [p + half_length * v for p, v in zip(adjusted_pt, normalized_v)]
            tip_points = cone_points(base_center=tip_center_base,
                                     radius=tip_radius,
                                     height=tip_height,
                                     central_axis=adjusted_v,
                                     theta_resolution=tip_resolution)
            add_points_to_bytearray(barr, tip_points)
            point_count += len(tip_points)
            point_mins = index_mins(tip_points, point_mins)
            point_maxes = index_maxes(tip_points, point_maxes)

        builder.add_buffer_view(
            buffer=buffer,
            byte_length=len(barr)-prev_len,
            byte_offset=prev_len,
            target=BufferTarget.ARRAY_BUFFER,
        )
        builder.add_accessor(
            buffer_view=builder.buffer_view_count-1,
            component_type=ComponentType.FLOAT,
            count=point_count,
            type=AccessorType.VEC3,
            mins=point_mins,
            maxes=point_maxes,
        )

        builder.add_mesh(
            position_accessor=builder.accessor_count-1,
            indices_accessor=triangles_accessor,
            material=material_index,
        )

    uri = f"vectors_{unique_id()}.bin"
    builder.add_buffer(byte_length=len(barr), uri=uri)
    builder.add_file_resource(uri, data=barr)


def add_error_bars_gltf(builder: GLTFBuilder,
                        viewer_state: Vispy3DViewerState,
                        layer_state: ScatterLayerState,
                        axis: Literal["x", "y", "z"],
                        data: ndarray,
                        bounds: Bounds,
                        mask: Optional[ndarray] = None):
    att = getattr(layer_state, f"{axis}err_attribute")
    err_values = layer_state.layer[att].ravel()[mask]
    err_values[~isfinite(err_values)] = 0
    index = ['x', 'y', 'z'].index(axis)

    # NB: This ordering is intentional to account for glTF coordinate system
    gltf_index = ['z', 'y', 'x'].index(axis)

    axis_range = abs(bounds[index][1] - bounds[index][0])
    if viewer_state.native_aspect:
        max_range = max((abs(b[1] - b[0]) for b in bounds))
        factor = 1 / max_range
    else:
        factor = 1 / axis_range
    err_values *= factor

    barr = bytearray()

    errors_bin = f"errors_{unique_id()}.bin"
    points = []
    for pt, err in zip(data, err_values):
        start = [c - err if idx == gltf_index else c for idx, c in enumerate(pt)]
        end = [c + err if idx == gltf_index else c for idx, c in enumerate(pt)]
        line_points = (start, end)
        points.extend(line_points)

        add_points_to_bytearray(barr, line_points)

    pt_mins = index_mins(points)
    pt_maxes = index_maxes(points)

    builder.add_buffer(byte_length=len(barr), uri=errors_bin)
    builder.add_buffer_view(
        buffer=builder.buffer_count-1,
        byte_length=len(barr),
        byte_offset=0,
        target=BufferTarget.ARRAY_BUFFER,
    )
    builder.add_accessor(
        buffer_view=builder.buffer_view_count-1,
        component_type=ComponentType.FLOAT,
        count=len(points),
        type=AccessorType.VEC3,
        mins=pt_mins,
        maxes=pt_maxes,
    )
    builder.add_mesh(
        position_accessor=builder.accessor_count-1,
        material=builder.material_count-1,
        mode=PrimitiveMode.LINES,
    )

    builder.add_file_resource(errors_bin, data=barr)


def add_scatter_layer_gltf(builder: GLTFBuilder,
                           viewer_state: Vispy3DScatterViewerState,
                           layer_state: ScatterLayerState,
                           theta_resolution: int = 8,
                           phi_resolution: int = 8,
                           clip_to_bounds: bool = True,
                           scaled: bool = True):
    bounds = xyz_bounds(viewer_state, with_resolution=False)
    if clip_to_bounds:
        mask = mask_for_bounds(viewer_state, layer_state, bounds)
    else:
        mask = None

    fixed_color = layer_state.color_mode == "Fixed"
    fixed_size = layer_state.size_mode == "Fixed"

    if not fixed_size:
        size_mask = isfinite(layer_state.layer[layer_state.size_attribute])
        mask = size_mask if mask is None else (mask & size_mask)
    if not fixed_color:
        color_mask = isfinite(layer_state.layer[layer_state.cmap_attribute])
        mask = color_mask if mask is None else (mask & color_mask)

    data = xyz_for_layer(viewer_state, layer_state,
                         preserve_aspect=viewer_state.native_aspect,
                         mask=mask,
                         scaled=scaled)
    data = data[:, [1, 2, 0]]
    factor = max((abs(b[1] - b[0]) for b in bounds))

    # We calculate this even if we aren't using fixed size as we might also use this for vectors
    radius = layer_state.size_scaling * sqrt(layer_state.size) / (10 * factor)
    # TODO: Remove the fixed_size condition
    if fixed_size:
        radius = 0.01
    else:
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

    barr = bytearray()
    triangles = sphere_triangles(theta_resolution=theta_resolution, phi_resolution=phi_resolution)
    add_triangles_to_bytearray(barr, triangles)
    triangles_len = len(barr)
    max_index = max(idx for tri in triangles for idx in tri)

    buffer = builder.buffer_count
    builder.add_buffer_view(
        buffer=buffer,
        byte_length=triangles_len,
        byte_offset=0,
        target=BufferTarget.ELEMENT_ARRAY_BUFFER,
    )
    builder.add_accessor(
        buffer_view=builder.buffer_view_count-1,
        component_type=ComponentType.UNSIGNED_INT,
        count=len(triangles)*3,
        type=AccessorType.SCALAR,
        mins=[0],
        maxes=[max_index],
    )
    sphere_triangles_accessor = builder.accessor_count - 1

    first_material_index = builder.material_count
    if fixed_color:
        color = layer_color(layer_state)
        color_components = hex_to_components(color)
        builder.add_material(color=color_components, opacity=layer_state.alpha)

    buffer = builder.buffer_count
    cmap = layer_state.cmap
    cmap_att = layer_state.cmap_attribute
    cmap_vals = layer_state.layer[cmap_att][mask]
    crange = layer_state.cmap_vmax - layer_state.cmap_vmin
    uri = f"layer_{unique_id()}.bin"
    for i, point in enumerate(data):

        prev_len = len(barr)
        r = radius if fixed_size else sizes[i]
        pts = sphere_points(center=point, radius=r,
                            theta_resolution=theta_resolution,
                            phi_resolution=phi_resolution)
        add_points_to_bytearray(barr, pts)
        point_mins = index_mins(pts)
        point_maxes = index_maxes(pts)

        if not fixed_color:
            cval = cmap_vals[i]
            normalized = max(min((cval - layer_state.cmap_vmin) / crange, 1), 0)
            cindex = int(normalized * 255)
            color = cmap(cindex)
            builder.add_material(color, layer_state.alpha)

        builder.add_buffer_view(
            buffer=buffer,
            byte_length=len(barr)-prev_len,
            byte_offset=prev_len,
            target=BufferTarget.ARRAY_BUFFER,
        )
        builder.add_accessor(
            buffer_view=builder.buffer_view_count-1,
            component_type=ComponentType.FLOAT,
            count=len(pts),
            type=AccessorType.VEC3,
            mins=point_mins,
            maxes=point_maxes,
        )

        material_index = builder.material_count - 1
        builder.add_mesh(
            position_accessor=builder.accessor_count-1,
            indices_accessor=sphere_triangles_accessor,
            material=material_index,
        )

    builder.add_buffer(byte_length=len(barr), uri=uri)
    builder.add_file_resource(uri, data=barr)

    for axis in ("x", "y", "z"):
        if getattr(layer_state, f"{axis}err_visible", False):
            add_error_bars_gltf(
                builder=builder,
                viewer_state=viewer_state,
                layer_state=layer_state,
                axis=axis,
                data=data,
                bounds=bounds,
                mask=mask,
            )

    if layer_state.vector_visible:
        tip_height = radius / 2
        shaft_radius = radius / 8
        tip_radius = tip_height / 2
        if fixed_color:
            materials = None
        else:
            last_material_index = builder.material_count - 1
            materials = list(range(first_material_index, last_material_index+1))
        add_vectors_gltf(
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
            materials=materials,
            mask=mask,
        )


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

    offset = _VECTOR_OFFSETS_GLTF[layer_state.vector_origin]
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
    viewer_state: Vispy3DScatterViewerState,
    layer_state: ScatterLayerState,
    theta_resolution: int = 8,
    phi_resolution: int = 8,
    clip_to_bounds: bool = True,
    scaled: bool = True
):

    bounds = xyz_bounds(viewer_state, with_resolution=False)
    if clip_to_bounds:
        mask = mask_for_bounds(viewer_state, layer_state, bounds)
    else:
        mask = None

    fixed_size = layer_state.size_mode == "Fixed"
    fixed_color = layer_state.color_mode == "Fixed"

    if not fixed_size:
        size_mask = isfinite(layer_state.layer[layer_state.size_attribute])
        mask = size_mask if mask is None else (mask & size_mask)
    if not fixed_color:
        color_mask = isfinite(layer_state.layer[layer_state.cmap_attribute])
        mask = color_mask if mask is None else (mask & color_mask)

    data = xyz_for_layer(viewer_state, layer_state,
                         preserve_aspect=viewer_state.native_aspect,
                         mask=mask,
                         scaled=scaled)
    data = data[:, [1, 2, 0]]
    factor = max((abs(b[1] - b[0]) for b in bounds))
    color = layer_color(layer_state)
    color_components = tuple(hex_to_components(color))

    # We calculate this even if we aren't using fixed size as we might also use this for vectors
    radius = layer_state.size_scaling * sqrt(layer_state.size) / (10 * factor)
    # TODO: Remove the fixed_size condition
    if fixed_size:
        radius = 0.01
    else:
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

    # If we're in fixed-size mode, we can reuse the same prim and translate it
    if fixed_size:
        first_point = data[0]
        points = sphere_points(center=first_point, radius=radius,
                               theta_resolution=theta_resolution,
                               phi_resolution=phi_resolution)
        sphere_mesh = builder.add_mesh(points, triangles, color=color_components, opacity=layer_state.alpha)

        for i in range(1, len(data)):
            point = data[i]
            translation = tuple(p - fp for p, fp in zip(point, first_point))
            if fixed_color:
                material = None
            else:
                cval = cmap_vals[i]
                normalized = max(min((cval - layer_state.cmap_vmin) / crange, 1), 0)
                color = tuple(int(256 * c) for c in cmap(normalized)[:3])
                material = material_for_color(builder.stage, color, layer_state.alpha)
            builder.add_translated_reference(sphere_mesh, translation, material=material)

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
        # TODO: Add vectors here
