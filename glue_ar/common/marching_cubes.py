from mcubes import marching_cubes
from numpy import isfinite, linspace

from gltflib import AccessorType, BufferTarget, ComponentType

from glue_vispy_viewers.volume.layer_state import VolumeLayerState
from glue_vispy_viewers.volume.viewer_state import Vispy3DVolumeViewerState

from glue_ar.common.export_options import ar_layer_export
from glue_ar.common.gltf_builder import GLTFBuilder
from glue_ar.common.stl_builder import STLBuilder
from glue_ar.common.usd_builder import USDBuilder
from glue_ar.common.volume_export_options import ARIsosurfaceExportOptions
from glue_ar.gltf_utils import add_points_to_bytearray, add_triangles_to_bytearray, index_export_option, \
                               index_mins, index_maxes
from glue_ar.utils import BoundsWithResolution, clip_sides, export_label_for_layer, frb_for_layer, hex_to_components, \
                          isomin_for_layer, isomax_for_layer, layer_color


@ar_layer_export(VolumeLayerState, "Isosurface", ARIsosurfaceExportOptions, ("gltf", "glb"))
def add_isosurface_layer_gltf(builder: GLTFBuilder,
                              viewer_state: Vispy3DVolumeViewerState,
                              layer_state: VolumeLayerState,
                              options: ARIsosurfaceExportOptions,
                              bounds: BoundsWithResolution):
    data = frb_for_layer(viewer_state, layer_state, bounds)

    if len(data) == 0:
        return

    layer_id = export_label_for_layer(layer_state)

    isomin = isomin_for_layer(viewer_state, layer_state)
    isomax = isomax_for_layer(viewer_state, layer_state)

    data[~isfinite(data)] = isomin - 10

    data -= isomin
    data *= (1 / (isomax - isomin))

    if hasattr(layer_state, 'stretch'):
        data = layer_state.stretch_object(data, out=data, **layer_state.stretch_parameters)

    isosurface_count = int(options.isosurface_count)
    levels = linspace(0, 1, num=isosurface_count + 2)
    color = layer_color(layer_state)
    color_components = hex_to_components(color)
    sides = clip_sides(viewer_state, clip_size=1)
    sides = tuple(sides[i] for i in (2, 1, 0))

    for level in levels[1:-1]:
        barr = bytearray()
        level_bin = f"layer_{layer_state.layer.uuid}_level_{level}.bin"

        points, triangles = marching_cubes(data, level)
        if len(points) == 0:
            continue

        opacity = layer_state.alpha * level
        if layer_state.color_mode == "Fixed":
            surface_color_components = color_components
        else:
            surface_color = layer_state.cmap(level)
            surface_color_components = [int(256 * float(c)) for c in surface_color[:3]]

        builder.add_material(surface_color_components, opacity=opacity)
        material_index = builder.material_count - 1

        points = [tuple((-1 + (index + 0.5) * side) for index, side in zip(pt, sides)) for pt in points]
        points = [[p[1], p[0], p[2]] for p in points]
        add_points_to_bytearray(barr, points)
        point_len = len(barr)

        pt_mins = index_mins(points)
        pt_maxes = index_maxes(points)
        tri_mins = [int(min(idx for tri in triangles for idx in tri))]
        max_tri_index = int(max(idx for tri in triangles for idx in tri))
        tri_maxes = [max_tri_index]

        index_format = index_export_option(max_tri_index)
        add_triangles_to_bytearray(barr, triangles, export_option=index_format)
        triangle_len = len(barr) - point_len

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
            component_type=index_format.component_type,
            count=len(triangles)*3,
            type=AccessorType.SCALAR,
            mins=tri_mins,
            maxes=tri_maxes,
        )
        builder.add_mesh(
            layer_id=layer_id,
            position_accessor=builder.accessor_count-2,
            indices_accessor=builder.accessor_count-1,
            material=material_index,
        )
        builder.add_file_resource(level_bin, data=barr)


@ar_layer_export(VolumeLayerState, "Isosurface", ARIsosurfaceExportOptions, ("usdz", "usdc", "usda"))
def add_isosurface_layer_usd(
    builder: USDBuilder,
    viewer_state: Vispy3DVolumeViewerState,
    layer_state: VolumeLayerState,
    options: ARIsosurfaceExportOptions,
    bounds: BoundsWithResolution,
):

    data = frb_for_layer(viewer_state, layer_state, bounds)

    if len(data) == 0:
        return

    isomin = isomin_for_layer(viewer_state, layer_state)
    isomax = isomax_for_layer(viewer_state, layer_state)

    data[~isfinite(data)] = isomin - 10

    data -= isomin
    data *= (1 / (isomax - isomin))

    if hasattr(layer_state, 'stretch'):
        data = layer_state.stretch_object(data, out=data, **layer_state.stretch_parameters)

    isosurface_count = int(options.isosurface_count)
    levels = linspace(0, 1, num=isosurface_count + 2)
    color = layer_color(layer_state)
    color_components = tuple(hex_to_components(color))
    sides = clip_sides(viewer_state, clip_size=1)
    sides = tuple(sides[i] for i in (2, 1, 0))

    for level in levels[1:-1]:
        alpha = layer_state.alpha * level
        points, triangles = marching_cubes(data, level)
        if len(points) == 0:
            continue

        if layer_state.color_mode == "Fixed":
            surface_color_components = color_components
        else:
            surface_color = layer_state.cmap(level)
            surface_color_components = [int(256 * float(c)) for c in surface_color[:3]]

        points = [tuple((-1 + (index + 0.5) * side) for index, side in zip(pt, sides)) for pt in points]
        points = [[p[1], p[0], p[2]] for p in points]
        builder.add_mesh(points, triangles, surface_color_components, alpha)


@ar_layer_export(VolumeLayerState, "Isosurface", ARIsosurfaceExportOptions, ("stl",))
def add_isosurface_layer_stl(
    builder: STLBuilder,
    viewer_state: Vispy3DVolumeViewerState,
    layer_state: VolumeLayerState,
    options: ARIsosurfaceExportOptions,
    bounds: BoundsWithResolution,
):

    data = frb_for_layer(viewer_state, layer_state, bounds)

    if len(data) == 0:
        return

    isomin = isomin_for_layer(viewer_state, layer_state)
    isomax = isomax_for_layer(viewer_state, layer_state)

    data[~isfinite(data)] = isomin - 10

    isosurface_count = int(options.isosurface_count)
    levels = linspace(isomin, isomax, num=isosurface_count + 2)
    sides = clip_sides(viewer_state, clip_size=1)
    sides = tuple(sides[i] for i in (2, 1, 0))

    for level in levels[1:-1]:
        # alpha = (3 * i + isosurface_count) / (4 * isosurface_count) * opacity
        points, triangles = marching_cubes(data, level)
        if len(points) == 0:
            continue

        points = [tuple((-1 + (index + 0.5) * side) for index, side in zip(pt, sides)) for pt in points]
        points = [[p[1], p[0], p[2]] for p in points]
        builder.add_mesh(points, triangles)


try:
    from glue_jupyter.ipyvolume.volume import VolumeLayerState as IPVVolumeLayerState
    ar_layer_export.add(IPVVolumeLayerState, "Isosurface", ARIsosurfaceExportOptions,
                        ("gltf", "glb"), False, add_isosurface_layer_gltf)
    ar_layer_export.add(IPVVolumeLayerState, "Isosurface", ARIsosurfaceExportOptions,
                        ("usda", "usdc", "usdz"), False, add_isosurface_layer_usd)
    ar_layer_export.add(IPVVolumeLayerState, "Isosurface", ARIsosurfaceExportOptions,
                        ("stl",), False, add_isosurface_layer_stl)
except ImportError:
    pass
