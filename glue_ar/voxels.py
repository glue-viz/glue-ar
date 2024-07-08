from math import floor
from numpy import isfinite, argwhere, transpose
from os.path import join
import operator
import struct

from glue_vispy_viewers.volume.layer_state import VolumeLayerState
from glue_vispy_viewers.volume.viewer_state import Vispy3DVolumeViewerState
from glue_ar.common.export import compress_gl

from glue_ar.utils import hex_to_components, isomin_for_layer, isomax_for_layer, layer_color

from glue_ar.gltf_utils import *

from gltflib import Accessor, AccessorType, Asset, BufferTarget, BufferView, Primitive, \
    ComponentType, GLTFModel, Node, Scene, Attributes, Mesh, Buffer
from gltflib.gltf import GLTF
from gltflib.gltf_resource import FileResource


def create_voxel_export(
    viewer_state: Vispy3DVolumeViewerState,
    layer_state: VolumeLayerState,
    precomputed_frbs=None
):
    n_opacities = 100
    color = layer_color(layer_state)
    color_components = hex_to_components(color)
    materials = [create_material_for_color(color_components, i / n_opacities) for i in range(n_opacities + 1)]

    # resolution = int(viewer_state.resolution)
    resolution = 512
    bounds = [
        (viewer_state.z_min, viewer_state.z_max, resolution),
        (viewer_state.y_min, viewer_state.y_max, resolution),
        (viewer_state.x_min, viewer_state.x_max, resolution)
    ]

    # For now, only consider one layer
    # shape = (resolution, resolution, resolution)
    data = layer_state.layer.compute_fixed_resolution_buffer(
            target_data=layer_state.layer,
            bounds=bounds,
            target_cid=layer_state.attribute)

    isomin = isomin_for_layer(viewer_state, layer_state) 
    isomax = isomax_for_layer(viewer_state, layer_state) 

    data[~isfinite(data)] = isomin - 1

    data = transpose(data, (1, 0, 2))

    x_range = viewer_state.x_max - viewer_state.x_min
    y_range = viewer_state.y_max - viewer_state.y_min
    z_range = viewer_state.z_max - viewer_state.z_min
    x_spacing = x_range / resolution
    y_spacing = y_range / resolution
    z_spacing = z_range / resolution
    sides = (z_spacing, x_spacing, y_spacing)

    world_bounds = (
        (viewer_state.z_min, viewer_state.z_max),
        (viewer_state.x_min, viewer_state.x_max),
        (viewer_state.y_min, viewer_state.y_max),
    )
    # world_positions = [linspace(bds[0], bds[1], resolution) for bds in world_bounds]
    clip_transforms = clip_linear_transformations(world_bounds, clip_size=1)
    clip_sides = [s * transform[0] for s, transform in zip(sides, clip_transforms)]

    point_index = 0
    buffer_views = []
    accessors = []
    meshes = []
    points_barr = bytearray()
    triangles_barr = bytearray()
    points_bin = "points.bin"
    triangles_bin = "triangles.bin"

    triangles = rectangular_prism_triangulation()
    triangles_barr = bytearray()
    for triangle in triangles:
        for idx in triangle:
            triangles_barr.extend(struct.pack('I', idx))
    triangle_barrlen = len(triangles_barr)

    buffer_views = [
        BufferView(buffer=1,
                   byteLength=triangle_barrlen,
                   byteOffset=0,
                   target=BufferTarget.ELEMENT_ARRAY_BUFFER.value,
        )
    ]

    accessors = [
        Accessor(bufferView=0,
                 componentType=ComponentType.UNSIGNED_INT.value,
                 count=len(triangles) * 3,
                 type=AccessorType.SCALAR.value,
                 min=[0],
                 max=[7]
        )
    ]

    opacity_cutoff = 0.1
    opacity_factor = 0.75
    isorange = isomax - isomin
    nonempty_indices = argwhere(layer_state.alpha * opacity_factor * (data - isomin) / isorange)
    print(nonempty_indices[0])
    for indices in nonempty_indices:
        center = tuple((index + 0.5) * side for index, side in zip(indices, clip_sides))

        pts = rectangular_prism_points(center, clip_sides)
        point_index += len(pts)
        value = data[*indices]
        adjusted_value = min(max(layer_state.alpha * opacity_factor * (value - isomin) / isorange, 0), 1)
        print(adjusted_value)
        if adjusted_value < opacity_cutoff:
            continue

        print("Keeping it!")
        material_index = floor(adjusted_value * n_opacities)

        prev_ptbarr_len = len(points_barr)
        for pt in pts:
            for coord in pt:
                points_barr.extend(struct.pack('f', coord))
        ptbarr_len = len(points_barr)

        pt_mins = [min([operator.itemgetter(i)(pt) for pt in pts]) for i in range(3)]
        pt_maxes = [max([operator.itemgetter(i)(pt) for pt in pts]) for i in range(3)]

        # We're going to use two buffers
        # The first one (index 0) for the points
        # and the second one (index 1) for the triangles
        buffer_views.append(
            BufferView(buffer=0,
                       byteLength=ptbarr_len-prev_ptbarr_len,
                       byteOffset=prev_ptbarr_len,
                       target=BufferTarget.ARRAY_BUFFER.value,
            )
        )
        accessors.append(
            Accessor(bufferView=len(buffer_views)-1,
                     componentType=ComponentType.FLOAT.value,
                     count=len(pts),
                     type=AccessorType.VEC3.value,
                     min=pt_mins,
                     max=pt_maxes,
            )
        )
        meshes.append(
            Mesh(primitives=[
                Primitive(attributes=Attributes(POSITION=len(accessors)-1),
                          indices=0,
                          material=material_index,
                )]
            )
        )

    print(len(accessors))
    print(resolution ** 3)


    points_buffer = Buffer(byteLength=len(points_barr), uri=points_bin)
    triangles_buffer = Buffer(byteLength=len(triangles_barr), uri=triangles_bin)
    buffers = [points_buffer, triangles_buffer]

    nodes = [Node(mesh=i) for i in range(len(meshes))]

    file_resources = [
        FileResource(points_bin, data=points_barr),
        FileResource(triangles_bin, data=triangles_barr),
    ]
    
    node_indices = list(range(len(nodes)))

    model = GLTFModel(
        asset=Asset(version='2.0'),
        scenes=[Scene(nodes=node_indices)],
        nodes=nodes,
        meshes=meshes,
        buffers=buffers,
        bufferViews=buffer_views,
        accessors=accessors,
        materials=materials
    )
    gltf = GLTF(model=model, resources=file_resources)
    gltf_filepath = "voxel_test.gltf"
    glb_filepath = "voxel_test.glb"
    gltf.export(gltf_filepath)
    gltf.export(glb_filepath)
    # print("About to compress")
    # compress_gl(glb_filepath)


def test_prism_mesh():

    center = (0, 0, 0)
    sides = (1, 1, 3)
    points = rectangular_prism_points(center, sides)
    triangles = rectangular_prism_triangulation()
    point_mins = [min([operator.itemgetter(i)(point) for point in points]) for i in range(3)]
    point_maxes = [max([operator.itemgetter(i)(point) for point in points]) for i in range(3)]
    
    output_directory = "out"
    
    N_POINTS = 8
    arr = bytearray()
    for point in points:
        for coord in point:
            arr.extend(struct.pack('f', coord))
    
    triangles_offset = len(arr)
    for triangle in triangles:
        for index in triangle:
            arr.extend(struct.pack('I', index))
    
    buffer = Buffer(byteLength=len(arr), uri="buf.bin")
    buffer_views = [
        BufferView(buffer=0, byteLength=triangles_offset, target=BufferTarget.ARRAY_BUFFER.value),
        BufferView(buffer=0, byteOffset=triangles_offset, byteLength=len(arr)-triangles_offset, target=BufferTarget.ELEMENT_ARRAY_BUFFER.value)
    ]
    accessors = [
        Accessor(bufferView=0, componentType=ComponentType.FLOAT.value, count=N_POINTS, type=AccessorType.VEC3.value, min=point_mins, max=point_maxes),
        Accessor(bufferView=1, componentType=ComponentType.UNSIGNED_INT.value, count=len(triangles) * 3, type=AccessorType.SCALAR.value, min=[0], max=[N_POINTS-1])
    ]
    file_resources = [FileResource("buf.bin", data=arr)]
    
    model = GLTFModel(
        asset=Asset(version='2.0'),
        scenes=[Scene(nodes=[0])],
        nodes=[Node(mesh=0)],
        meshes=[Mesh(primitives=[Primitive(attributes=Attributes(POSITION=0), indices=1)])],
        buffers=[buffer],
        bufferViews=buffer_views,
        accessors=accessors
    )
    gltf = GLTF(model=model, resources=file_resources)
    gltf.export(join(output_directory, "prism.gltf"))
    gltf.export(join(output_directory, "prism.glb"))


if __name__ == "__main__":
    test_prism_mesh()
