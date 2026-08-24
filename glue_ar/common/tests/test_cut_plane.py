import inspect
from itertools import product

import pytest

try:
    from glue_vispy_viewers.volume.viewer_state import (
        Vispy3DVolumeViewerState,
        cutting_plane_from_state,
    )
    CUTTING_PLANE_AVAILABLE = True
except ImportError:
    CUTTING_PLANE_AVAILABLE = False

if not CUTTING_PLANE_AVAILABLE:
    pytest.skip("Cutting plane functionality is not available", allow_module_level=True)

from glue_ar.common.cut_plane import (
    apply_cut_plane_to_isosurface,
    create_cut_plane_check,
)
from glue_ar.utils import xyz_bounds


def _permute_list(lst: list[float], permutation: list[int]) -> list[float]:
    return [lst[c] for c in permutation]


@pytest.mark.parametrize("index_permutation,cut_depth,cut_axis",
                         product([None, [1, 0, 2], [1, 2, 0], [2, 0, 1]],
                                 [0.0, 0.2, 0.5, 0.7],
                                 ["X", "Y", "Z"]))
def test_cut_plane_check_simple(index_permutation, cut_depth, cut_axis):
    viewer_state = Vispy3DVolumeViewerState()
    viewer_state.cut_enabled = True
    viewer_state.cut_depth = cut_depth
    viewer_state.resolution = 128
    viewer_state.cut_mode = "Simple"
    viewer_state.cut_axis = cut_axis

    bounds = xyz_bounds(viewer_state, with_resolution=True)

    index_permutation = index_permutation or [1, 2, 0]

    cp = cutting_plane_from_state(viewer_state)
    assert cp is not None

    check = create_cut_plane_check(viewer_state, bounds, index_permutation=index_permutation)
    zeros = [0.0, 0.0, 0.0]
    nonzero_index = ["X", "Y", "Z"].index(cut_axis)
    first_clipped = list(zeros)
    first_clipped[nonzero_index] = -(cp[3] - 1) / cp[nonzero_index]
    first_clipped = _permute_list(first_clipped, index_permutation)
    assert check(first_clipped)

    first_retained = list(zeros)
    first_retained[nonzero_index] = -2 * cp[3] / cp[nonzero_index]
    if cp[3] < 0:
        first_retained[nonzero_index] *= -1
    first_retained = _permute_list(first_retained, index_permutation)
    assert not check(first_retained)

    second_clipped = list(zeros)
    second_clipped[nonzero_index] = cp[3] / cp[nonzero_index]
    if cp[3] < 0:
        second_clipped[nonzero_index] = -(second_clipped[nonzero_index] - 1)
    second_clipped = _permute_list(second_clipped, index_permutation)
    assert check(second_clipped)

    second_retained = list(zeros)
    zero_indices = [idx for idx in range(3) if idx != nonzero_index]
    second_retained[zero_indices[0]] = 3
    second_retained[zero_indices[1]] = 2
    second_retained[nonzero_index] = -(cp[3] - 3 * cp[zero_indices[0]] - 2 * cp[zero_indices[1]]) / cp[nonzero_index]
    second_retained = _permute_list(second_retained, index_permutation)
    assert not check(second_retained)


@pytest.mark.parametrize("index_permutation,cut_depth,cut_tilt,cut_rotation",
                         product([None, [1, 0, 2], [1, 2, 0], [2, 0, 1]],
                                 [0.2, 0.5, 0.7],
                                 [0.5, 1, 1.25],
                                 [0.75, 1.1, 1.3]))
def test_cut_plane_check_advanced(index_permutation, cut_depth, cut_tilt, cut_rotation):
    viewer_state = Vispy3DVolumeViewerState()
    viewer_state.cut_enabled = True
    viewer_state.cut_depth = cut_depth
    viewer_state.resolution = 128
    viewer_state.cut_mode = "Advanced"
    viewer_state.cut_rotation = cut_rotation
    viewer_state.cut_tilt = cut_tilt

    bounds = xyz_bounds(viewer_state, with_resolution=True)

    index_permutation = index_permutation or [1, 2, 0]

    cp = cutting_plane_from_state(viewer_state)
    assert cp is not None

    check = create_cut_plane_check(viewer_state, bounds, index_permutation=index_permutation)
    first_clipped = [0.0, 0.0, (1 - cp[3]) / cp[2]]
    first_clipped = _permute_list(first_clipped, index_permutation)
    assert check(first_clipped)

    first_retained = [0.0, -2 * cp[3] / cp[1], 0.0]
    if cp[3] < 0:
        first_retained[1] *= -1
    first_retained = _permute_list(first_retained, index_permutation)
    assert not check(first_retained)

    second_clipped = [0.0, 0.0, cp[3] / cp[2]]
    if cp[3] < 0:
        second_clipped[2] = -(second_clipped[2] - 1)
    second_clipped = _permute_list(second_clipped, index_permutation)
    assert check(second_clipped)

    second_retained = [-(1 + cp[3] - 3 * cp[1] - 2 * cp[2] / cp[0]), 3.0, 2.0]
    if cp[0] > 0:
        second_retained[0] *= -1
    second_retained = _permute_list(second_retained, index_permutation)
    assert not check(second_retained)


@pytest.mark.parametrize("index_permutation,cut_enabled",
                         product([None, [1,2,0], [2,0,1]], [True, False]))
def test_cut_plane_check_type(index_permutation, cut_enabled):
    viewer_state = Vispy3DVolumeViewerState()
    viewer_state.cut_enabled = cut_enabled
    viewer_state.cut_depth = 0.5 
    viewer_state.resolution = 128
    bounds = xyz_bounds(viewer_state, with_resolution=True)

    check = create_cut_plane_check(viewer_state, bounds, index_permutation=index_permutation)
    assert callable(check)
    signature = inspect.signature(check)
    assert signature.return_annotation is bool
    assert "indices" in signature.parameters
    assert signature.parameters["indices"].annotation is list[int | float]


@pytest.mark.parametrize("index_permutation",
                         [None, [1,2,0], [2,0,1]])
def test_cut_plane_check_empty_plane_always_true(index_permutation):
    viewer_state = Vispy3DVolumeViewerState()
    viewer_state.cut_enabled = False
    viewer_state.resolution = 128
    bounds = xyz_bounds(viewer_state, with_resolution=True)

    check = create_cut_plane_check(viewer_state, bounds, index_permutation=index_permutation)
    assert check([1, 2, 3])
    assert check([2, 4, 7])
    assert check([0, 1, 2])
    assert check([128, 129, 130])


def test_apply_cut_plane_to_isosurface():
    viewer_state = Vispy3DVolumeViewerState()
    viewer_state.cut_enabled = True
    viewer_state.cut_depth = 0.5
    viewer_state.resolution = 128
    viewer_state.cut_mode = "Simple"
    viewer_state.cut_axis = "X"

    bounds = xyz_bounds(viewer_state, with_resolution=True)
    points = [
        # Retained
        [10.1, 17.2, 11.0],
        [62.1, 12.7, 24.7],
        [34.7, 19.6, 22.7],
        [92.4, 86.6, 22.7],
        # Clipped
        [54.1, 34.6, 102.1],
        [11.1, 67.5, 87.6],
        [16.2, 101.7, 76.5],
    ]

    triangles = [
        # Completely retained
        [0, 1, 2],
        [0, 1, 3],
        [1, 2, 3],
        # One point retained
        [2, 4, 5],
        [2, 4, 6],
        # Two points retained
        [0, 1, 4],
        [2, 3, 6],
        # Completely clipped
        [4, 5, 6],
    ]

    new_points, new_triangles = apply_cut_plane_to_isosurface(viewer_state, bounds, points, triangles)

    # (4 retained points)
    # + (2 new points each from triangles 3 & 4)
    # + (2 new points each from triangles 4 & 5)
    assert len(new_points) == 4 + (2 * 2) + (2 * 2)

    # 7 retained triangles
    # + 1 new triangle each from triangles 5 & 6
    assert len(new_triangles) == 7 + 2
