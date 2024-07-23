from itertools import product
from math import cos, sqrt
from glue_ar.gltf_utils import index_maxes
from ..shapes import cone_points, cylinder_points, orthogonal_basis, rectangular_prism_points, rectangular_prism_triangulation, sphere_points

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
        center = (1, 2, 3)
        radius = 2
        theta_resolution = 5
        phi_resolution = 8

        precision = 5

        points = sphere_points(
                    center,
                    radius,
                    theta_resolution=theta_resolution,
                    phi_resolution=phi_resolution)
        points = {tuple(round(t, precision) for t in pt) for pt in points}

        expected = {(1, 2, 5), (1, 2, 1)}

        half_sqrt2 = sqrt(2) / 2
        xy = ((1, 0), (half_sqrt2, half_sqrt2), (0, 1), (-half_sqrt2, half_sqrt2),
              (-1, 0), (-half_sqrt2, -half_sqrt2), (0, -1), (half_sqrt2, -half_sqrt2))
        z = (radius * half_sqrt2, 0, -radius * half_sqrt2)
        zr = (radius * half_sqrt2, radius, radius * half_sqrt2)

        for vz, r in zip(z, zr):
            for (vx, vy) in xy:
                point = (r * vx + 1, r * vy + 2, vz + 3)
                expected.add(tuple(round(t, precision) for t in point))

        assert points == expected

    def test_cylinder_points(self):
        center = (-1, 2, -5)
        radius = 3
        central_axis = (0, 0, 2)
        length = 2
        theta_resolution = 8

        precision = 5
        points = cylinder_points(center, radius, length, central_axis, theta_resolution)
        points = {tuple(round(t, precision) for t in pt) for pt in points}


        half_sqrt2 = sqrt(2) / 2
        xy = ((1, 0), (half_sqrt2, half_sqrt2), (0, 1), (-half_sqrt2, half_sqrt2),
              (-1, 0), (-half_sqrt2, -half_sqrt2), (0, -1), (half_sqrt2, -half_sqrt2))

        expected = {(3 * vx - 1, 3 * vy + 2, vz) for (vx, vy), vz in product(xy, (-4, -6))}
        expected = {tuple(round(t, precision) for t in pt) for pt in expected}

        assert points == expected

    def test_points(self):
        center = (2, 0, -1)
        radius = 6
        height = 10
        central_axis = (0, 1, 0)
        theta_resolution = 4

        precision = 5

        points = set(cone_points(center, radius, height, central_axis, theta_resolution))
        points = {tuple(round(t, precision) for t in pt) for pt in points}

        expected = {(-4, 0, -7), (8, 0, 5), (-4, 0, 5), (8, 0, -7), (2, 10, -1)}
        expected = {tuple(round(t, precision) for t in pt) for pt in expected}

        assert points == expected

