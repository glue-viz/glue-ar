from gltflib import Accessor, Asset, Attributes, Buffer, BufferView, GLTFModel, \
        Material, Mesh, Node, PBRMetallicRoughness, Primitive, PrimitiveMode, Scene
from gltflib.gltf import GLTF 
from gltflib.gltf_resource import FileResource


class GLTFBuilder:

    def __init__(self):
        self.materials = []
        self.meshes = []
        self.buffers = []
        self.buffer_views = []
        self.accessors = []
        self.file_resources = []

    def add_material(self, color, opacity=1,
                     roughness_factor=1, metallic_factor=0,
                     alpha_mode="BLEND"):
        if any(c > 1 for c in color):
            color = [c / 256 for c in color[:3]]
        self.materials.append(
            Material(
                pbrMetallicRoughness=PBRMetallicRoughness(
                    baseColorFactor=color + [opacity],
                    roughnessFactor=roughness_factor,
                    metallicFactor=metallic_factor
                ),
                alphaMode=alpha_mode
            )
        )
        return self
    
    def add_mesh(self, position_accessor, indices_accessor, material=None,
                 mode=PrimitiveMode.TRIANGLES):
        primitive_kwargs = { "mode": mode }
        if material:
            primitive_kwargs["material"] = material
        self.meshes.append(
            Mesh(primitives=[
                Primitive(attributes=Attributes(POSITION=position_accessor),
                          indices=indices_accessor,
                          **primitive_kwargs,
                )]
            )
        )
        return self

    def add_buffer(self, byte_length, uri):
        self.buffers.append(
            Buffer(
                byteLength=byte_length,
                uri=uri
            )
        )
        return self

    def add_buffer_view(self, buffer, byte_length, byte_offset, target):
        self.buffer_views.append(
            BufferView(
                buffer=buffer,
                byteLength=byte_length,
                byteOffset=byte_offset,
                target=target
            )
        )
        return self

    def add_accessor(self, buffer_view, component_type, count,
                     type, mins, maxes):
        self.accessors.append(
            Accessor(
                bufferView=buffer_view,
                componentType=component_type,
                count=count,
                type=type,
                min=mins,
                max=maxes,
            )
        )
        return self

    def add_file_resource(self, filename, data):
        self.file_resources.append(
            FileResource(
                filename,
                data=data,
            )
        )
        return self

    @property
    def material_count(self):
        return len(self.materials)

    @property
    def mesh_count(self):
        return len(self.meshes)

    @property
    def buffer_count(self):
        return len(self.buffers)

    @property
    def buffer_view_count(self):
        return len(self.buffer_views)

    @property
    def accessor_count(self):
        return len(self.accessors)

    def build_model(self):
        nodes = [Node(mesh=i) for i in range(len(self.meshes))]
        node_indices = list(range(len(nodes)))
        scenes = [Scene(nodes=node_indices)]
        return GLTFModel(
            asset=Asset(version="2.0"),
            scenes=scenes,
            nodes=nodes,
            meshes=self.meshes,
            buffers=self.buffers,
            bufferViews=self.buffer_views,
            accessors=self.accessors,
            materials=self.materials or None,
        )

    def build(self):
        model = self.build_model()
        return GLTF(model=model, resources=self.file_resources)
