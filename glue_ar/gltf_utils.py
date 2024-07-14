from typing import List

from gltflib import Material, PBRMetallicRoughness

__all__ = [
    "slope_intercept_between",
    "clip_linear_transformations",
    "bring_into_clip",
    "offset_triangles",
    "create_material_for_color",
]


def slope_intercept_between(a, b):
    slope = (b[1] - a[1]) / (b[0] - a[0])
    intercept = b[1] - slope * b[0]
    return slope, intercept


def clip_linear_transformations(bounds, clip_size=1):
    ranges = [abs(bds[1] - bds[0]) for bds in bounds]
    max_range = max(ranges)
    line_data = []
    for bds, rg in zip(bounds, ranges):
        frac = rg / max_range
        half_frac = frac / 2
        half_target = clip_size * half_frac
        line_data.append(slope_intercept_between((bds[0], -half_target), (bds[1], half_target)))
    return line_data


def bring_into_clip(points, transforms):
    return [tuple(transform[0] * c + transform[1] for transform, c in zip(transforms, pt)) for pt in points]


def offset_triangles(triangle_indices, offset):
    return [[idx + offset for idx in triangle] for triangle in triangle_indices]


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
