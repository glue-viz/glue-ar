import ngrok
import os
from os.path import split
from tempfile import NamedTemporaryFile
from threading import Thread
from typing import Type

from glue.config import viewer_tool
from glue.core.state_objects import State
from glue.viewers.common.state import LayerState
from glue.viewers.common.tool import Tool
from glue_vispy_viewers.scatter.layer_artist import ScatterLayerState
from glue_vispy_viewers.volume.volume_viewer import VispyVolumeViewerMixin

from glue_ar.utils import AR_ICON, export_label_for_layer, xyz_bounds
from glue_ar.common.export import export_modelviewer, export_viewer
from glue_ar.common.scatter_export_options import ARVispyScatterExportOptions
from glue_ar.common.volume_export_options import ARIsosurfaceExportOptions
from glue_ar.qt.qr import get_local_ip
from glue_ar.qt.qr_dialog import QRDialog
from glue_ar.qt.server import run_ar_server


__all__ = ["ARLocalQRTool"]


@viewer_tool
class ARLocalQRTool(Tool):
    icon = AR_ICON
    tool_id = "ar:qr"
    action_text = "3D view via QR"
    tool_tip = "Get a QR code for the current view in 3D"

    def _export_items_for_layer(self, layer: LayerState) -> Type[State]:
        if isinstance(layer, ScatterLayerState):
            return ("Scatter", ARVispyScatterExportOptions())
        else:
            return ("Isosurface", ARIsosurfaceExportOptions(isosurface_count=8))

    def activate(self):
        layer_states = [layer.state for layer in self.viewer.layers
                        if layer.enabled and layer.state.visible]
        bounds = xyz_bounds(self.viewer.state, with_resolution=isinstance(self.viewer, VispyVolumeViewerMixin))
        state_dictionary = {
            export_label_for_layer(state): self._export_items_for_layer(state)
            for state in layer_states
        }
        with NamedTemporaryFile(suffix=".gltf") as gltf_tmp, \
             NamedTemporaryFile(suffix=".html") as html_tmp:

            _, gltf_base = split(gltf_tmp.name)
            export_viewer(self.viewer.state, layer_states, bounds, state_dictionary, gltf_tmp.name)
            export_modelviewer(html_tmp.name, gltf_base, self.viewer.state.title)

            port = 4000
            directory, filename = split(html_tmp.name)
            server = run_ar_server(port, directory)
            use_ngrok = os.getenv("NGROK_AUTHTOKEN", None) is not None

            try:
                thread = Thread(target=server.serve_forever)
                thread.start()

                if use_ngrok:
                    listener = ngrok.forward(port, authtoken_from_env=True)
                    url = f"{listener.url()}/{filename}"
                else:
                    ip = get_local_ip()
                    url = f"http://{ip}:{port}/{filename}"
                dialog = QRDialog(parent=self.viewer, url=url)
                dialog.exec_()

            finally:
                if use_ngrok:
                    try:
                        ngrok.disconnect(listener.url())
                    except RuntimeError:
                        pass
                server.shutdown()
                server.server_close()
