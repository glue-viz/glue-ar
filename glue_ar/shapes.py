from itertools import product
import math

from numpy import cross, pi

from glue_ar.gltf_utils import offset_triangles

__all__ = [
    "rectangular_prism_points",
    "rectangular_prism_triangulation",
    "sphere_mesh_index",
    "sphere_points",
    "sphere_triangles",
    "cylinder_points",
    "cylinder_triangles",
    "circular_cone_points",
    "circular_cone_triangles",
]


def rectangular_prism_points(center, sides):
    side_diffs = [(-s / 2, s / 2) for s in sides]
    diffs = product(*side_diffs)
    points = [tuple(c - d for c, d in zip(center, diff)) for diff in diffs]
    return points


def rectangular_prism_triangulation(start_index=0):
    triangles = [
        # side
        (start_index + 0, start_index + 2, start_index + 1),
        (start_index + 1, start_index + 2, start_index + 3),

        # side
        (start_index + 4, start_index + 7, start_index + 6),
        (start_index + 7, start_index + 4, start_index + 5),

        # bottom
        (start_index + 7, start_index + 3, start_index + 2),
        (start_index + 7, start_index + 2, start_index + 6),

        # top
        (start_index + 5, start_index + 4, start_index + 1),
        (start_index + 4, start_index + 0, start_index + 1),

        # side
        (start_index + 6, start_index + 2, start_index + 4),
        (start_index + 0, start_index + 4, start_index + 2),

        # side
        (start_index + 5, start_index + 1, start_index + 7),
        (start_index + 7, start_index + 1, start_index + 3),
    ]

    return triangles

def sphere_mesh_index(row, column, theta_resolution, phi_resolution):
    if row == 0:
        return 0
    elif row == theta_resolution - 1:
        return (theta_resolution - 2) * phi_resolution + 1
    else:
        column = column % phi_resolution
        return phi_resolution * (row - 1) + column + 1


def sphere_points(center, radius, theta_resolution=5, phi_resolution=5):
    # Number of points: phi_resolution * (theta_resolution - 2) + 2
    nonpole_thetas = [i * math.pi / theta_resolution for i in range(1, theta_resolution-1)]
    phis = [i * 2 * math.pi / phi_resolution for i in range(phi_resolution)]
    points = [(
        center[0] + radius * math.cos(phi) * math.sin(theta),
        center[1] + radius * math.sin(phi) * math.sin(theta),
        center[2] + radius * math.cos(theta)
    ) for theta, phi in product(nonpole_thetas, phis)]
    points = [(center[0], center[1], center[2] + radius)] + points + [(center[0], center[1], center[2] - radius)]

    return points


def sphere_triangles(theta_resolution=5, phi_resolution=5):
    triangles = [(int(0), i + 1, i) for i in range(1, phi_resolution)]
    tr, pr = theta_resolution, phi_resolution
    triangles.append((0, 1, theta_resolution))
    for row in range(1, theta_resolution - 1):
        for col in range(phi_resolution):
            rc_index = sphere_mesh_index(row, col, tr, pr)
            triangles.append((rc_index, sphere_mesh_index(row+1, col, tr, pr), sphere_mesh_index(row+1, col-1, tr, pr)))
            triangles.append((rc_index, sphere_mesh_index(row, col+1, tr, pr), sphere_mesh_index(row+1, col, tr, pr)))

    row = theta_resolution - 2
    last_index = sphere_mesh_index(theta_resolution - 1, 0, tr, pr)
    for col in range(phi_resolution):
        triangles.append((sphere_mesh_index(row, col, tr, pr), sphere_mesh_index(row, col+1, tr, pr), last_index))

    return triangles


def normalize(vector):
    magnitude = math.sqrt(sum(c * c for c in vector))
    return [c / magnitude for c in vector]


def orthogonal_basis(vector):
    first = [-vector[1], vector[0] + vector[2], -vector[1]]
    return [
        first,
        cross(vector, first),
    ]


def cylinder_points(center,
                    radius,
                    length,
                    central_axis,
                    theta_resolution=5):
    
    central_axis = normalize(central_axis)
    half_length = length / 2
    endcap_centers = [
        [c - a * half_length for c, a in zip(center, central_axis)],
        [c + a * half_length for c, a in zip(center, central_axis)]
    ]

    orthog_1, orthog_2 = orthogonal_basis(central_axis)

    thetas = [2 * pi * i / theta_resolution for i in range(theta_resolution)]

    return [
        [
            c + o1 * radius * math.cos(theta) + o2 * radius * math.sin(theta)
            for c, o1, o2 in zip(center, orthog_1, orthog_2)
        ]
        for center, theta in product(endcap_centers, thetas)
    ]


def cylinder_triangles(theta_resolution=5, start_index=0):
    bottom = [
        (0, i + 1, i) for i in range(1, theta_resolution-1)
    ]
    top = [
        (theta_resolution, theta_resolution + i, theta_resolution + i + 1) for i in range(1, theta_resolution-1)
    ]
    bottom_based_sides = [
        (i, (i + 1) % theta_resolution, i + theta_resolution) for i in range(theta_resolution)
    ]
    top_based_sides = [
        (i + theta_resolution, (i + 1) % theta_resolution, (i + 1) % theta_resolution + theta_resolution)
         for i in range(theta_resolution)
    ]
    if start_index > 0:
        bottom = offset_triangles(bottom, start_index)
        top = offset_triangles(top, start_index)
        bottom_based_sides = offset_triangles(bottom_based_sides, start_index)
        top_based_sides = offset_triangles(top_based_sides, start_index)

    return [t for v in (bottom, top, bottom_based_sides, top_based_sides) for t in v]


def circular_cone_points(base_center,
                radius,
                height,
                central_axis,
                theta_resolution=5):

    central_axis = normalize(central_axis)
    orthog_1, orthog_2 = orthogonal_basis(central_axis)
    thetas = [2 * pi * i / theta_resolution for i in range(theta_resolution)]
    top = [c + height * a for c, a in zip(base_center, central_axis)]

    return [top] + [
        [
            c + o1 * radius * math.cos(theta) + o2 * radius * math.sin(theta)
            for c, o1, o2 in zip(base_center, orthog_1, orthog_2)
        ]
        for theta in thetas
    ]


def circular_cone_triangles(theta_resolution=5, start_index=0):
    sides = [(start_index, start_index + i, start_index + 1 + (i % theta_resolution)) for i in range(1, theta_resolution + 1)]
    bottom = [
        (start_index + i, start_index + 1, 1 + start_index + (i % theta_resolution))
        for i in range(2, theta_resolution)
    ]

    return sides + bottom
