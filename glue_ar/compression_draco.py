import numpy as np

from glue_ar.common.gltf_builder import GLTFBuilder
from glue_ar.registries import compressor

from gltflib import AccessorType, AlphaMode, ComponentType, GLTFModel
from gltflib.gltf_resource import GLTFResource
import DracoPy

DRACO_EXTENSION = "KHR_draco_mesh_compression"


def component_dtype(component_type: ComponentType | int) -> type:
    match component_type:
        case ComponentType.UNSIGNED_BYTE:
            return np.uint8
        case ComponentType.UNSIGNED_SHORT:
            return np.uint16
        case ComponentType.UNSIGNED_INT:
            return np.uint32
        case ComponentType.FLOAT:
            return np.float32
        case ComponentType.SHORT:
            return np.int16
        case ComponentType.BYTE:
            return np.int8
        case _:
            raise ValueError("Invalid component type")


def components_per_element(accessor_type: AccessorType | str) -> int:
    match accessor_type:
        case AccessorType.SCALAR.value:
            return 1
        case AccessorType.VEC2.value:
            return 2
        case AccessorType.VEC3.value:
            return 3
        case AccessorType.VEC4.value | AccessorType.MAT2.value:
            return 4
        case AccessorType.MAT3.value:
            return 9
        case AccessorType.MAT4.value:
            return 16
        case _:
            raise ValueError("Invalid accessor type")


def accessor_to_numpy(model: GLTFModel, accessor_index: int, buffers_data) -> np.ndarray:
    accessor = model.accessors[accessor_index]
    bv = model.bufferViews[accessor.bufferView]
    buf_index = bv.buffer
    bin_data = buffers_data[buf_index]

    base = (bv.byteOffset or 0) + (accessor.byteOffset or 0)

    component_type = accessor.componentType
    dtype = component_dtype(component_type)

    n_components = components_per_element(accessor.type)

    count = accessor.count
    item_bytes = np.dtype(dtype).itemsize * n_components
    byte_length = count * item_bytes

    raw = memoryview(bin_data)[base : base + byte_length]
    arr = np.frombuffer(raw, dtype=dtype)

    if n_components == 1:
        return arr
    else:
        return arr.reshape((count, n_components))


def get_data(resource: GLTFResource) -> bytes:
    if resource.data:
        return resource.data

    if resource.uri:
        with open(resource.uri, 'rb') as f:
            data = f.read()

        return data

    raise ValueError("Resource has no data!")


def create_draco_model(
    builder: GLTFBuilder,
    quantization_bits=10,
    compression_level=10,
) -> GLTFBuilder:

    gltf = builder.build()

    model = gltf.model

    resources_data = {}
    buffers_data = []
    for buffer in model.buffers or []:
        for resource in gltf.resources:
            if resource.uri == buffer.uri:
                data = get_data(resource)
                resources_data[resource.uri] = data
                buffers_data.append(data)

    draco_bin_data = bytearray()

    draco_builder = GLTFBuilder()
    buffer_index = draco_builder.buffer_count

    for material in model.materials or []:
        pbr = material.pbrMetallicRoughness
        draco_builder.add_material(
            color = pbr.baseColorFactor[:3],
            opacity = pbr.baseColorFactor[-1],
            metallic_factor=pbr.metallicFactor or 0,
            roughness_factor = pbr.roughnessFactor or 1,
            alpha_mode=AlphaMode(material.alphaMode),
        )

    meshes_handled: set[int] = set()

    for layer_id, mesh_indices in builder.meshes_by_layer.items():
        for mesh_index in mesh_indices:

            if mesh_index in meshes_handled:
                continue

            mesh = model.meshes[mesh_index]

            if mesh.primitives is None:
                continue

            for primitive in mesh.primitives:

                # No POSITION - we can't Draco-encode this primitive
                if primitive.attributes is None or primitive.attributes.POSITION is None:
                    continue

                position_accessor_idx = primitive.attributes.POSITION
                positions = accessor_to_numpy(model, position_accessor_idx, buffers_data)
                # positions = positions.astype(np.float32, copy=False)

                if primitive.indices is not None:
                    index_arr = accessor_to_numpy(model, primitive.indices, buffers_data)
                    # index_arr = index_arr.astype(np.uint32, copy=False)
                    index_arr = index_arr.ravel()
                else:
                    count = positions.shape[0]
                    index_arr = np.arange(count, dtype=np.uint32)

                faces = index_arr.reshape(-1, 3)

                draco_bytes = DracoPy.encode(positions, faces, quantization_bits=quantization_bits, compression_level=compression_level)

                byte_offset = len(draco_bin_data)
                draco_bin_data.extend(draco_bytes)

                buffer_view_index = draco_builder.buffer_view_count
                draco_builder.add_buffer_view(
                    buffer=buffer_index,
                    byte_offset=byte_offset,
                    byte_length=len(draco_bytes),
                    target=None,  # NB: We want this here for Draco; this isn't a standard ARRAY_BUFFER / ELEMENT_ARRAY_BUFFER
                )

                position_accessor = model.accessors[position_accessor_idx]
                min_vals = (
                    position_accessor.min
                    if position_accessor.min is not None
                    else positions.min(axis=0).tolist()
                )
                max_vals = (
                    position_accessor.max
                    if position_accessor.max is not None
                    else positions.max(axis=0).tolist()
                )
                draco_builder.add_accessor(
                    component_type=position_accessor.componentType,
                    type=AccessorType(position_accessor.type),
                    count=position_accessor.count,
                    mins=min_vals,
                    maxes=max_vals,
                    buffer_view=None,
                )

                extensions_data = {
                    DRACO_EXTENSION: {
                        "bufferView": buffer_view_index,
                        "attributes": {
                            "POSITION": 0,
                        }
                    }
                }

                draco_builder.add_mesh(
                    layer_id=layer_id,
                    position_accessor=draco_builder.accessor_count-1,
                    material=primitive.material,
                    mode=primitive.mode,
                    extensions=extensions_data,
                )

            meshes_handled.add(mesh_index)


    bin_uri = "draco.bin"
    draco_builder.add_buffer(byte_length=len(draco_bin_data), uri=bin_uri)
    draco_builder.add_file_resource(filename=bin_uri, data=draco_bin_data)
    draco_builder.add_extension(DRACO_EXTENSION, used=True, required=True)

    return draco_builder


@compressor("draco")
def compress_draco(builder: GLTFBuilder) -> GLTFBuilder:
    return create_draco_model(builder)
