import ngrok
import os
from os.path import split
from tempfile import NamedTemporaryFile
from threading import Thread

from glue.config import viewer_tool
from glue.viewers.common.tool import Tool

from glue_ar.utils import AR_ICON
from glue_ar.common.export import create_plotter, export_gl, export_modelviewer
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

    def activate(self):
        with NamedTemporaryFile(suffix=".gltf") as gltf_tmp, \
             NamedTemporaryFile(suffix=".html") as html_tmp:

            plotter = create_plotter(self.viewer, {})
            export_gl(plotter, gltf_tmp.name, with_alpha=True)
            _, gltf_base = split(gltf_tmp.name)
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
