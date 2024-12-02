import operator
import struct
from typing import Callable, Iterable, List, Optional, Type, TypeVar, Union

from gltflib import Material, PBRMetallicRoughness

from glue_ar.common.scatter import Point

__all__ = [
    "create_material_for_color",
    "add_points_to_bytearray",
    "add_triangles_to_bytearray",
    "index_mins",
    "index_maxes",
]


GLTF_COMPRESSION_EXTENSIONS = {
    "draco": "KHR_draco_mesh_compression",
    "meshoptimizer": "EXT_meshopt_compression",
}


def create_material_for_color(
    color: List[int],
    opacity: float
) -> Material:
    rgb = [t / 256 for t in color[:3]]
    return Material(
            pbrMetallicRoughness=PBRMetallicRoughness(
                baseColorFactor=rgb + [opacity],
                roughnessFactor=1,
                metallicFactor=0
            ),
            alphaMode="BLEND"
    )


def add_points_to_bytearray(arr: bytearray, points: Iterable[Iterable[Union[int, float]]]):
    for point in points:
        for coordinate in point:
            arr.extend(struct.pack('f', coordinate))


def add_triangles_to_bytearray(arr: bytearray, triangles: Iterable[Iterable[int]]):
    for triangle in triangles:
        for index in triangle:
            arr.extend(struct.pack('I', index))


T = TypeVar("T", bound=Union[int, float])


def index_extrema(items: List[List[T]],
                  extremum: Callable[[T, T], T],
                  previous: Optional[List[List[T]]] = None,
                  type: Type[T] = float) -> List[List[T]]:
    size = len(items[0])
    extrema = [type(extremum([operator.itemgetter(i)(item) for item in items])) for i in range(size)]
    if previous is not None:
        extrema = [extremum(x, p) for x, p in zip(extrema, previous)]
    return extrema


def index_mins(items, previous=None, type: Type[T] = float) -> List[List[T]]:
    return index_extrema(items, extremum=min, type=type, previous=previous)


def index_maxes(items, previous=None, type: Type[T] = float) -> List[List[T]]:
    return index_extrema(items, extremum=max, type=type, previous=previous)


def matrix(origin: Point, destination: Point, scale_ratio: float) -> list[float]:
    translation = tuple(d - o for d, o in zip(destination, origin))
    return [
        scale_ratio, 0, 0, 0,
        0, scale_ratio, 0, 0,
        0, 0, scale_ratio, 0,
        translation[0], translation[1], translation[2], 1,
    ]
