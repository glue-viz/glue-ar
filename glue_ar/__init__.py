from glue_ar.common.scatter_export_options import *  # noqa
from glue_ar.common.volume_export_options import *  # noqa


def setup_qt():
    try:
        from glue_vispy_viewers.scatter.qt.scatter_viewer import VispyScatterViewer
    except ImportError:
        from glue_vispy_viewers.scatter.scatter_viewer import VispyScatterViewer

    from glue_ar.qt.export_tool import QtARExportTool  # noqa

    VispyScatterViewer.subtools = {
        **VispyScatterViewer.subtools,
        "save": VispyScatterViewer.subtools["save"] + ["save:ar"]
    }

    try:
        from glue_vispy_viewers.volume.qt.volume_viewer import VispyVolumeViewer
    except ImportError:
        from glue_vispy_viewers.volume.volume_viewer import VispyVolumeViewer
    VispyVolumeViewer.subtools = {
        **VispyVolumeViewer.subtools,
        "save": VispyVolumeViewer.subtools["save"] + ["save:ar"]
    }

    try:
        from glue_ar.qt.qr_tool import ARLocalQRTool  # noqa
        VispyScatterViewer.tools = [t for t in VispyScatterViewer.tools] + ["ar"]
        VispyVolumeViewer.tools = [t for t in VispyVolumeViewer.tools] + ["ar"]
        VispyScatterViewer.subtools["ar"] = ["ar:qr"]
        VispyVolumeViewer.subtools["ar"] = ["ar:qr"]
    except ImportError:
        pass


def setup_jupyter():
    from glue_ar.jupyter.export_tool import JupyterARExportTool  # noqa
    from glue_vispy_viewers.scatter.jupyter import JupyterVispyScatterViewer
    from glue_vispy_viewers.volume.jupyter import JupyterVispyVolumeViewer
    JupyterVispyScatterViewer.tools = [t for t in JupyterVispyScatterViewer.tools] + ["save:ar_jupyter"]
    JupyterVispyVolumeViewer.tools = [t for t in JupyterVispyVolumeViewer.tools] + ["save:ar_jupyter"]


def setup():
    try:
        setup_qt()
    except ImportError as e:
        print("Qt setup error")
        print(e)
        pass

    try:
        setup_jupyter()
    except ImportError as e:
        print("Jupyter setup error")
        print(e)
        pass
