from itertools import product
from math import sqrt
import pytest
from glue_ar.common.shapes import cone_points, cone_triangles, \
                                  cylinder_points, cylinder_triangles, \
                                  rectangular_prism_points, rectangular_prism_triangulation, \
                                  sphere_points, sphere_triangles


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

    def test_rectangular_prism_triangles(self):
        triangles = set(rectangular_prism_triangulation())

        assert {(0, 2, 1),
                (0, 4, 2),
                (1, 2, 3),
                (4, 0, 1),
                (4, 7, 6),
                (5, 1, 7),
                (5, 4, 1),
                (6, 2, 4),
                (7, 1, 3),
                (7, 2, 6),
                (7, 3, 2),
                (7, 4, 5)} == triangles

        start_index = 5
        triangles = set(rectangular_prism_triangulation(start_index=start_index))

        assert {(5, 7, 6),
                (5, 9, 7),
                (6, 7, 8),
                (9, 5, 6),
                (9, 12, 11),
                (10, 6, 12),
                (10, 9, 6),
                (11, 7, 9),
                (12, 6, 8),
                (12, 7, 11),
                (12, 8, 7),
                (12, 9, 10)} == triangles

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

    @pytest.mark.parametrize("theta_resolution,phi_resolution", product((5, 8, 10, 12, 15, 20), repeat=2))
    def test_sphere_points_count(self, theta_resolution, phi_resolution):
        points = sphere_points(center=(0, 0, 0,), radius=1,
                               theta_resolution=theta_resolution,
                               phi_resolution=phi_resolution)
        assert len(points) == 2 + (theta_resolution - 2) * phi_resolution

    @pytest.mark.parametrize("theta_resolution,phi_resolution", product((5, 8, 10, 12, 15, 20), repeat=2))
    def test_sphere_triangles_count(self, theta_resolution, phi_resolution):
        triangles = sphere_triangles(theta_resolution=theta_resolution,
                                     phi_resolution=phi_resolution)
        assert len(triangles) == 2 * phi_resolution * (theta_resolution - 2)

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

    @pytest.mark.parametrize("theta_resolution", (3, 5, 8, 10, 12, 15, 20))
    def test_cylinder_points_count(self, theta_resolution):
        points = cylinder_points(center=(0, 0, 0,), radius=1,
                                 length=1, central_axis=(0, 0, 1),
                                 theta_resolution=theta_resolution)
        assert len(points) == 2 * theta_resolution

    @pytest.mark.parametrize("theta_resolution,start_index", product((3, 5, 8, 10, 12, 15), (0, 2, 5, 7, 10)))
    def test_cylinder_triangles_count(self, theta_resolution, start_index):
        triangles = cylinder_triangles(theta_resolution=theta_resolution,
                                       start_index=start_index)
        assert len(triangles) == 2 * (theta_resolution - 2) + 2 * theta_resolution

    def test_cone_points(self):
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

    @pytest.mark.parametrize("theta_resolution", (3, 5, 8, 10, 12, 15, 20))
    def test_cone_points_count(self, theta_resolution):
        points = cone_points(base_center=(0, 0, 0,), radius=1,
                             height=1, central_axis=(0, 0, 1),
                             theta_resolution=theta_resolution)
        assert len(points) == theta_resolution + 1

    @pytest.mark.parametrize("theta_resolution,start_index", product((3, 5, 8, 10, 12, 15), (0, 2, 5, 7, 10)))
    def test_cone_triangles_count(self, theta_resolution, start_index):
        triangles = cone_triangles(theta_resolution=theta_resolution,
                                   start_index=start_index)
        assert len(triangles) == 2 * theta_resolution - 2
