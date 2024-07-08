from gltflib.gltf_resource import FileResource
from mcubes import marching_cubes
from numpy import isfinite, linspace, transpose
from uuid import uuid4
import operator
import struct

from gltflib import GLTF
from gltflib import Accessor, AccessorType, Asset, BufferTarget, BufferView, Primitive, \
    ComponentType, GLTFModel, Node, Scene, Attributes, Mesh, Buffer

from pxr import Gf, Sdf, Usd, UsdGeom, UsdLux, UsdShade, Vt

from glue_vispy_viewers.volume.layer_state import VolumeLayerState
from glue_vispy_viewers.volume.viewer_state import Vispy3DVolumeViewerState

from glue_ar.common.export import compress_gl
from glue_ar.utils import hex_to_components, isomin_for_layer, isomax_for_layer, layer_color
from glue_ar.gltf_utils import *


def unique_id():
    return uuid4().hex


def create_marching_cubes_gltf(
    viewer_state: Vispy3DVolumeViewerState,
    layer_state: VolumeLayerState,
):

    resolution = int(viewer_state.resolution)
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

    data[~isfinite(data)] = isomin - 10

    data = transpose(data, (1, 0, 2))

    isosurface_count = 30

    buffers = []
    buffer_views = []
    accessors = []
    meshes = []
    file_resources = []

    levels = linspace(isomin, isomax, isosurface_count)
    opacity = layer_state.alpha / isosurface_count
    color = layer_color(layer_state)
    color_components = hex_to_components(color)
    materials = [create_material_for_color(color_components, opacity)]

    for level in levels:
        barr = bytearray()
        level_bin = f"level_{level}.bin"

        points, triangles = marching_cubes(data, level)
        for pt in points:
            for coord in pt:
                barr.extend(struct.pack('f', coord))
        point_len = len(barr)

        for tri in triangles:
            for idx in tri:
                barr.extend(struct.pack('I', idx))
        triangle_len = len(barr) - point_len

        pt_mins = [min([operator.itemgetter(i)(pt) for pt in points]) for i in range(3)]
        pt_maxes = [max([operator.itemgetter(i)(pt) for pt in points]) for i in range(3)]
        tri_mins = [int(min([operator.itemgetter(i)(tri) for tri in triangles])) for i in range(3)]
        tri_maxes = [int(max([operator.itemgetter(i)(tri) for tri in triangles])) for i in range(3)]
       
        buffers.append(Buffer(byteLength=len(barr), uri=level_bin))

        buffer = len(buffers) - 1
        buffer_views.append(
            BufferView(buffer=buffer,
                       byteLength=point_len,
                       byteOffset=0,
                       target=BufferTarget.ARRAY_BUFFER.value,
            )
        )
        accessors.append(
            Accessor(bufferView=len(buffer_views)-1,
                     componentType=ComponentType.FLOAT.value,
                     count=len(points),
                     type=AccessorType.VEC3.value,
                     min=pt_mins,
                     max=pt_maxes,
            )
        )
        buffer_views.append(
            BufferView(buffer=buffer,
                       byteLength=triangle_len,
                       byteOffset=point_len,
                       target=BufferTarget.ELEMENT_ARRAY_BUFFER.value,
            )
        )
        accessors.append(
            Accessor(bufferView=len(buffer_views)-1,
                     componentType=ComponentType.UNSIGNED_INT.value,
                     count=len(triangles) * 3,
                     type=AccessorType.SCALAR.value,
                     min=tri_mins,
                     max=tri_maxes,
            )
        )
        meshes.append(
            Mesh(primitives=[
                Primitive(attributes=Attributes(POSITION=len(accessors)-2),
                          indices=len(accessors)-1,
                          material=0
                )]
            )
        )

        file_resources.append(FileResource(level_bin, data=barr))

    nodes = [Node(mesh=i) for i in range(len(meshes))]
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
    print(model)
    gltf = GLTF(model=model, resources=file_resources)
    gltf_filepath = "marching_cubes.gltf"
    glb_filepath = "marching_cubes.glb"
    gltf.export(gltf_filepath)
    gltf.export(glb_filepath)
    print("About to compress")
    compress_gl(glb_filepath)


def create_marching_cubes_usd(
    viewer_state: Vispy3DVolumeViewerState,
    layer_state: VolumeLayerState,
):

    resolution = int(viewer_state.resolution)
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

    data[~isfinite(data)] = isomin - 10

    data = transpose(data, (1, 0, 2))

    isosurface_count = 30

    output_filename = "marching_cubes.usdc"
    output_filepath = output_filename
    stage = Usd.Stage.CreateNew(output_filepath)
    UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.y)

    default_prim_key = "/world"
    default_prim = UsdGeom.Xform.Define(stage, default_prim_key).GetPrim()
    stage.SetDefaultPrim(default_prim)

    light = UsdLux.RectLight.Define(stage, "/light")
    light.CreateHeightAttr(-1)

    levels = linspace(isomin, isomax, isosurface_count)
    opacity = 0.5 * layer_state.alpha
    color = layer_color(layer_state)
    color_components = hex_to_components(color)

    # TODO: Refactor this into a utility function
    material = UsdShade.Material.Define(stage, "/material")
    pbr_shader = UsdShade.Shader.Define(stage, "/material/PBRShader")
    pbr_shader.CreateIdAttr("UsdPreviewSurface")
    pbr_shader.CreateInput("roughness", Sdf.ValueTypeNames.Float).Set(0.4)
    pbr_shader.CreateInput("metallic", Sdf.ValueTypeNames.Float).Set(0.0)
    pbr_shader.CreateInput("diffuseColor", Sdf.ValueTypeNames.Color3f).Set(tuple(c / 255 for c in color_components))
    pbr_shader.CreateInput("opacity", Sdf.ValueTypeNames.Float).Set(opacity)
    material.CreateSurfaceOutput().ConnectToSource(pbr_shader.ConnectableAPI(), "surface")

    for level in levels:
        points, triangles = marching_cubes(data, level)
        xform_key = f"{default_prim_key}/xform_{unique_id()}"
        UsdGeom.Xform.Define(stage, xform_key)
        surface_key = f"{xform_key}/level_{unique_id()}"
        surface = UsdGeom.Mesh.Define(stage, surface_key)
        surface.CreateSubdivisionSchemeAttr().Set(UsdGeom.Tokens.none)
        surface.CreatePointsAttr(points)
        surface.CreateFaceVertexCountsAttr([3] * len(triangles))
        surface.CreateFaceVertexIndicesAttr([int(idx) for tri in triangles for idx in tri])

        surface.GetPrim().ApplyAPI(UsdShade.MaterialBindingAPI)
        UsdShade.MaterialBindingAPI(surface).Bind(material)


    stage.GetRootLayer().Save()

