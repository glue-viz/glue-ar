from glue_vispy_viewers.volume.viewer_state import Vispy3DVolumeViewerState
from numpy import isfinite, argwhere, transpose
from typing import Iterable, Optional

from glue_vispy_viewers.volume.layer_state import VolumeLayerState

from glue_ar.common.export_options import ar_layer_export
from glue_ar.common.gltf_builder import GLTFBuilder
from glue_ar.common.stl_builder import STLBuilder
from glue_ar.common.usd_builder import USDBuilder
from glue_ar.common.volume_export_options import ARVoxelExportOptions
from glue_ar.usd_utils import material_for_color
from glue_ar.utils import BoundsWithResolution, alpha_composite, binned_opacity, clamp, clamped_opacity, \
                          clip_sides, frb_for_layer, hex_to_components, isomin_for_layer, \
                          isomax_for_layer, layer_color, unique_id, xyz_bounds

from glue_ar.gltf_utils import add_points_to_bytearray, add_triangles_to_bytearray, \
                               index_mins, index_maxes
from glue_ar.common.shapes import rectangular_prism_points, rectangular_prism_triangulation

from gltflib import AccessorType, BufferTarget, ComponentType


@ar_layer_export(VolumeLayerState, "Voxel", ARVoxelExportOptions, ("gltf", "glb"), multiple=True)
def add_voxel_layers_gltf(builder: GLTFBuilder,
                          viewer_state: Vispy3DVolumeViewerState,
                          layer_states: Iterable[VolumeLayerState],
                          options: Iterable[ARVoxelExportOptions],
                          bounds: Optional[BoundsWithResolution] = None):

    bounds = bounds or xyz_bounds(viewer_state, with_resolution=True)
    sides = clip_sides(viewer_state, clip_size=1)
    sides = tuple(sides[i] for i in (1, 2, 0))

    barr = bytearray()
    voxels_id = unique_id()
    uri = f"data_{voxels_id}.bin"

    triangles = rectangular_prism_triangulation()
    add_triangles_to_bytearray(barr, triangles)
    triangles_barrlen = len(barr)
    origin = (0, 0, 0)
    pts = rectangular_prism_points(origin, sides)
    add_points_to_bytearray(barr, pts)
    point_mins = index_mins(pts)
    point_maxes = index_maxes(pts)

    builder.add_buffer(byte_length=len(barr), uri=uri)
    builder.add_file_resource(uri, data=barr)

    builder.add_buffer_view(
        buffer=builder.buffer_count-1,
        byte_length=triangles_barrlen,
        byte_offset=0,
        target=BufferTarget.ELEMENT_ARRAY_BUFFER,
    )
    builder.add_accessor(
        buffer_view=builder.buffer_view_count-1,
        component_type=ComponentType.UNSIGNED_INT,
        count=len(triangles) * 3,
        type=AccessorType.SCALAR,
        mins=[0],
        maxes=[7],
    )
    indices_accessor = builder.accessor_count - 1

    builder.add_buffer_view(
        buffer=builder.buffer_count-1,
        byte_length=len(barr)-triangles_barrlen,
        byte_offset=triangles_barrlen,
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

    opacity_factor = 1
    occupied_voxels = {}

    for layer_state, option in zip(layer_states, options):
        opacity_cutoff = clamp(option.opacity_cutoff, 0, 1)
        opacity_resolution = clamp(option.opacity_resolution, 0, 1)
        data = frb_for_layer(viewer_state, layer_state, bounds)

        isomin = isomin_for_layer(viewer_state, layer_state)
        isomax = isomax_for_layer(viewer_state, layer_state)

        data[~isfinite(data)] = isomin - 1

        data = transpose(data, (1, 0, 2))

        isorange = isomax - isomin
        nonempty_indices = argwhere(data > isomin)

        color = layer_color(layer_state)
        color_components = hex_to_components(color)

        for indices in nonempty_indices:
            value = data[tuple(indices)]
            adjusted_opacity = clamped_opacity(layer_state.alpha * opacity_factor * (value - isomin) / isorange)
            indices_tpl = tuple(indices)
            if indices_tpl in occupied_voxels:
                current_color = occupied_voxels[indices_tpl]
                adjusted_a_color = color_components[:3] + [adjusted_opacity]
                new_color = alpha_composite(adjusted_a_color, current_color)
                occupied_voxels[indices_tpl] = new_color
            else:
                occupied_voxels[indices_tpl] = color_components[:3] + [adjusted_opacity]

    colors_map = {}
    for indices, rgba in occupied_voxels.items():
        if rgba[-1] < opacity_cutoff:
            continue

        center = tuple((-1 + (index + 0.5) * side) for index, side in zip(indices, sides))
        rgba_tpl = tuple(rgba[:3] + [binned_opacity(rgba[3], opacity_resolution)])
        if rgba_tpl in colors_map:
            mesh_index = colors_map[rgba_tpl]
            builder.add_node(
                mesh=mesh_index,
                translation=center,
            )
        else:
            builder.add_material(
                rgba[:3],
                rgba[3],
            )
            builder.add_mesh(
                position_accessor=builder.accessor_count-1,
                indices_accessor=indices_accessor,
                material=builder.material_count-1,
            )
            colors_map[rgba_tpl] = builder.mesh_count - 1


@ar_layer_export(VolumeLayerState, "Voxel", ARVoxelExportOptions, ("usda", "usdc", "usdz"), multiple=True)
def add_voxel_layers_usd(builder: USDBuilder,
                         viewer_state: Vispy3DVolumeViewerState,
                         layer_states: Iterable[VolumeLayerState],
                         options: Iterable[ARVoxelExportOptions],
                         bounds: Optional[BoundsWithResolution] = None):

    bounds = bounds or xyz_bounds(viewer_state, with_resolution=True)
    sides = clip_sides(viewer_state, clip_size=1)
    sides = tuple(sides[i] for i in (1, 2, 0))

    triangles = rectangular_prism_triangulation()

    opacity_factor = 1
    occupied_voxels = {}

    for layer_state, option in zip(layer_states, options):
        opacity_cutoff = clamp(option.opacity_cutoff, 0, 1)
        opacity_resolution = clamp(option.opacity_resolution, 0, 1)
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
            value = data[tuple(indices)]
            adjusted_opacity = clamped_opacity(layer_state.alpha * opacity_factor * (value - isomin) / isorange)
            indices_tpl = tuple(indices)
            if indices_tpl in occupied_voxels:
                current_color = occupied_voxels[indices_tpl]
                adjusted_a_color = color_components[:3] + [adjusted_opacity]
                new_color = alpha_composite(adjusted_a_color, current_color)
                occupied_voxels[indices_tpl] = new_color
            elif adjusted_opacity >= opacity_cutoff:
                occupied_voxels[indices_tpl] = color_components[:3] + [adjusted_opacity]
    materials_map = {}
    mesh = None
    first_point = None
    for indices, rgba in occupied_voxels.items():
        if rgba[-1] < opacity_cutoff:
            continue

        center = tuple((index + 0.5) * side for index, side in zip(indices, sides))
        rgba_tpl = tuple(rgba[:3] + [binned_opacity(rgba[3], opacity_resolution)])
        if rgba_tpl in materials_map:
            material = materials_map[rgba_tpl]
        else:
            material = material_for_color(builder.stage, rgba[:3], rgba[3])
            materials_map[rgba_tpl] = material

        points = rectangular_prism_points(center, sides)
        if mesh is None:
            mesh = builder.add_mesh(points, triangles, rgba[:3], rgba[3])
            first_point = center
        else:
            translation = tuple(p - fp for p, fp in zip(center, first_point))
            builder.add_translated_reference(mesh, translation, material)

    return builder


@ar_layer_export(VolumeLayerState, "Voxel", ARVoxelExportOptions, ("stl",), multiple=True)
def add_voxel_layers_stl(builder: STLBuilder,
                         viewer_state: Vispy3DVolumeViewerState,
                         layer_states: Iterable[VolumeLayerState],
                         options: Iterable[ARVoxelExportOptions],
                         bounds: Optional[BoundsWithResolution] = None):

    bounds = bounds or xyz_bounds(viewer_state, with_resolution=True)
    sides = clip_sides(viewer_state, clip_size=1)
    sides = tuple(sides[i] for i in (1, 2, 0))

    triangles = rectangular_prism_triangulation()

    opacity_factor = 1
    occupied_voxels = {}

    for layer_state, option in zip(layer_states, options):
        opacity_cutoff = clamp(option.opacity_cutoff, 0, 1)
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
            value = data[tuple(indices)]
            adjusted_opacity = clamped_opacity(layer_state.alpha * opacity_factor * (value - isomin) / isorange)
            indices_tpl = tuple(indices)
            if indices_tpl in occupied_voxels:
                current_color = occupied_voxels[indices_tpl]
                adjusted_a_color = color_components[:3] + [adjusted_opacity]
                new_color = alpha_composite(adjusted_a_color, current_color)
                occupied_voxels[indices_tpl] = new_color
            elif adjusted_opacity >= opacity_cutoff:
                occupied_voxels[indices_tpl] = color_components[:3] + [adjusted_opacity]

    for indices, rgba in occupied_voxels.items():
        if rgba[-1] < opacity_cutoff:
            continue

        center = tuple((index + 0.5) * side for index, side in zip(indices, sides))
        points = rectangular_prism_points(center, sides)
        builder.add_mesh(points, triangles)

    return builder


try:
    from glue_jupyter.ipyvolume.volume import VolumeLayerState as IPVVolumeLayerState
    ar_layer_export.add(IPVVolumeLayerState, "Voxel", ARVoxelExportOptions,
                        ("gltf", "glb"), True, add_voxel_layers_gltf)
    ar_layer_export.add(IPVVolumeLayerState, "Voxel", ARVoxelExportOptions,
                        ("usda", "usdc", "usdz"), True, add_voxel_layers_usd)
    ar_layer_export.add(IPVVolumeLayerState, "Voxel", ARVoxelExportOptions,
                        ("stl",), True, add_voxel_layers_stl)
except ImportError:
    pass
