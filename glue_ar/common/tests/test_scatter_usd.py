from os import remove
from random import random, randint, seed
from tempfile import NamedTemporaryFile
from typing import Dict, Tuple, Type, Union

from glue.core import Data
from glue.core.state_objects import State
from glue.viewers.common.viewer import Viewer
from glue_jupyter import JupyterApplication
from glue_jupyter.ipyvolume.scatter import IpyvolumeScatterView
from glue_qt.app import GlueApplication
from glue_vispy_viewers.scatter.qt.scatter_viewer import VispyScatterViewer
from pxr import Sdf, Usd
import pytest

from glue_ar.common.export import export_viewer
from glue_ar.common.scatter import IPYVOLUME_POINTS_GETTERS, radius_for_scatter_layer
from glue_ar.common.scatter_export_options import ARIpyvolumeScatterExportOptions, ARVispyScatterExportOptions
from glue_ar.common.shapes import sphere_points, sphere_points_count, sphere_triangles_count
from glue_ar.usd_utils import material_for_mesh
from glue_ar.utils import export_label_for_layer, hex_to_components, iterator_count, layers_to_export, xyz_bounds


@pytest.mark.parametrize("app_type,viewer_type", (("qt", "vispy"), ("jupyter", "vispy"), ("jupyter", "ipyvolume")))
class TestVispyScatterUSD:

    @pytest.fixture(scope='function', autouse=True)
    def setup_method(self, app_type: str, viewer_type: str):

        # Setup
        seed(186)
        self.n = 40
        x1 = [random() * 5 for _ in range(self.n)]
        y1 = [random() for _ in range(self.n)]
        z1 = [randint(1, 30) for _ in range(self.n)]
        self.data1 = Data(x=x1, y=y1, z=z1, label="Scatter Data 1")
        self.data1.style.color = "#fedcba"
        self.app = self._create_application(app_type)
        self.app.data_collection.append(self.data1)
        self.viewer: Viewer = self.app.new_data_viewer(self._viewer_class(viewer_type))
        self.viewer.add_data(self.data1)

        x2 = [random() * 7 for _ in range(self.n)]
        y2 = [randint(100, 200) for _ in range(self.n)]
        z2 = [random() for _ in range(self.n)]
        self.data2 = Data(x=x2, y=y2, z=z2, label="Scatter Data 2")

        self.viewer.state.x_att = self.data1.id['x']
        self.viewer.state.y_att = self.data1.id['y']
        self.viewer.state.z_att = self.data1.id['z']
        self.state_dictionary = self._basic_state_dictionary(viewer_type)

        yield

        # Teardown
        if getattr(self, "tmpfile", None) is not None:
            self.tmpfile.close()
            remove(self.tmpfile.name)
        if hasattr(self.viewer, "close"):
            self.viewer.close(warn=False)
        self.viewer = None
        if hasattr(self.app, 'close'):
            self.app.close()
        self.app = None

    def _create_application(self, app_type: str) -> Union[GlueApplication, JupyterApplication]:
        if app_type == "qt":
            return GlueApplication()
        elif app_type == "jupyter":
            return JupyterApplication()
        else:
            raise ValueError("Application type should be either qt or jupyter")

    def _viewer_class(self, viewer_type: str) -> Union[Type[VispyScatterViewer], Type[IpyvolumeScatterView]]:
        if viewer_type == "vispy":
            return VispyScatterViewer
        elif viewer_type == "ipyvolume":
            return IpyvolumeScatterView
        else:
            raise ValueError("Viewer type should be either vispy or ipyvolume")

    def _basic_state_dictionary(self, viewer_type: str) -> Dict[str, Tuple[str, State]]:
        if viewer_type == "vispy":
            state_maker = lambda: ARVispyScatterExportOptions(theta_resolution=15,
                                                              phi_resolution=15)
        elif viewer_type == "ipyvolume":
            state_maker = ARIpyvolumeScatterExportOptions
        else:
            raise ValueError("Viewer type should be either vispy or ipyvolume")

        return {
            export_label_for_layer(layer): ("Scatter", state_maker())
            for layer in self.viewer.layers
        }

    def test_basic_export(self):
        bounds = xyz_bounds(self.viewer.state, with_resolution=False)
        self.tmpfile = NamedTemporaryFile(suffix=".usdc", delete=False)
        self.tmpfile.close()
        layer_states = [layer.state for layer in layers_to_export(self.viewer)]
        export_viewer(self.viewer.state,
                      layer_states=layer_states,
                      bounds=bounds,
                      state_dictionary=self.state_dictionary,
                      filepath=self.tmpfile.name,
                      compression=None)

        stage = Usd.Stage.Open(self.tmpfile.name)
        world = stage.GetDefaultPrim()
        assert str(world.GetPath()) == "/world"

        layer = self.viewer.layers[0]
        label = export_label_for_layer(layer.state)
        identifier = label.replace(" ", "_")
        _, options = self.state_dictionary[label]

        # The default ipyvolume geometry type is diamond
        theta_resolution: int = getattr(options, "theta_resolution", 3)
        phi_resolution: int = getattr(options, "phi_resolution", 3)
        sphere_pts_count = sphere_points_count(theta_resolution=theta_resolution, phi_resolution=phi_resolution)
        sphere_tris_count = sphere_triangles_count(theta_resolution=theta_resolution, phi_resolution=phi_resolution)
        expected_vert_cts = [3] * sphere_tris_count

        color_precision = 5
        color_components = [round(c / 255, color_precision) for c in hex_to_components(layer.state.color)]

        # There should be 2n + 4 total prims:
        # The xform and the mesh for each point -> 2 * n
        # The top-level world prim
        # The light
        # The material
        # The PBR shader
        assert iterator_count(stage.TraverseAll()) == 2 * self.n + 4

        original_point_mesh = None
        for i in range(self.n):
            point_mesh = stage.GetPrimAtPath(f"/world/xform_{identifier}_{i}/mesh_{identifier}_{i}")
            assert point_mesh is not None
            points = list(point_mesh.GetAttribute("points").Get())
            assert len(points) == sphere_pts_count
            vertex_counts = list(point_mesh.GetAttribute("faceVertexCounts").Get())
            assert vertex_counts == expected_vert_cts
            vertex_indices = list(point_mesh.GetAttribute("faceVertexIndices").Get())
            assert len(vertex_indices) == sphere_tris_count * 3

            material = material_for_mesh(point_mesh)
            pbr_shader = stage.GetPrimAtPath(f"{material.GetPath()}/PBRShader")
            assert pbr_shader.GetAttribute("inputs:metallic").Get() == 0.0
            assert pbr_shader.GetAttribute("inputs:roughness").Get() == 1.0
            assert round(pbr_shader.GetAttribute("inputs:opacity").Get(), color_precision) == \
                   round(layer.state.alpha, color_precision)
            assert [round(c, color_precision) for c in pbr_shader.GetAttribute("inputs:diffuseColor").Get()] == \
                   color_components

            if i == 0:
                original_point_mesh = point_mesh
            else:
                stack_top = point_mesh.GetPrimStack()[0]
                assert stack_top.referenceList.prependedItems[0] == \
                       Sdf.Reference(primPath=original_point_mesh.GetPath())
