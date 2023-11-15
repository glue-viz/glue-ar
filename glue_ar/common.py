import pyvista as pv

def layers_info(info_creator, viewer_state, layer_states=None):
    info = {}
    if layer_states is None:
        layer_states = list((l for l in viewer_state.layers if l.visible))

    for layer_state in layer_states:
        info[layer_state.layer.uuid] = info_creator(viewer_state, layer_state)

    return info


def create_plotter(adder, info_creator, viewer_state, layer_states=None):
    plotter = pv.Plotter()

    info = layers_info(info_creator, viewer_state, layer_states)
    for layer_info in info.values():
        data = layer_info.pop("data")
        adder(plotter, data, **layer_info)

    return plotter
