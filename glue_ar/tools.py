import os

import pyvista as pv

from glue.config import viewer_tool
from glue.viewers.common.tool import Tool

from glue_ar.common import create_plotter
from glue_ar.scatter import scatter_layer_as_multiblock
from glue_ar.export import export_gl, export_modelviewer
from glue_ar.volume import create_meshes

__all__ = ["GLScatterExportTool", "GLVolumeExportTool"]

# This is just some placeholder image that I found online
AR_ICON = os.path.abspath(os.path.join(os.path.dirname(__file__), "ar"))


# No UI for now - that's easy to add once implementations are complete
# For now, this just exports to "test.gltf" and "test.html"
@viewer_tool
class GLScatterExportTool(Tool):
    icon = AR_ICON
    tool_id = "ar:scatter-gl"
    action_text = "Export to gl"
    tool_tip = "Export the current view to a glB file"

    def activate(self):
        plotter = create_plotter(pv.Plotter.add_mesh, scatter_layer_as_multiblock, self.viewer.state)
        
        # output_filename = "test.obj"
        # plotter.export_obj(output_filename)

        output_filename = "test.glb"
        export_gl(plotter, output_filename, with_alpha=True)
        
        export_modelviewer("test.html", output_filename, "Testing visualization")


@viewer_tool
class GLVolumeExportTool(Tool):
    icon = AR_ICON
    tool_id = "ar:volume-gl"
    action_text = "Export to gl"
    tool_tip = "Export the current view to a glB file"

    def activate(self):
        plotter = pv.Plotter()
        meshes = create_meshes(self.viewer.state, use_gaussian_filter=True, smoothing_iteration_count=5)
        for data in meshes.values():
            mesh = data.pop("mesh")
            plotter.add_mesh(mesh, color=data["color"], opacity=data["opacity"])
        plotter.export_obj("volume.obj")
        export_gl(plotter, "volume.gltf", with_alpha=True)  # Do we want alpha for volume renderings?
        export_modelviewer("volume.html", "volume.gltf", "Testing visualization")
