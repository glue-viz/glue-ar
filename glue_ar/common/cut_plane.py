from typing import Callable, List
from numpy import roll, ndarray

from glue.viewers.volume3d.viewer_state import VolumeViewerState3D
from glue_vispy_viewers.volume.viewer_state import cutting_plane_from_state

from glue_ar.utils import BoundsWithResolution


def create_cut_plane_check(
    viewer_state: VolumeViewerState3D,
    bounds: BoundsWithResolution,
    index_permutation=None,
) -> Callable[[List[int]], bool]:
    cut_plane = cutting_plane_from_state(viewer_state)
    if cut_plane is None:
        def check(_indices: List[int]):
            return True
        return check

    resolution_factors = [viewer_state.resolution / bound[2] for bound in bounds]
    cut_plane_coeffs = [factor * coeff for factor, coeff in zip(resolution_factors, cut_plane[:3])]

    cids = index_permutation or [1, 2, 0]

    def cut_plane_check(indices: List[int]):
        return cut_plane_coeffs[cids[0]] * indices[0] + cut_plane_coeffs[cids[1]] * indices[1] + cut_plane_coeffs[cids[2]] * indices[2] + cut_plane[3] > 0

    return cut_plane_check


def _dot(p1, p2):
    return sum(c1 * c2 for c1, c2 in zip(p1, p2))


def _intersection_point(retained, discarded, cut_plane):
    coeffs = cut_plane[:3]
    coeffs = [coeffs[1], coeffs[2], coeffs[0]]
    diff = [d - r for r, d in zip(retained, discarded)]
    t = -(cut_plane[3] + _dot(coeffs, retained)) / _dot(coeffs, diff)
    return [r * (1 - t) + d * t for r, d in zip(retained, discarded)]


# TODO These types probably need adjustment
def adjust_isosurface_for_cut_plane(
    viewer_state: VolumeViewerState3D,
    bounds: BoundsWithResolution,
    points: List[List[float]] | ndarray,
    triangles: List[List[int]] | ndarray,
) -> [List[List[float]], List[List[int]]]:

    cut_plane_check = create_cut_plane_check(viewer_state, bounds)

    cut_plane = cutting_plane_from_state(viewer_state)
    resolution_factors = [viewer_state.resolution / bound[2] for bound in bounds]
    cut_plane_coeffs = [factor * coeff for factor, coeff in zip(resolution_factors, cut_plane[:3])]

    if not isinstance(points, list):
        points = points.tolist()

    if not isinstance(triangles, list):
        triangles = triangles.tolist()

    # First, determine which points will be retained
    point_mappings = {}
    mapped_index = 0
    for index, point in enumerate(points):
        if not cut_plane_check(point):
            point_mappings[index] = mapped_index
            mapped_index += 1

    # Next, handle the triangles
    # There are four cases:
    # * All points are retained
    #    - In this case, all we need to do is remap the triangle indices
    # * No points are retained
    #    - In this case we can just drop the triangle altogether
    # * The triangle has exactly one point retained
    #    - In this case the unclipped portion of the original triangle will be a new triangle
    #      whose vertices are the unclipped vertex and the points where the edges out from the
    #      unclipped vertex intersect the cutting plane. So we replace the original triangle
    #      with the new triangle formed by these three points and respecting the original orientation
    # * The triangle has exactly one point clipped
    #    - In this case we find the intersection points with the cutting plane as above, but now the
    #      unclipped region is a quadrilateral. So we replace the original triangle with two triangles
    #      that form the quadrilateral and respect the original triangle's orientation

    new_triangles = []
    cut_coeffs = cut_plane_coeffs[:3] + [cut_plane[3]]
    for triangle in triangles:
        retained = [index in point_mappings for index in triangle]
        retained_count = sum(retained)

        match retained_count:
            case 3:
                new_triangles.append([point_mappings[index] for index in triangle])
            case 1:
                index = retained.index(True)
                retained_index = triangle[index]
                retained_point = points[retained_index]
                non_retained_indices = [triangle[idx] for idx in range(3) if idx != index]
                non_retained_points = [points[idx] for idx in non_retained_indices]

                qs = [_intersection_point(retained_point, pt, cut_coeffs) for pt in non_retained_points]
                points.extend(qs)
                n = len(points)
                point_mappings[n-2] = mapped_index
                point_mappings[n-1] = mapped_index + 1
                new_triangle = [mapped_index, mapped_index + 1]
                mapped_index += 2
                new_triangle.insert(index, point_mappings[retained_index])
                new_triangles.append(new_triangle)
            case 2:
                non_retained_index = retained.index(False)

                # Move the non-retained index to the end for simplicity
                shift = 2 - non_retained_index
                shifted_triangle = roll(triangle, shift)
                shifted_pts = [points[idx] for idx in shifted_triangle]
                q02 = _intersection_point(shifted_pts[0], shifted_pts[2], cut_coeffs)
                q12 = _intersection_point(shifted_pts[1], shifted_pts[2], cut_coeffs)

                points.append(q02)
                points.append(q12)
                n = len(points)
                point_mappings[n-2] = mapped_index
                point_mappings[n-1] = mapped_index + 1
                new_triangles.append([point_mappings[shifted_triangle[0]], point_mappings[shifted_triangle[1]], mapped_index])
                new_triangles.append([point_mappings[shifted_triangle[1]], mapped_index + 1, mapped_index])
                mapped_index += 2


    new_points = []
    for index, point in enumerate(points):
        if index in point_mappings:
            new_points.append(point)

    return new_points, new_triangles
