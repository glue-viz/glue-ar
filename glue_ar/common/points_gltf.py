from gltflib import AccessorType, BufferTarget, ComponentType, PrimitiveMode
from glue_vispy_viewers.common.viewer_state import Vispy3DViewerState
from glue_vispy_viewers.scatter.layer_state import ScatterLayerState

from glue_ar.common.export_options import ar_layer_export
from glue_ar.common.scatter import ScatterLayerState3D, scatter_layer_mask
from glue_ar.gltf_utils import add_points_to_bytearray, index_mins, index_maxes
from glue_ar.utils import Bounds, Viewer3DState, hex_to_components, layer_color, unique_id, xyz_bounds, xyz_for_layer
from glue_ar.common.gltf_builder import GLTFBuilder
from glue_ar.common.scatter_export_options import ARPointExportOptions


def add_points_layer_gltf(builder: GLTFBuilder,
                          viewer_state: Viewer3DState,
                          layer_state: ScatterLayerState3D,
                          bounds: Bounds,
                          clip_to_bounds: bool = True):

    if layer_state is None:
        return

    bounds = xyz_bounds(viewer_state, with_resolution=False)

    mask = scatter_layer_mask(viewer_state, layer_state, bounds, clip_to_bounds)
    data = xyz_for_layer(viewer_state, layer_state,
                         preserve_aspect=viewer_state.native_aspect,
                         mask=mask,
                         scaled=True)
    data = data[:, [1, 2, 0]]
    data_mins = index_mins(data)
    data_maxes = index_maxes(data)

    color = layer_color(layer_state)
    color_components = hex_to_components(color)
    builder.add_material(color=color_components, opacity=layer_state.alpha)

    uri = f"layer_{unique_id()}.bin"

    barr = bytearray()
    add_points_to_bytearray(barr, data)
    builder.add_buffer(byte_length=len(barr), uri=uri)
    builder.add_buffer_view(
        buffer = builder.buffer_count-1,
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

