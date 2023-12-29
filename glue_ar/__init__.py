from glue_ar.export_scatter import *
from glue_ar.export_volume import *
from glue_ar.tools import *

def setup():
    from glue_qt.config import qt_client
    
    from glue_vispy_viewers.scatter.scatter_viewer import VispyScatterViewer
    VispyScatterViewer.tools += ["ar"]
    VispyScatterViewer.subtools["ar"] = ["ar:export", "ar:qr"]

    from glue_vispy_viewers.volume.volume_viewer import VispyVolumeViewer
    VispyVolumeViewer.tools += ["ar"]
    VispyVolumeViewer.subtools["ar"] = ["ar:export", "ar:qr"]
