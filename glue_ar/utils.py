from glue.core.subset_group import GroupedSubset
from numpy import array


def isomin_for_layer(viewer_state, layer):
    if isinstance(layer.layer, GroupedSubset):
        for viewer_layer in viewer_state.layers:
            if viewer_layer.layer is layer.layer.data:
                return viewer_layer.vmin

    return layer.vmin


def xyz_bounds(viewer_state):
    return [(viewer_state.x_min, viewer_state.x_max),
            (viewer_state.y_min, viewer_state.y_max),
            (viewer_state.z_min, viewer_state.z_max)]


# TODO: Make this better?
# glue-plotly has had to deal with similar issues,
# the utilities there are at least better than this
def layer_color(layer_state):
    layer_color = layer_state.color
    if layer_color == '0.35' or layer_color == '0.75':
        layer_color = 'gray'
    return layer_color


# TODO: Worry about efficiency later
def xyz_for_layer(viewer_state, layer_state, scaled=False):
    xs = layer_state.layer[viewer_state.x_att]
    ys = layer_state.layer[viewer_state.y_att]
    zs = layer_state.layer[viewer_state.z_att]
    vals = [xs, ys, zs]

    if scaled:
        bounds = xyz_bounds(viewer_state)
        for idx, bds in enumerate(bounds):
            m = 2 / (bds[1] - bds[0])
            b = (bds[0] + bds[1]) / (bds[1] - bds[0])
            vals[idx] = m * vals[idx] + b
        
    return array(list(zip(*vals)))
