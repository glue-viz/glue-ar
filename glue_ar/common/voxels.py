from glue_vispy_viewers.volume.viewer_state import Vispy3DVolumeViewerState
from numpy import isfinite, argwhere, transpose
from typing import Iterable

from glue_vispy_viewers.volume.layer_state import VolumeLayerState

from glue_ar.common.gltf_builder import GLTFBuilder
from glue_ar.utils import add_points_to_bytearray, add_triangles_to_bytearray, alpha_composite, \
                          frb_for_layer, hex_to_components, index_maxes, index_mins, isomin_for_layer, isomax_for_layer, layer_color

from glue_ar.gltf_utils import clip_linear_transformations
from glue_ar.shapes import rectangular_prism_points, rectangular_prism_triangulation

from gltflib import AccessorType, BufferTarget, ComponentType
from gltflib.gltf import GLTF


def create_voxel_gltf(
    viewer_state: Vispy3DVolumeViewerState,
    layer_states: Iterable[VolumeLayerState]) -> GLTF:

    builder = GLTFBuilder()

    resolution = int(viewer_state.resolution)
    bounds = [
        (viewer_state.z_min, viewer_state.z_max, resolution),
        (viewer_state.y_min, viewer_state.y_max, resolution),
        (viewer_state.x_min, viewer_state.x_max, resolution)
    ]

    x_range = viewer_state.x_max - viewer_state.x_min
    y_range = viewer_state.y_max - viewer_state.y_min
    z_range = viewer_state.z_max - viewer_state.z_min
    x_spacing = x_range / resolution
    y_spacing = y_range / resolution
    z_spacing = z_range / resolution
    sides = (z_spacing, x_spacing, y_spacing)

    world_bounds = (
        (viewer_state.z_min, viewer_state.z_max),
        (viewer_state.x_min, viewer_state.x_max),
        (viewer_state.y_min, viewer_state.y_max),
    )
    clip_transforms = clip_linear_transformations(world_bounds, clip_size=1)
    clip_sides = [s * transform[0] for s, transform in zip(sides, clip_transforms)]

    point_index = 0
    points_barr = bytearray()
    triangles_barr = bytearray()
    points_bin = "points.bin"
    triangles_bin = "triangles.bin"

    triangles = rectangular_prism_triangulation()
    triangles_barr = bytearray()
    add_triangles_to_bytearray(triangles_barr, triangles)
    triangle_barrlen = len(triangles_barr)

    builder.add_buffer_view(
        buffer=1,
        byte_length=triangle_barrlen,
        byte_offset=0,
        target=BufferTarget.ELEMENT_ARRAY_BUFFER,
    )
    builder.add_accessor(
        buffer_view=0,
        component_type=ComponentType.UNSIGNED_INT,
        count=len(triangles) * 3,
        type=AccessorType.SCALAR,
        mins=[0],
        maxes=[7],
    )

    opacity_cutoff = 0.1
    opacity_factor = 0.75

    occupied_voxels = {}

    for layer_state in layer_states:
        data = frb_for_layer(viewer_state, layer_state, bounds)

        isomin = isomin_for_layer(viewer_state, layer_state)
        isomax = isomax_for_layer(viewer_state, layer_state)

        data[~isfinite(data)] = isomin - 1

        data = transpose(data, (1, 0, 2))

        isorange = isomax - isomin
        nonempty_indices = argwhere(data - isomin > 0)

        color = layer_color(layer_state)
        color_components = hex_to_components(color)

        for indices in nonempty_indices:
            center = tuple((index + 0.5) * side for index, side in zip(indices, clip_sides))

            value = data[*indices]
            adjusted_opacity = min(max(layer_state.alpha * opacity_factor * (value - isomin) / isorange, 0), 1)
            indices_tpl = tuple(indices)
            if indices_tpl in occupied_voxels:
                current_color = occupied_voxels[indices_tpl]
                adjusted_a_color = color_components[:3] + [adjusted_opacity]
                new_color = alpha_composite(adjusted_a_color, current_color)
                occupied_voxels[indices_tpl] = new_color
            elif adjusted_opacity >= opacity_cutoff:
                occupied_voxels[indices_tpl] = color_components[:3] + [adjusted_opacity]

    materials_map = {}
    for indices, rgba in occupied_voxels.items():
        if rgba[-1] < opacity_cutoff:
            continue

        center = tuple((index + 0.5) * side for index, side in zip(indices, clip_sides))

        pts = rectangular_prism_points(center, clip_sides)
        prev_ptbarr_len = len(points_barr)
        point_index += len(pts)
        add_points_to_bytearray(points_barr, pts)
        ptbarr_len = len(points_barr)

        pt_mins = index_mins(pts)
        pt_maxes = index_maxes(pts)

        # We're going to use two buffers
        # The first one (index 0) for the points
        # and the second one (index 1) for the triangles
        builder.add_buffer_view(
           buffer=0,
           byte_length=ptbarr_len-prev_ptbarr_len,
           byte_offset=prev_ptbarr_len,
           target=BufferTarget.ARRAY_BUFFER,
        )
        builder.add_accessor(
            buffer_view=builder.buffer_view_count-1,
            component_type=ComponentType.FLOAT,
            count=len(pts),
            type=AccessorType.VEC3,
            mins=pt_mins,
            maxes=pt_maxes,
        )
        rgba_tpl = tuple(rgba)
        if rgba_tpl in materials_map:
            material_index = materials_map[rgba_tpl]
        else:
            material_index = builder.material_count
            materials_map[rgba_tpl] = material_index
            builder.add_material(
                rgba[:3],
                rgba[3],
            )
        builder.add_mesh(
            position_accessor=builder.accessor_count - 1,
            indices_accessor=0,
            material=material_index
        )

    builder.add_buffer(byte_length=len(points_barr), uri=points_bin)
    builder.add_buffer(byte_length=len(triangles_barr), uri=triangles_bin)

    builder.add_file_resource(points_bin, data=points_barr)
    builder.add_file_resource(triangles_bin, data=triangles_barr)

    return builder.build()