from numpy import invert
import pyvista as pv
from scipy.ndimage import filters

from glue.core.subset_group import GroupedSubset
from glue_ar.utils import isomin_for_layer, layer_color 

# For the 3D volume viewer
# This is largely lifted from Luca's plugin
def create_meshes(viewer_state, layer_states=None, use_gaussian_filter=False, smoothing_iteration_count=0):

    meshes = {}

    bounds = [(viewer_state.z_min, viewer_state.z_max, viewer_state.resolution),
              (viewer_state.y_min, viewer_state.y_max, viewer_state.resolution),
              (viewer_state.x_min, viewer_state.x_max, viewer_state.resolution)]

    if layer_states is None:
        layer_states = list(viewer_state.layers)

    for layer_state in layer_states:

        if not isinstance(layer_state.layer, GroupedSubset):
            data = layer_state.layer.compute_fixed_resolution_buffer(
                target_data=viewer_state.reference_data,
                bounds=bounds,
                target_cid=layer_state.attribute
            )

            meshes[layer_state.layer.uuid] = {
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

            datacube = meshes[parent.uuid]["data"]
            data = subcube * datacube

            meshes[layer_state.layer.uuid] = {
                "data": data,
                "isomin": isomin_for_layer(viewer_state, layer_state),
                "opacity": layer_state.alpha,
                "color": layer_color(layer_state),
                "name": layer_state.layer.label
            }

            # Delete sublayer data from parent data
            if parent.uuid in meshes:
                parent_data = meshes[parent.uuid]["data"]
                parent_data = invert(subcube) * parent_data
                meshes[parent.uuid]["data"] = parent_data


    for item in meshes.values():
        data = item["data"]
        isomin = item["isomin"]

        if use_gaussian_filter:
            data = filters.gaussian_filters(data, 1)

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

        item["mesh"] = isodata

    return meshes

