from gltflib import Buffer, BufferView
from gltflib.gltf import GLTF
from gltflib.gltf_resource import FileResource

from numbers import Number
from struct import iter_unpack
from typing import List, Literal, Optional, Tuple, cast
from glue_ar.gltf_utils import GLTFIndexExportOption

from glue_ar.utils import iterator_count


BufferFormat = Literal["f", "B", "H", "I"]


def get_data(gltf: GLTF, buffer: Buffer, buffer_view: Optional[BufferView] = None) -> bytes:

    if buffer.uri is None:
        return bytes()

    # TODO: Find a better way to deal with this
    resource = cast(FileResource, gltf.get_resource(buffer.uri))
    if not resource.loaded:
        resource.load()

    data = resource.data
    if buffer_view is not None:
        offset = buffer_view.byteOffset or 0
        end = offset + buffer_view.byteLength
        data = resource.data[offset:end]

    return data


def count_points(gltf: GLTF, buffer: Buffer, buffer_view: BufferView, format: BufferFormat) -> int:
    data = get_data(gltf, buffer, buffer_view)
    n_values = iterator_count(iter_unpack(format, data))
    return n_values // 3


def count_vertices(gltf: GLTF, buffer: Buffer, buffer_view: BufferView):
    return count_points(gltf, buffer, buffer_view, 'f')


def count_indices(gltf: GLTF, buffer: Buffer, buffer_view: BufferView, export_option: GLTFIndexExportOption):
    return count_points(gltf, buffer, buffer_view, export_option.format)


def unpack_points(gltf: GLTF,
                  buffer: Buffer,
                  buffer_view: BufferView,
                  format: BufferFormat) -> List[Tuple[Number, Number, Number]]:
    data = get_data(gltf, buffer, buffer_view)

    # TODO: Is there a more efficient way to unpack into length-3 points?
    unpacked = []
    current_point = []
    for value in iter_unpack(format, data):
        if len(current_point) < 3:
            current_point.append(value[0])
        else:
            unpacked.append(tuple(current_point))
            current_point = [value[0]]

    unpacked.append(tuple(current_point))

    return unpacked


def unpack_vertices(gltf: GLTF, buffer: Buffer, buffer_view: BufferView) -> List[Tuple[Number, Number, Number]]:
    return unpack_points(gltf, buffer, buffer_view, 'f')


def unpack_indices(gltf: GLTF, buffer: Buffer, buffer_view: BufferView, export_option: GLTFIndexExportOption = GLTFIndexExportOption.Int) -> List[Tuple[Number, Number, Number]]:
    return unpack_points(gltf, buffer, buffer_view, export_option.format)
