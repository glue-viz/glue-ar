from glue_ar.export_scatter import *  # noqa
from glue_ar.export_volume import *  # noqa
from glue_ar.tools import *  # noqa


def setup_qt():
    try:
        from glue_vispy_viewers.scatter.qt.scatter_viewer import VispyScatterViewer
    except ImportError:
        from glue_vispy_viewers.scatter.scatter_viewer import VispyScatterViewer
    VispyScatterViewer.tools = [t for t in VispyScatterViewer.tools] + ["ar"]
    VispyScatterViewer.subtools = {
        **VispyScatterViewer.subtools,
        "save": VispyScatterViewer.subtools["save"] + ["save:ar"]
    }
    VispyScatterViewer.subtools["ar"] = ["ar:qr"]

    try:
        from glue_vispy_viewers.volume.qt.volume_viewer import VispyVolumeViewer
    except ImportError:
        from glue_vispy_viewers.volume.volume_viewer import VispyVolumeViewer
    VispyVolumeViewer.tools = [t for t in VispyVolumeViewer.tools] + ["ar"]
    VispyVolumeViewer.subtools = {
        **VispyVolumeViewer.subtools,
        "save": VispyVolumeViewer.subtools["save"] + ["save:ar"]
    }
    VispyVolumeViewer.subtools["ar"] = ["ar:qr"]


def setup_jupyter():
    print("Setup jupyter")
    from glue_vispy_viewers.scatter.jupyter import JupyterVispyScatterViewer
    from glue_vispy_viewers.volume.jupyter import JupyterVispyVolumeViewer
    JupyterVispyScatterViewer.tools = [t for t in JupyterVispyScatterViewer.tools] + ["save:ar_jupyter"]
    JupyterVispyVolumeViewer.tools = [t for t in JupyterVispyVolumeViewer.tools] + ["save:ar_jupyter"]


def setup():
    try:
        setup_qt()
    except ImportError:
        pass

    try:
        setup_jupyter()
    except ImportError:
        pass
