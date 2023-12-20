from numpy import invert
import pyvista as pv
from scipy.ndimage import gaussian_filter

from glue.core.subset_group import GroupedSubset
from glue_ar.utils import isomin_for_layer, layer_color

test_parent_cube = None
test_subcube = None
test_data = None


# Trying to export each layer individually, rather than doing all of the meshes
# as a global operation on the viewer.
# The main difference here is that we aren't excising the subset points from
# the parent mesh as Luca's plugin did.
# But glue isn't going to be doing that, and if we have opacity then we should(?)
# get the same effect as in glue in the exported file
def meshes_for_volume_layer(viewer_state, layer_state, bounds, use_gaussian_filter=False, smoothing_iteration_count=0):

    global test_parent_cube
    global test_subcube
    global test_data

    # TODO: Allow passing in a dictionary of precomputed FRBs (keyed by label)
    # so that when we're running this across a viewer, we can possibly avoid repeated FRB computation

    layer_content = layer_state.layer
    parent = layer_content.data if isinstance(layer_content, GroupedSubset) else layer_content
    if parent is layer_content:
        parent_layer_state = layer_state
    else:
        for state in viewer_state.layers:
            if state.layer is layer_content:
                parent_layer_state = state
                break

    data = parent.compute_fixed_resolution_buffer(
        target_data=viewer_state.reference_data,
        bounds=bounds,
        target_cid=parent_layer_state.attribute)

    if isinstance(layer_state.layer, GroupedSubset):
        subcube = parent.compute_fixed_resolution_buffer(
            target_data=viewer_state.reference_data,
            bounds=bounds,
            subset_state=layer_state.layer.subset_state
        )
        test_parent_cube = data
        data = subcube * data 

        test_subcube = subcube
        test_data = data

    if use_gaussian_filter:
        data = gaussian_filter(data, 1)

    isomin = isomin_for_layer(viewer_state, layer_state)

    # Conventions between pyvista and glue data storage
    data = data.transpose(2, 1, 0)

    grid = pv.ImageData()
    grid.dimensions = (viewer_state.resolution,) * 3
    grid.origin = (viewer_state.x_min, viewer_state.y_min, viewer_state.z_min)
    # Comment from Luca: # I think the voxel spacing will always be 1, because of how glue downsamples to a fixed resolution grid. But don't hold me to this!
    grid.spacing = (1, 1, 1)
    grid.point_data["values"] = data.flatten(order="F")
    isodata = grid.contour([isomin])

    if smoothing_iteration_count > 0:
        isodata = isodata.smooth(n_iter=smoothing_iteration_count)

    return {
        "data": isodata,
        "color": layer_color(layer_state),
        "opacity": layer_state.alpha,
        # "isomin": isomin,
    }


def bounds_3d(viewer_state):
    return [(viewer_state.z_min, viewer_state.z_max, viewer_state.resolution),
              (viewer_state.y_min, viewer_state.y_max, viewer_state.resolution),
              (viewer_state.x_min, viewer_state.x_max, viewer_state.resolution)]


# For the 3D volume viewer
# This is largely lifted from Luca's plugin
def create_meshes(viewer_state, layer_states, parameters):

    meshes = {}

    bounds = bounds_3d(viewer_state)

    if layer_states is None:
        layer_states = list(viewer_state.layers)

    for layer_state in layer_states:

        if not isinstance(layer_state.layer, GroupedSubset):
            data = layer_state.layer.compute_fixed_resolution_buffer(
                target_data=viewer_state.reference_data,
                bounds=bounds,
                target_cid=layer_state.attribute
            )

            meshes[layer_state.layer.label] = {
                "data": data,
                "color": layer_color(layer_state),
                "opacity": layer_state.alpha,
                "isomin": isomin_for_layer(viewer_state, layer_state),
                "name": layer_state.layer.label
            }

    for layer_state in layer_states:

        if isinstance(layer_state.layer, GroupedSubset):
            parent = layer_state.layer.data
            subcube = parent.compute_fixed_resolution_buffer(
                target_data=viewer_state.reference_data,
                bounds=bounds,
                subset_state=layer_state.layer.subset_state
            )

            datacube = meshes[parent.label]["data"]
            data = subcube * datacube

            meshes[layer_state.layer.label] = {
                "data": data,
                "isomin": isomin_for_layer(viewer_state, layer_state),
                "opacity": layer_state.alpha,
                "color": layer_color(layer_state),
                "name": layer_state.layer.label
            }

            # Delete sublayer data from parent data
            if parent.label in meshes:
                parent_data = meshes[parent.label]["data"]
                parent_data = invert(subcube) * parent_data
                meshes[parent.label]["data"] = parent_data


    for label, item in meshes.items():
        data = item["data"]
        isomin = item["isomin"]

        if parameters[label]["gaussian_filter"]:
            data = gaussian_filter(data, 1)

        # Conventions between pyvista and glue data storage
        data = data.transpose(2, 1, 0)

        grid = pv.ImageData()
        grid.dimensions = (viewer_state.resolution,) * 3
        grid.origin = (viewer_state.x_min, viewer_state.y_min, viewer_state.z_min)
        # Comment from Luca: # I think the voxel spacing will always be 1, because of how glue downsamples to a fixed resolution grid. But don't hold me to this!
        grid.spacing = (1, 1, 1)
        grid.point_data["values"] = data.flatten(order="F")
        isodata = grid.contour([isomin])

        iterations = parameters[label]["smoothing_iterations"]
        if iterations > 0:
            isodata = isodata.smooth(n_iter=iterations)

        item["mesh"] = isodata

    return meshes

