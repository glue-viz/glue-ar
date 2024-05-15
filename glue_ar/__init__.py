from glue_ar.export_scatter import *  # noqa
from glue_ar.export_volume import *  # noqa
from glue_ar.tools import *  # noqa


def setup():

    from glue_vispy_viewers.scatter.scatter_viewer import VispyScatterViewer
    VispyScatterViewer.tools += ["ar"]
    VispyScatterViewer.subtools = {
        **VispyScatterViewer.subtools,
        "save": VispyScatterViewer.subtools["save"] + ["save:ar"]
    }
    VispyScatterViewer.subtools["ar"] = ["ar:qr"]

    from glue_vispy_viewers.volume.volume_viewer import VispyVolumeViewer
    VispyVolumeViewer.tools += ["ar"]
    VispyVolumeViewer.subtools = {
        **VispyVolumeViewer.subtools,
        "save": VispyVolumeViewer.subtools["save"] + ["save:ar"]
    }
    VispyVolumeViewer.subtools["ar"] = ["ar:qr"]
