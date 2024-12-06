from collections import defaultdict
from gltflib import AccessorType, BufferTarget, ComponentType, PrimitiveMode
from glue_vispy_viewers.common.viewer_state import Vispy3DViewerState
from glue_vispy_viewers.scatter.layer_state import ScatterLayerState

from glue_ar.common.export_options import ar_layer_export
from glue_ar.common.scatter import Scatter3DLayerState, ScatterLayerState3D, scatter_layer_mask
from glue_ar.gltf_utils import add_points_to_bytearray, index_mins, index_maxes
from glue_ar.utils import Bounds, NoneType, Viewer3DState, color_identifier, hex_to_components, \
        layer_color, unique_id, xyz_bounds, xyz_for_layer
from glue_ar.common.gltf_builder import GLTFBuilder
from glue_ar.common.scatter_export_options import ARPointExportOptions

try:
    from glue_jupyter.common.state3d import ViewerState3D
except ImportError:
    ViewerState3D = NoneType


def add_points_layer_gltf(builder: GLTFBuilder,
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

    uri = f"layer_{unique_id()}.bin"

    if fixed_color:
        color = layer_color(layer_state)
        color_components = hex_to_components(color)
        builder.add_material(color=color_components, opacity=layer_state.alpha)

        barr = bytearray()
        add_points_to_bytearray(barr, data)

        data_mins = index_mins(data)
        data_maxes = index_maxes(data)

        builder.add_buffer(byte_length=len(barr), uri=uri)
        builder.add_buffer_view(
            buffer=builder.buffer_count-1,
            byte_length=len(barr),
            byte_offset=0,
            target=BufferTarget.ARRAY_BUFFER
        )
        builder.add_accessor(
            buffer_view=builder.buffer_view_count-1,
            component_type=ComponentType.FLOAT,
            count=len(data),
            type=AccessorType.VEC3,
            mins=data_mins,
            maxes=data_maxes,
        )
        builder.add_mesh(
            position_accessor=builder.accessor_count-1,
            material=builder.material_count-1,
            mode=PrimitiveMode.POINTS
        )
        builder.add_file_resource(uri, data=barr)
    else:
        # If we don't have fixed colors, the idea is to make a different "mesh" for each different color used
        # So first we need to run through the points and determine which color they have, and group ones with
        # the same color together
        points_by_color = defaultdict(list)
        cmap = layer_state.cmap
        cmap_attr = "cmap_attribute" if vispy_layer_state else "cmap_att"
        cmap_att = getattr(layer_state, cmap_attr)
        cmap_vals = layer_state.layer[cmap_att][mask]
        crange = layer_state.cmap_vmax - layer_state.cmap_vmin
        opacity = layer_state.alpha

        for i, point in enumerate(data):
            cval = cmap_vals[i]
            normalized = max(min((cval - layer_state.cmap_vmin) / crange, 1), 0)
            cindex = int(normalized * 255)
            color = cmap(cindex)
            points_by_color[color].append(point)

        for color, points in points_by_color.items():
            builder.add_material(color, opacity)
            material_index = builder.material_count - 1

            uri = f"layer_{unique_id()}_{color_identifier(color, opacity)}"

            barr = bytearray()
            add_points_to_bytearray(barr, points)
            point_mins = index_mins(points)
            point_maxes = index_maxes(points)

            builder.add_buffer(byte_length=len(barr), uri=uri)
            builder.add_buffer_view(
                buffer=builder.buffer_count-1,
                byte_length=len(barr),
                byte_offset=0,
                target=BufferTarget.ARRAY_BUFFER
            )
            builder.add_accessor(
                buffer_view=builder.buffer_view_count-1,
                component_type=ComponentType.FLOAT,
                count=len(points),
                type=AccessorType.VEC3,
                mins=point_mins,
                maxes=point_maxes
            )
            builder.add_mesh(
                position_accessor=builder.accessor_count-1,
                material=material_index,
                mode=PrimitiveMode.POINTS,
            )
            builder.add_file_resource(uri, data=barr)


@ar_layer_export(ScatterLayerState, "Points", ARPointExportOptions, ("gltf", "glb"))
def add_vispy_points_layer_gltf(builder: GLTFBuilder,
                                viewer_state: Vispy3DViewerState,
                                layer_state: ScatterLayerState,
                                options: ARPointExportOptions,
                                bounds: Bounds,
                                clip_to_bounds: bool = True):
    add_points_layer_gltf(builder=builder,
                          viewer_state=viewer_state,
                          layer_state=layer_state,
                          bounds=bounds,
                          clip_to_bounds=clip_to_bounds)


@ar_layer_export(Scatter3DLayerState, "Points", ARPointExportOptions, ("gltf", "glb"))
def add_ipyvolume_points_layer_gltf(builder: GLTFBuilder,
                                    viewer_state: ViewerState3D,
                                    layer_state: ScatterLayerState,
                                    options: ARPointExportOptions,
                                    bounds: Bounds,
                                    clip_to_bounds: bool = True):
    add_points_layer_gltf(builder=builder,
                          viewer_state=viewer_state,
                          layer_state=layer_state,
                          bounds=bounds,
                          clip_to_bounds=clip_to_bounds)
