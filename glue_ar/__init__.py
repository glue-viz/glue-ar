from glue_ar.tools import *

def setup():
    from glue_qt.config import qt_client
    
    from glue_vispy_viewers.scatter.scatter_viewer import VispyScatterViewer
    VispyScatterViewer.tools += ["ar:gltf"]
