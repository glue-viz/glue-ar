from glue.core.subset_group import GroupedSubset
from numpy import array, inf


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


def bounds_3d_from_layers(viewer_state, layer_states):
    mins = [inf, inf, inf]
    maxes = [-inf, -inf, -inf]
    atts = viewer_state.x_att, viewer_state.y_att, viewer_state.z_att
    for state in layer_states:
        data = state.layer.layer
        mins = [min(min(data[att]), m) for m, att in zip(mins, atts)]
        maxes = [max(max(data[att]), m) for m, att in zip(maxes, atts)]
        print(mins)
    return [(l, u) for l, u in zip(mins, maxes)]


# TODO: Make this better?
# glue-plotly has had to deal with similar issues,
# the utilities there are at least better than this
def layer_color(layer_state):
    layer_color = layer_state.color
    if layer_color == '0.35' or layer_color == '0.75':
        layer_color = 'gray'
    return layer_color


def scale(data, bounds, preserve_aspect=True):
    if preserve_aspect:
        ranges = [abs(bds[1] - bds[0]) for bds in bounds]
        max_range = max(ranges)
        index = ranges.index(max_range)
        bds = bounds[index]
        m = 2 / (bds[1] - bds[0])
        b = (bds[0] + bds[1]) / (bds[1] - bds[0])
        scaled = [[m * v + b for v in d] for d in data]
    else:
        scaled = []
        for idx, bds in enumerate(bounds):
            m = 2 / (bds[1] - bds[0])
            b = (bds[0] + bds[1]) / (bds[1] - bds[0])
            scaled.append([m * d + b for d in data[idx]])
    
    return scaled


# TODO: Worry about efficiency later
def xyz_for_layer(viewer_state, layer_state,
                  scaled=False,
                  preserve_aspect=True,
                  clip_to_bounds=True):
    xs = layer_state.layer[viewer_state.x_att]
    ys = layer_state.layer[viewer_state.y_att]
    zs = layer_state.layer[viewer_state.z_att]
    vals = [xs, ys, zs]

    if scaled or clip_to_bounds:
        bounds = xyz_bounds(viewer_state)
        if clip_to_bounds:
            xs, ys, zs = [], [], []
            for x, y, z in zip(*vals):
                if (x >= bounds[0][0] and x <= bounds[0][1]) and \
                   (y >= bounds[1][0] and y <= bounds[1][1]) and \
                   (z >= bounds[2][0] and z <= bounds[2][1]):
                       xs.append(x)
                       ys.append(y)
                       zs.append(z)
            vals = [xs, ys, zs]


        if scaled:
            vals = scale(vals, bounds, preserve_aspect=preserve_aspect)
        
    return array(list(zip(*vals)))
