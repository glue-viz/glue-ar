import os
from os.path import join, split, splitext
from glue_vispy_viewers.volume.layer_state import VolumeLayerState

import pyvista as pv

from qtpy import compat
from qtpy.QtWidgets import QDialog

from glue.config import viewer_tool
from glue.viewers.common.tool import Tool
from glue_ar.export_dialog import ARExportDialog

from glue_ar.scatter import scatter_layer_as_multiblock
from glue_ar.export import export_gl, export_modelviewer
from glue_ar.utils import bounds_3d_from_layers
from glue_ar.volume import bounds_3d, meshes_for_volume_layer

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
        
        dialog = ARExportDialog(parent=self.viewer, viewer_state=self.viewer.state)
        result = dialog.exec_()
        if result == QDialog.Rejected:
            return

        export_path, _ = compat.getsavefilename(parent=self.viewer, basedir=f"scatter.{dialog.state.filetype.lower()}")
        if not export_path:
            return

        plotter = pv.Plotter()
        layer_states = [layer.state for layer in self.viewer.layers if layer.enabled and layer.state.visible]
        for layer_state in layer_states:
            layer_info = dialog.state_dictionary[layer_state.layer.label].as_dict()
            mesh_info = scatter_layer_as_multiblock(self.viewer.state, layer_state,
                                                    scaled=True,
                                                    clip_to_bounds=self.viewer.state.clip_data,
                                                    **layer_info)
            mesh = mesh_info.pop("mesh")
            if len(mesh.points) > 0:
                plotter.add_mesh(mesh, **mesh_info)

        dir, base = split(export_path)
        name, ext = splitext(base)
        html_path = join(dir, f"{name}.html")
        if ext == '.gltf':
            export_gl(plotter, export_path, with_alpha=True)
            export_modelviewer(html_path, base, "Testing visualization")
        else:
            plotter.export_obj(export_path)


@viewer_tool
class GLVolumeExportTool(Tool):
    icon = AR_ICON
    tool_id = "ar:volume-gl"
    action_text = "Export to gl"
    tool_tip = "Export the current view to a glB file"

    def activate(self):

        dialog = ARExportDialog(parent=self.viewer, viewer_state=self.viewer.state)
        result = dialog.exec_()
        if result == QDialog.Rejected:
            return

        export_path, _ = compat.getsavefilename(parent=self.viewer, basedir=f"volume.{dialog.state.filetype.lower()}")
        if not export_path:
            return

        plotter = pv.Plotter()
        layer_states = [layer.state for layer in self.viewer.layers if layer.enabled and layer.state.visible]
        frbs = {}
        if self.viewer.state.clip_data:
            bounds = bounds_3d(self.viewer.state) 
        else:
            bounds = bounds_3d_from_layers(self.viewer.state, layer_states)
        for layer_state in layer_states:
            layer_info = dialog.state_dictionary[layer_state.layer.label].as_dict()
            if isinstance(layer_state, VolumeLayerState):
                mesh_info = meshes_for_volume_layer(self.viewer.state, layer_state,
                                                    bounds=bounds,
                                                    precomputed_frbs=frbs,
                                                    **layer_info)
            else:
                mesh_info = scatter_layer_as_multiblock(self.viewer.state, layer_state,
                                                        scaled=False,
                                                        clip_to_bounds=self.viewer.state.clip_data,
                                                        **layer_info)
            mesh = mesh_info.pop("mesh")
            if len(mesh.points) > 0:
                plotter.add_mesh(mesh, **mesh_info)

        dir, base = split(export_path)
        name, ext = splitext(base)
        html_path = join(dir, f"{name}.html")
        if ext == '.gltf':
            export_gl(plotter, export_path, with_alpha=True)  # Do we want alpha for volume renderings?
            export_modelviewer(html_path, base, "Testing visualization")
        else:
            plotter.export_obj(export_path)
