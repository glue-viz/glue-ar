from os import remove
from random import random, randint, seed
from tempfile import NamedTemporaryFile

from gltflib import AccessorType, AlphaMode, BufferTarget, ComponentType, GLTFModel
from gltflib.gltf import GLTF
from glue.core import Data
from glue_qt.app import GlueApplication
from glue_vispy_viewers.scatter.qt.scatter_viewer import VispyScatterViewer

from glue_ar.common.export import export_viewer
from glue_ar.common.scatter_export_options import ARVispyScatterExportOptions
from glue_ar.common.shapes import sphere_points_count, sphere_triangles, sphere_triangles_count
from glue_ar.common.tests.gltf_helpers import count_indices, count_vertices, unpack_vertices
from glue_ar.utils import export_label_for_layer, hex_to_components, mask_for_bounds, xyz_bounds, xyz_for_layer


class TestScatterGLTF:

    def setup_method(self, method):
        seed(1374)
        self.n = 40
        x1 = [random() * 5 for _ in range(self.n)]
        y1 = [random() for _ in range(self.n)]
        z1 = [randint(1, 30) for _ in range(self.n)]
        self.data1 = Data(x=x1, y=y1, z=z1, label="Scatter Data 1")
        self.data1.style.color = "#fedcba"
        self.app = GlueApplication()
        self.app.data_collection.append(self.data1)
        self.viewer = self.app.new_data_viewer(VispyScatterViewer)
        self.viewer.add_data(self.data1)

        x2 = [random() * 7 for _ in range(self.n)]
        y2 = [randint(100, 200) for _ in range(self.n)]
        z2 = [random() for _ in range(self.n)]
        self.data2 = Data(x=x2, y=y2, z=z2, label="Scatter Data 2")

        self.viewer.state.x_att = self.data1.id['x']
        self.viewer.state.y_att = self.data1.id['y']
        self.viewer.state.z_att = self.data1.id['z']
        self.state_dictionary = {
            export_label_for_layer(layer): ("Scatter", ARVispyScatterExportOptions())
            for layer in self.viewer.layers
        }

    def teardown_method(self, method):
        if getattr(self, "tmpfile", None) is not None:
            self.tmpfile.close()
            remove(self.tmpfile.name)
        self.viewer.close(warn=False)
        self.viewer = None
        self.app.close()
        self.app = None

    def test_basic_export(self):
        bounds = xyz_bounds(self.viewer.state, with_resolution=False)
        self.tmpfile = NamedTemporaryFile(suffix=".gltf", delete=False)
        self.tmpfile.close()
        export_viewer(self.viewer.state,
                      [layer.state for layer in self.viewer.layers],
                      bounds=bounds,
                      state_dictionary=self.state_dictionary,
                      filepath=self.tmpfile.name)

        gltf: GLTF = GLTF.load(self.tmpfile.name)
        model = gltf.model
        assert isinstance(model, GLTFModel)

        assert model.buffers is not None and len(model.buffers) == 1
        assert model.bufferViews is not None and len(model.bufferViews) == 1 + self.n
        assert model.accessors is not None and len(model.accessors) == 1 + self.n
        assert model.meshes is not None and len(model.meshes) == self.n
        assert model.nodes is not None and len(model.nodes) == self.n
        assert model.materials is not None and len(model.materials) == 1

        material = model.materials[0]
        layer = self.viewer.layers[0]
        label = export_label_for_layer(layer)
        method, options = self.state_dictionary[label]
        assert method == "Scatter"
        assert isinstance(options, ARVispyScatterExportOptions)
        color_components = [c / 256 for c in hex_to_components("#fedcba")] + [layer.state.alpha]
        assert material.alphaMode == AlphaMode.BLEND.value
        assert material.pbrMetallicRoughness is not None
        assert material.pbrMetallicRoughness.baseColorFactor == color_components
        assert material.pbrMetallicRoughness.roughnessFactor == 1
        assert material.pbrMetallicRoughness.metallicFactor == 0

        assert all(mesh.primitives[0].indices == 0 for mesh in model.meshes)

        theta_resolution: int = options.theta_resolution
        phi_resolution: int = options.phi_resolution
        triangles_count = sphere_triangles_count(theta_resolution=theta_resolution,
                                                 phi_resolution=phi_resolution)
        points_count = sphere_points_count(theta_resolution=theta_resolution,
                                           phi_resolution=phi_resolution)

        assert count_indices(gltf, model.buffers[0], model.bufferViews[0]) == triangles_count
        assert count_vertices(gltf, model.buffers[0], model.bufferViews[1]) == points_count

        assert model.bufferViews[0].target == BufferTarget.ELEMENT_ARRAY_BUFFER.value
        assert model.bufferViews[1].target == BufferTarget.ARRAY_BUFFER.value

        indices_accessor = model.accessors[0]
        assert indices_accessor.bufferView == 0
        assert indices_accessor.componentType == ComponentType.UNSIGNED_INT.value
        assert indices_accessor.count == triangles_count * 3
        assert indices_accessor.type == AccessorType.SCALAR.value
        assert indices_accessor.min == [0]
        assert indices_accessor.max == [max(max(tri) for tri in sphere_triangles(theta_resolution=theta_resolution,
                                                                                 phi_resolution=phi_resolution))]

        for index, accessor in enumerate(model.accessors[1:]):
            assert accessor.bufferView == index + 1
            assert accessor.componentType == ComponentType.FLOAT.value
            assert accessor.count == points_count
            assert accessor.type == AccessorType.VEC3.value

        mask = mask_for_bounds(self.viewer.state, layer.state, bounds)
        data = xyz_for_layer(self.viewer.state, layer.state,
                             preserve_aspect=self.viewer.state.native_aspect,
                             mask=mask,
                             scaled=True)
        data = data[:, [1, 2, 0]]

        # Unpack the center of each sphere mesh matches the
        # corresponding data point
        tolerance = 1e-7
        for index, mesh in enumerate(model.meshes):
            buffer_view = model.bufferViews[mesh.primitives[0].attributes.POSITION]
            points = unpack_vertices(gltf, model.buffers[0], buffer_view)
            n_points = len(points)
            center = tuple(sum(p[i] for p in points) / n_points for i in range(3))
            data_point = data[index]
            assert all(abs(center[i] - data_point[i]) < tolerance for i in range(len(center)))
