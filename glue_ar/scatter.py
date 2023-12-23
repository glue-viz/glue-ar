import pyvista as pv
from glue_ar.utils import layer_color, xyz_for_layer


# For the 3D scatter viewer
def scatter_layer_as_points(viewer_state, layer_state):
    xyz = xyz_for_layer(viewer_state, layer_state)
    return {
        "data": xyz,
        "color": layer_color(layer_state),
        "opacity": layer_state.alpha,
        "style": "points_gaussian",
        "point_size": 5 * layer_state.size,
        "render_points_as_spheres": True
    }


def scatter_layer_as_spheres(viewer_state, layer_state):
    data = xyz_for_layer(viewer_state, layer_state)
    return {
        "data": [pv.Sphere(center=p) for p in data]
    }


def scatter_layer_as_glyphs(viewer_state, layer_state, glyph):
    data = xyz_for_layer(viewer_state, layer_state, scaled=True)
    points = pv.PointSet(data)
    glyphs = points.glyph(geom=glyph, orient=False, scale=False)
    return {
        "data": glyphs,
        "color": layer_color(layer_state),
        "opacity": layer_state.alpha,
    }


def scatter_layer_as_multiblock(viewer_state, layer_state,
                                theta_resolution=8,
                                phi_resolution=8,
                                scaled=True):
    data = xyz_for_layer(viewer_state, layer_state, scaled=scaled)
    spheres = [pv.Sphere(center=p, radius=layer_state.size_scaling * layer_state.size / 600, phi_resolution=phi_resolution, theta_resolution=theta_resolution) for p in data]
    blocks = pv.MultiBlock(spheres)
    geometry = blocks.extract_geometry()
    info = {
        "data": geometry,
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
        info["cmap"] = layer_state.cmap.name  # This assumes that we're using a matplotlib colormap
        info["clim"] = [layer_state.cmap_vmin, layer_state.cmap_vmax]
        info["scalars"] = "colors"
    return info
