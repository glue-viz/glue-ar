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


# TODO These types probably need adjustment
def adjust_isosurface_for_cut_plane(
    viewer_state: VolumeViewerState3D,
    bounds: BoundsWithResolution,
    points: List[List[float]],
    triangles: List[List[int]]
) -> [List[List[float]], List[List[int]]]:

    cut_plane_check = create_cut_plane_check(viewer_state, bounds)

    cut_plane = cutting_plane_from_state(viewer_state)

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
    for triangle in triangles:
        retained = [index in point_mappings for index in triangle]

        if all(retained):
            new_triangles.append([point_mappings[index] for index in triangle])
        elif any(retained):
           retained_count = sum(retained)
           if retained_count == 1:
               index = retained.index(True)
               retained_index = triangle[index]
               non_retained_indices = [idx for idx in triangle if idx != index]
