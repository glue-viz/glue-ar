from mcubes import marching_cubes
from numpy import isfinite, linspace, transpose
from typing import Iterable

from gltflib import AccessorType, BufferTarget, ComponentType

from glue_vispy_viewers.volume.layer_state import VolumeLayerState
from glue_vispy_viewers.volume.viewer_state import Vispy3DVolumeViewerState

from glue_ar.common.export import compress_gl
from glue_ar.common.gltf_builder import GLTFBuilder
from glue_ar.common.usd_builder import USDBuilder
from glue_ar.utils import add_points_to_bytearray, add_triangles_to_bytearray, \
                          frb_for_layer, hex_to_components, index_maxes, index_mins, \
                          isomin_for_layer, isomax_for_layer, layer_color
from glue_ar.gltf_utils import *


def create_marching_cubes_gltf(
    viewer_state: Vispy3DVolumeViewerState,
    layer_states: Iterable[VolumeLayerState]):

    resolution = int(viewer_state.resolution)
    bounds = [
        (viewer_state.z_min, viewer_state.z_max, resolution),
        (viewer_state.y_min, viewer_state.y_max, resolution),
        (viewer_state.x_min, viewer_state.x_max, resolution)
    ]

    builder = GLTFBuilder()
    isosurface_count = 75

    for layer_state in layer_states:

        data = frb_for_layer(viewer_state, layer_state, bounds)

        isomin = isomin_for_layer(viewer_state, layer_state)
        isomax = isomax_for_layer(viewer_state, layer_state)

        data[~isfinite(data)] = isomin - 10

        data = transpose(data, (1, 0, 2))

        levels = linspace(isomin, isomax, isosurface_count)
        opacity = 0.25 * layer_state.alpha
        color = layer_color(layer_state)
        color_components = hex_to_components(color)
        builder.add_material(color_components, opacity)

        for level in levels[1:]:
            barr = bytearray()
            level_bin = f"layer_{layer_state.layer.uuid}_level_{level}.bin"

            points, triangles = marching_cubes(data, level)
            add_points_to_bytearray(barr, points)
            point_len = len(barr)

            add_triangles_to_bytearray(barr, triangles)
            triangle_len = len(barr) - point_len

            pt_mins = index_mins(points)
            pt_maxes = index_maxes(points)
            tri_mins = [int(min(idx for tri in triangles for idx in tri))]
            tri_maxes = [int(max(idx for tri in triangles for idx in tri))]

            builder.add_buffer(byte_length=len(barr), uri=level_bin)

            buffer = builder.buffer_count - 1
            builder.add_buffer_view(
                buffer=buffer,
                byte_length=point_len,
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
            builder.add_buffer_view(
                buffer=buffer,
                byte_length=triangle_len,
                byte_offset=point_len,
                target=BufferTarget.ELEMENT_ARRAY_BUFFER,
            )
            builder.add_accessor(
                buffer_view=builder.buffer_view_count-1,
                component_type=ComponentType.UNSIGNED_INT,
                count=len(triangles)*3,
                type=AccessorType.SCALAR,
                mins=tri_mins,
                maxes=tri_maxes,
            )
            builder.add_mesh(
                position_accessor=builder.accessor_count-2,
                indices_accessor=builder.accessor_count-1,
                material=builder.material_count-1,
            )
            builder.add_file_resource(level_bin, data=barr)

    gltf = builder.build()
    gltf_filepath = "marching_cubes.gltf"
    glb_filepath = "marching_cubes.glb"
    gltf.export(gltf_filepath)
    gltf.export(glb_filepath)
    print("About to compress")
    compress_gl(glb_filepath)


def create_marching_cubes_usd(
    viewer_state: Vispy3DVolumeViewerState,
    layer_states: Iterable[VolumeLayerState],
):

    resolution = int(viewer_state.resolution)
    bounds = [
        (viewer_state.z_min, viewer_state.z_max, resolution),
        (viewer_state.y_min, viewer_state.y_max, resolution),
        (viewer_state.x_min, viewer_state.x_max, resolution)
    ]

    builder = USDBuilder()
    output_filename = "marching_cubes.usdc"
    output_filepath = output_filename

    isosurface_count = 75

    for layer_state in layer_states:

        # For now, only consider one layer
        # shape = (resolution, resolution, resolution)
        data = frb_for_layer(viewer_state, layer_state, bounds)

        isomin = isomin_for_layer(viewer_state, layer_state)
        isomax = isomax_for_layer(viewer_state, layer_state)

        data[~isfinite(data)] = isomin - 10

        data = transpose(data, (1, 0, 2))

        levels = linspace(isomin, isomax, isosurface_count)
        opacity = layer_state.alpha
        color = layer_color(layer_state)
        color_components = tuple(hex_to_components(color))

        for i, level in enumerate(levels[1:]):
            alpha = (3 * i + isosurface_count) / (4 * isosurface_count) * opacity
            print(alpha / opacity)
            points, triangles = marching_cubes(data, level)

            builder.add_shape(points, triangles, color_components, alpha)

    builder.export(output_filepath)
