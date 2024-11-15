from itertools import product

from glue.core import Data
from glue.viewers.common.viewer import LayerArtist
from glue_jupyter.common.state3d import VolumeViewerState
from ..utils import *
from ..utils import clip_linear_transformations
from ..utils import clip_sides


def test_data_count():
    data1 = Data(label="Data 1")
    data2 = Data(label="Data 2")
    viewer_state = VolumeViewerState()

    layer1 = LayerArtist(viewer_state, layer=data1)
    layer1_2 = LayerArtist(viewer_state, layer=data1)
    layer2 = LayerArtist(viewer_state, layer=data2)

    assert data_count((layer1,)) == 1
    assert data_count((layer1, layer1_2)) == 1
    assert data_count((layer1, layer2)) == 2

    subset = data1.new_subset()
    subset_layer = LayerArtist(viewer_state, layer=subset)

    assert data_count((subset_layer,)) == 1
    assert data_count((layer1, subset_layer)) == 1
    assert data_count((layer2, subset_layer)) == 2


def test_export_label_for_layer():
    data = Data(label="Data")
    subset = data.new_subset(label="Subset")
    viewer_state = VolumeViewerState()
    data_layer = LayerArtist(viewer_state, layer=data)
    subset_layer = LayerArtist(viewer_state, layer=subset)

    assert export_label_for_layer(data_layer, add_data_label=True) == "Data"
    assert export_label_for_layer(data_layer, add_data_label=False) == "Data"

    assert export_label_for_layer(subset_layer, add_data_label=True) == "Subset (Data)"
    assert export_label_for_layer(subset_layer, add_data_label=False) == "Subset"


def test_slope_intercept_between():

    assert slope_intercept_between((3, 3), (1, 1)) == (1, 0)
    assert slope_intercept_between((3, 4), (1, 2)) == (1, 1)
    assert slope_intercept_between((-1, 5), (1, 5)) == (0, 5)
    assert slope_intercept_between((-1, 5), (1, 15)) == (5, 10)


def test_clip_linear_transformations():
    bounds = [(0, 2), (0, 8), (2, 6)]
    
    assert clip_linear_transformations(bounds) == [
        (0.25, -0.25),
        (0.25, -1),
        (0.25, -1)
    ]

    assert clip_linear_transformations(bounds, clip_size=2) == [
        (0.5, -0.5),
        (0.5, -2),
        (0.5, -2)
    ]

    assert clip_linear_transformations(bounds, stretches=(4, 0.5, 0.25)) == [
        (1, -1),
        (0.125, -0.5),
        (0.0625, -0.25)
    ]

    assert clip_linear_transformations(bounds, clip_size=4,
                                       stretches=(4, 0.5, 0.25)) == [
        (4, -4),
        (0.5, -2),
        (0.25, -1)
    ]


def test_layer_color():
    data = Data(label="Data")
    viewer_state = VolumeViewerState()
    layer = LayerArtist(viewer_state, layer=data)
    layer.state.color = "#abcdef"

    assert layer_color(layer.state) == "#abcdef"

    layer.state.color = "0.35"
    assert layer_color(layer.state) == "#808080"

    layer.state.color = "0.75"
    assert layer_color(layer.state) == "#808080"


def test_clip_sides_non_native():
    viewer_state = VolumeViewerState()
    viewer_state.native_aspect = False

    viewer_state.x_min = 0
    viewer_state.x_max = 8
    viewer_state.y_min = -2
    viewer_state.y_max = 2
    viewer_state.z_min = -1
    viewer_state.z_max = 1
    
    resolutions = (32, 64, 128, 256, 512)
    clip_sizes = (1, 2, 3, 5, 10)
    for resolution, clip_size in product(resolutions, clip_sizes):
        print(resolution, clip_size)
        viewer_state.resolution = resolution 
        size = 2 * clip_size / resolution
        print(size)
        assert clip_sides(viewer_state, clip_size=clip_size) == (size, size, size)


def test_clip_sides_native():
    viewer_state = VolumeViewerState()
    viewer_state.native_aspect = True

    viewer_state.x_min = 0
    viewer_state.x_max = 8
    viewer_state.y_min = -2
    viewer_state.y_max = 2
    viewer_state.z_min = -1
    viewer_state.z_max = 1

    resolutions = (32, 64, 128, 256, 512)
    clip_sizes = (1, 2, 3, 5, 10)
    for resolution, clip_size in product(resolutions, clip_sizes):
        viewer_state.resolution = resolution 
        max_size = 2 * clip_size / resolution
        assert clip_sides(viewer_state, clip_size=clip_size) == (max_size, max_size / 2, max_size / 4)
