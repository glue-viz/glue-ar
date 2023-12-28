from numpy import array, clip, isnan, ones, sqrt
from numpy.linalg import norm
import pyvista as pv
from glue_ar.utils import layer_color, mask_for_bounds, xyz_bounds, xyz_for_layer


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


_VECTOR_OFFSETS = {
    'tail': 0,
    'middle': -0.5,
    'tip': -1
}


# This function creates a multiblock mesh for a given scatter layer
# Everything is scaled into clip space for better usability with e.g. model-viewer
def scatter_layer_as_multiblock(viewer_state, layer_state,
                                theta_resolution=8,
                                phi_resolution=8,
                                clip_to_bounds=True,
                                scaled=True):
    bounds = xyz_bounds(viewer_state)
    if clip_to_bounds:
        mask = mask_for_bounds(viewer_state, layer_state, bounds)
    else:
        mask = None
    data = xyz_for_layer(viewer_state, layer_state,
                         preserve_aspect=viewer_state.native_aspect,
                         mask=mask,
                         scaled=scaled)
    factor = max((abs(b[1] - b[0]) for b in bounds))
    if layer_state.size_mode == "Fixed":
        radius = layer_state.size_scaling * sqrt((layer_state.size)) / (7 * factor)
        spheres = [pv.Sphere(center=p, radius=radius,
                             phi_resolution=phi_resolution,
                             theta_resolution=theta_resolution) for p in data]
    else:
        # The specific size calculation is taken from the scatter layer artist
        size_data = layer_state.layer[layer_state.size_attribute].ravel()
        size_data = clip(size_data, layer_state.size_vmin, layer_state.size_vmax)
        if layer_state.size_vmax == layer_state.size_vmin:
            sizes = sqrt(ones(size_data.shape) * 10)
        else:
            sizes = sqrt((20 * (size_data - layer_state.size_vmin) /
                     (layer_state.size_vmax - layer_state.size_vmin)))
        sizes *= (layer_state.size_scaling / factor)
        sizes[isnan(sizes)] = 0.
        spheres = [pv.Sphere(center=p, radius=r,
                             phi_resolution=phi_resolution,
                             theta_resolution=theta_resolution) for p, r in zip(data, sizes)]
    blocks = pv.MultiBlock(spheres)

    if layer_state.vector_visible:
        tip_resolution = 10
        shaft_resolution = 10
        atts = [layer_state.vx_attribute, layer_state.vy_attribute, layer_state.vz_attribute]
        tip_factor = 0.25 if layer_state.vector_arrowhead else 0
        vector_data = [layer_state.layer[att].ravel()[mask] for att in atts]
        if viewer_state.native_aspect:
            factor = max((abs(b[1] - b[0]) for b in bounds))
            vector_data = [[0.5 * t / factor for t in v] for v in vector_data]
        else:
            bound_factors = [abs(b[1] - b[0]) for b in bounds]
            vector_data = [[0.5 * t / b for t in v] for v, b in zip(vector_data, bound_factors)]
        vector_data = array(list(zip(*vector_data)))

        arrows = []
        offset = _VECTOR_OFFSETS[layer_state.vector_origin]
        for pt, v in zip(data, vector_data):
            adjusted_v = v * layer_state.vector_scaling
            length = norm(adjusted_v)
            tip_length = tip_factor * length
            adjusted_pt = [c + offset * vc for c, vc in zip(pt, adjusted_v)]
            arrow = pv.Arrow(
                    start=adjusted_pt,
                    direction=v,
                    shaft_resolution=shaft_resolution,
                    tip_resolution=tip_resolution,
                    shaft_radius=0.002,
                    tip_radius=0.01,
                    scale=length,
                    tip_length=tip_length)
            arrows.append(arrow)

        blocks.extend(arrows)
        
    # Note:
    # each arrow has (4 * shaft_resolution) + tip_resolution + 1 points
    
    geometry = blocks.extract_geometry()
    info = {
        "mesh": geometry,
        "opacity": layer_state.alpha
    }
    if layer_state.color_mode == "Fixed":
        info["color"] = layer_color(layer_state)
    else:
        sphere_points = 2 + (phi_resolution - 2) * theta_resolution  # The number of points on each sphere
        cmap_values = layer_state.layer[layer_state.cmap_attribute][mask]
        point_cmap_values = [y for x in cmap_values for y in (x,) * sphere_points]
        if layer_state.vector_visible:
            arrow_points = (4 * shaft_resolution) + tip_resolution + 1
            point_cmap_values.extend([y for x in cmap_values for y in (x,) * arrow_points])
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
