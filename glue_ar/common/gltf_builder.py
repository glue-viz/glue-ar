from gltflib import Asset, GLTFModel, Node, Scene
from gltflib.gltf import GLTF 


class GLTFBuilder:

    def __init__(self):
        self.materials = []
        self.meshes = []
        self.buffers = []
        self.buffer_views = []
        self.accessors = []
        self.file_resources = []

    def add_material(self, material):
        self.materials.append(material)
    
    def add_mesh(self, mesh):
        self.meshes.append(mesh)

    def add_buffer(self, buffer):
        self.buffers.append(buffer)

    def add_buffer_view(self, view):
        self.buffer_views.append(view)

    def add_accessor(self, accessor):
        self.accessors.append(accessor)

    def add_file_resource(self, resource):
        self.file_resources.append(resource)

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
            materials=self.materials,
        )

    def build(self):
        model = self.build_model()
        return GLTF(model=model, resources=self.file_resources)
