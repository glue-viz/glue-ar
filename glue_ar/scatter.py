from numpy import isnan, ones
import pyvista as pv
from glue_ar.utils import layer_color, xyz_bounds, xyz_for_layer


# For the 3D scatter viewer
def scatter_layer_as_points(viewer_state, layer_state):
    xyz = xyz_for_layer(viewer_state, layer_state)
    return {
        "mesh": xyz,
        "color": layer_color(layer_state),
        "opacity": layer_state.alpha,
        "style": "points_gaussian",
        "point_size": 5 * layer_state.size,
        "render_points_as_spheres": True
    }


def scatter_layer_as_spheres(viewer_state, layer_state):
    data = xyz_for_layer(viewer_state, layer_state)
    return {
        "mesh": [pv.Sphere(center=p) for p in data]
    }


def scatter_layer_as_glyphs(viewer_state, layer_state, glyph):
    data = xyz_for_layer(viewer_state, layer_state, scaled=True)
    points = pv.PointSet(data)
    glyphs = points.glyph(geom=glyph, orient=False, scale=False)
    return {
        "mesh": glyphs,
        "color": layer_color(layer_state),
        "opacity": layer_state.alpha,
    }


# This function creates a multiblock mesh for a given scatter layer
# Everything is scaled into clip space for better usability with e.g. model-viewer
def scatter_layer_as_multiblock(viewer_state, layer_state,
                                theta_resolution=8,
                                phi_resolution=8,
                                scaled=True,
                                clip_to_bounds=True):
    data = xyz_for_layer(viewer_state, layer_state,
                         preserve_aspect=viewer_state.native_aspect,
                         clip_to_bounds=clip_to_bounds,
                         scaled=scaled)
    bounds = xyz_bounds(viewer_state)
    factor = max((abs(b[1] - b[0]) for b in bounds))
    if layer_state.size_mode == "Fixed":
        radius = (layer_state.size_scaling * layer_state.size) / factor
        spheres = [pv.Sphere(center=p, radius=radius,
                             phi_resolution=phi_resolution,
                             theta_resolution=theta_resolution) for p in data]
    else:
        # The specific size calculation is take from the scatter layer artist
        size_data = layer_state.layer[layer_state.size_attribute].ravel()
        if layer_state.size_vmax == layer_state.size_vmin:
            sizes = ones(size_data.shape) * 10
        else:
            sizes = (20 * (size_data - layer_state.size_vmin) /
                     (layer_state.size_vmax - layer_state.size_vmin))
        sizes *= (layer_state.size_scaling / factor)
        sizes[isnan(size_data)] = 0.
        spheres = [pv.Sphere(center=p, radius=r,
                             phi_resolution=phi_resolution,
                             theta_resolution=theta_resolution) for p, r in zip(data, sizes)]
    blocks = pv.MultiBlock(spheres)
    geometry = blocks.extract_geometry()

    info = {
        "mesh": geometry,
        "opacity": layer_state.alpha
    }
    if layer_state.color_mode == "Fixed":
        info["color"] = layer_color(layer_state)
    else:
        # sphere_cells = 2 * (phi_resolution - 2) * theta_resolution  # The number of cells on each sphere
        sphere_points = 2 + (phi_resolution - 2) * theta_resolution  # The number of points on each sphere
        cmap_values = layer_state.layer[layer_state.cmap_attribute]
        # cell_cmap_values = [y for x in cmap_values for y in (x,) * sphere_cells]
        point_cmap_values = [y for x in cmap_values for y in (x,) * sphere_points]
        # geometry.cell_data["colors"] = cell_cmap_values
        geometry.point_data["colors"] = point_cmap_values
        cmap = layer_state.cmap.name  # This assumes that we're using a matplotlib colormap
        clim = [layer_state.cmap_vmin, layer_state.cmap_vmax]
        if clim[0] > clim[1]:
            clim = [clim[1], clim[0]]
            cmap = f"{cmap}_r"
        info["cmap"] = cmap
        info["clim"] = clim
        info["scalars"] = "colors"

    return info
