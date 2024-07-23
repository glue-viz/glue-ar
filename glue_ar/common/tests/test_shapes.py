from itertools import product
from math import cos, sqrt
from glue_ar.gltf_utils import index_maxes
from ..shapes import rectangular_prism_points, rectangular_prism_triangulation, sphere_points

from typing import Dict, Iterable, List, Tuple


# def parity(triangle: Tuple[int ,int, int]) -> int:
#     return (
#         int(triangle[1] > triangle[2]) + \
#         int(triangle[0] > triangle[1]) + \
#         int(triangle[0] > triangle[2])
#     ) % 2   
# 
# 
# # This will only work for a triangulation of a simple surface
# # which is all we need for this package
# def orientable(triangulation: Iterable[Tuple[int, int, int]]) -> bool:
#    
#     sides_found: Dict[Tuple[int, int], List[int]] = {}
#     for t in triangulation:
#         p = parity(t)
#         sgn = (-1) ** p
#         for i, idx_i in enumerate(t):
#             for j in range(i+1, len(t)):
#                 idx_j = t[j]
#                 side = (min(idx_i, idx_j), max(idx_i, idx_j))
#                 if side not in sides_found:
#                     print("Adding", side, sgn)
#                     sides_found[side] = [sgn]
#                 else:
#                     prev = sides_found[side]
#                     print(prev)
#                     print(idx_i, idx_j)
#                     print(sgn)
#                     print("======")
#                     if len(prev) > 1 or sgn == prev[0]:
#                         return False
#                     prev.append(sgn)
#     return True


class TestShapes:

    def test_rectangular_prism_points(self):
        center = (1, 1, 1)
        sides = (2, 1, 3)

        points = set(rectangular_prism_points(center, sides))

        assert {(0.0, 0.5, -0.5),
                (0.0, 0.5, 2.5),
                (0.0, 1.5, -0.5),
                (0.0, 1.5, 2.5),
                (2.0, 0.5, -0.5),
                (2.0, 0.5, 2.5),
                (2.0, 1.5, -0.5),
                (2.0, 1.5, 2.5)} == points

    def test_sphere_points(self):
        center = (0, 0, 0)
        radius = 1
        theta_resolution = 5
        phi_resolution = 8

        points = set(sphere_points(
                    center,
                    radius,
                    theta_resolution=theta_resolution,
                    phi_resolution=phi_resolution)
                 )

        half_sqrt2 = sqrt(2) / 2

        expected =  set()
        expected.add((0, 0, 1))
        expected.add((0, 0, -1))

        xy = ((1, 0), (half_sqrt2, half_sqrt2), (0, 1), (-half_sqrt2, half_sqrt2),
              (-1, 0), (-half_sqrt2, -half_sqrt2), (0, -1), (half_sqrt2, -half_sqrt2))
        z = (half_sqrt2, 0, -half_sqrt2)
        sin_thetas = (half_sqrt2, 1, half_sqrt2)
        zr = tuple(radius * s for s in sin_thetas)

        for vz, r in zip(z, zr):
            for (vx, vy) in xy:
                expected.add((r * vx + center[0], r * vy + center[1], vz + center[2]))

        assert points == expected

