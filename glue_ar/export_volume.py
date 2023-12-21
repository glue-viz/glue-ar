import os
import typing
from PyQt6 import QtCore
from PyQt6.QtWidgets import QWidget
from echo import CallbackProperty, SelectionCallbackProperty
from echo.qt import autoconnect_callbacks_to_qt

from qtpy.QtWidgets import QDialog, QListWidgetItem

from glue.core.state_objects import State 
from glue.core.data_combo_helper import ComboHelper
from glue_qt.utils import load_ui

__all__ = ["ExportVolumeDialog"]

# Note that this class only holds the state that is
# currently displayed in the dialog. In particular,
# this means that `gaussian_filter` and `smoothing_iterations`
# represent the values for `layer`
class ExportVolumeDialogState(State):

    filetype = SelectionCallbackProperty()
    layer = SelectionCallbackProperty()
    use_gaussian_filter = CallbackProperty()
    smoothing_iterations = CallbackProperty()

    def __init__(self, viewer_state):
        super(ExportVolumeDialogState, self).__init__()

        self.filetype_helper = ComboHelper(self, 'filetype')
        self.filetype_helper.choices = ['glTF', 'OBJ']

        self.layers = [state for state in viewer_state.layers if state.visible]
        self.layer_helper = ComboHelper(self, 'layer')
        self.layer_helper.choices = [state.layer.label for state in self.layers]


class ExportVolumeDialog(QDialog):
    
    def __init__(self, parent=None, viewer_state=None):

        super(ExportVolumeDialog, self).__init__(parent=parent)

        self.viewer_state = viewer_state
        self.state = ExportVolumeDialogState(self.viewer_state)
        self.ui = load_ui('export_volume.ui', self, directory=os.path.dirname(__file__))

        layers = [state for state in self.viewer_state.layers if state.visible]
        self.info_dictionary = {
            layer.layer.label: {
                "use_gaussian_filter": False,
                "smoothing_iterations": 0
            } for layer in layers
        }

        for layer in layers:
            item = QListWidgetItem(layer.layer.label)
            self.ui.listsel_layer.addItem(item)

        self._connections = autoconnect_callbacks_to_qt(self.state, self.ui)

        self.ui.button_cancel.clicked.connect(self.reject)
        self.ui.button_ok.clicked.connect(self.accept)

        self.state.add_callback('use_gaussian_filter', self._on_gaussian_filter_change)
        self.state.add_callback('smoothing_iterations', self._on_smoothing_iterations_change)
        self.state.add_callback('layer', self._on_layer_change)

    def _on_gaussian_filter_change(self, filter):
        self.info_dictionary[self.state.layer]["use_gaussian_filter"] = filter

    def _on_smoothing_iterations_change(self, iterations):
        self.info_dictionary[self.state.layer]["smoothing_iterations"] = int(iterations)

    def _on_layer_change(self, layer):
        self.state.use_gaussian_filter = self.info_dictionary[layer]["use_gaussian_filter"]
        self.state.smoothing_iterations = self.info_dictionary[layer]["smoothing_iterations"]
