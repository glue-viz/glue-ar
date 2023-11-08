import os

STL_ICON = os.path.abspath(os.path.join(os.path.dirname(__file__), 'stl.png'))


def setup():
    from glue_qt.config import qt_client

    # Append plugin to toolbar in all Vispy Volume Viewers
    from glue_vispy_viewers.volume.volume_viewer import VispyVolumeViewer
    VispyVolumeViewer.tools.append('glue_stl')
