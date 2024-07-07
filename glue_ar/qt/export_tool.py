from os.path import splitext

from qtpy import compat
from qtpy.QtWidgets import QDialog

from glue.config import viewer_tool
from glue.viewers.common.tool import SimpleToolMenu, Tool
from glue_qt.utils.threading import Worker

from glue_ar.utils import AR_ICON
from glue_ar.common.export import export_to_ar
from glue_ar.qt.export_dialog import ARExportDialog
from glue_ar.qt.exporting_dialog import ExportingDialog


__all__ = ["ARToolMenu", "QtARExportTool"]

_FILETYPE_NAMES = {
    ".obj": "OBJ",
    ".gltf": "glTF",
    ".glb": "glB"
}


@viewer_tool
class ARToolMenu(SimpleToolMenu):
    tool_id = "ar"
    icon = AR_ICON
    tool_tip = "AR utilities"


@viewer_tool
class QtARExportTool(Tool):
    icon = AR_ICON
    tool_id = "save:ar"
    action_text = "Export 3D file"
    tool_tip = "Export the current view to a 3D file"

    _default_filename = "glue_export"

    def activate(self):

        dialog = ARExportDialog(parent=self.viewer, viewer=self.viewer)
        result = dialog.exec_()
        if result == QDialog.Rejected:
            return

        export_path, _ = compat.getsavefilename(parent=self.viewer,
                                                basedir=f"{self._default_filename}.{dialog.state.filetype.lower()}")
        if not export_path:
            return

        _, ext = splitext(export_path)
        filetype = _FILETYPE_NAMES.get(ext, None)
        worker = Worker(export_to_ar, self.viewer, export_path, dialog.state_dictionary,
                        compression=dialog.state.compression.lower())
        exporting_dialog = ExportingDialog(parent=self.viewer, filetype=filetype)
        worker.result.connect(exporting_dialog.close)
        worker.error.connect(exporting_dialog.close)
        worker.start()
        exporting_dialog.exec_()
