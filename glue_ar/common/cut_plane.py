from typing import Callable, List

from glue.viewers.volume3d.viewer_state import VolumeViewerState3D
from glue_vispy_viewers.volume.viewer_state import cutting_plane_from_state

from glue_ar.utils import BoundsWithResolution, set_bit_on


def create_cut_plane_check(
    viewer_state: VolumeViewerState3D,
    bounds: BoundsWithResolution
) -> Callable[[List[int]], bool]:
    cut_plane = cutting_plane_from_state(viewer_state)
    if cut_plane is None:
        def check(_indices: List[int]):
            return True
        return check

    resolution_factors = [viewer_state.resolution / bound[2] for bound in bounds]
    cut_plane_coeffs = [factor * coeff for factor, coeff in zip(resolution_factors, cut_plane[:3])]

    def cut_plane_check(indices: List[int]):
        return cut_plane_coeffs[1] * indices[0] + cut_plane_coeffs[2] * indices[1] + cut_plane_coeffs[0] * indices[2] + cut_plane[3] > 0

    return cut_plane_check


def _dot(p1, p2):
    return sum(c1 * c2 for c1, c2 in zip(p1, p2))


def _intersection_point(retained, discarded, cut_plane):
    coeffs = cut_plane[:3]
    diff = [r - d for r, d in zip(retained, discarded)]
    t = -(cut_plane[3] + _dot(coeffs, retained)) / _dot(coeffs, diff)
    return [r * (1 - t) + d * t for r, d in zip(retained, discarded)]


# TODO These types probably need adjustment
def adjust_isosurface_for_cut_plane(
    viewer_state: VolumeViewerState3D,
    bounds: BoundsWithResolution,
    points: List[List[float]],
    triangles: List[List[int]]
) -> [List[List[float]], List[List[int]]]:

    cut_plane_check = create_cut_plane_check(viewer_state, bounds)

    cut_plane = cutting_plane_from_state(viewer_state)
    resolution_factors = [viewer_state.resolution / bound[2] for bound in bounds]
    cut_plane_coeffs = [factor * coeff for factor, coeff in zip(resolution_factors, cut_plane[:3])]

    # First, determine which points will be retained
    point_mappings = {}
    mapped_index = 0
    for index, point in enumerate(points):
        if cut_plane_check(point): 
            point_mappings[index] = mapped_index
            mapped_index += 1

    # Next, handle the triangles
    # There are three cases:
    # * All points are retained
    #    - In this case, all we need to do is remap the triangle indices
    # * No points are retained
    #    - In this case we can just drop the triangle altogether
    # * The triangle has at least one point retained, and at least one not retained

    new_triangles = []
    cut_coeffs = cut_plane_coeffs[:3] + [cut_plane[3]]
    for triangle in triangles:
        retained = [index in point_mappings for index in triangle]
        retained_count = sum(retained)
        print(retained_count)

        match retained_count:
            case 3:
                new_triangles.append([point_mappings[index] for index in triangle])
            case 1:
                index = retained.index(True)
                retained_index = triangle[index]
                retained_point = points[triangle[retained_index]]
                non_retained_indices = [idx for idx in triangle if idx != index]
                non_retained_points = [points[triangle[idx]] for idx in non_retained_indices]

                qs = [_intersection_point(retained_point, pt, cut_coeffs) for pt in non_retained_points]
                points.extend(qs)
                n = len(points)
                point_mappings[n-1] = mapped_index
                point_mappings[n] = mapped_index + 1
                mapped_index += 2
                new_triangle = [n-1, n]
                new_triangle.insert(index, point_mappings[retained_index])
                new_triangles.append(new_triangle)
            case 2:
                non_retained_index = retained.index(False)

                # Move the non-retained index to the end for simplicity
                shift = 2 - non_retained_index
                shifted_triangle = triangle[shift:] + triangle[:shift]
                shifted_pts = [points[idx] for idx in shifted_triangle]
                q02 = _intersection_point(shifted_pts[0], shifted_pts[2], cut_coeffs)
                q12 = _intersection_point(shifted_pts[1], shifted_pts[2], cut_coeffs)

                points.append(q02)
                points.append(q12)
                n = len(points)
                point_mappings[n-1] = mapped_index
                point_mappings[n] = mapped_index + 1
                mapped_index += 2
                new_triangles.append([shifted_triangle[0], shifted_triangle[1], n-1])
                new_triangles.append([shifted_triangle[1], n, n-1])


    new_points = []
    for index, point in enumerate(points):
        mapped = point_mappings.get(index, None)
        if mapped is not None:
            new_points.append(points[mapped])

    return new_points, new_triangles

