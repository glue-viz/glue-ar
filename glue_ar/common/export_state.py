from echo import SelectionCallbackProperty
from glue.core.data_combo_helper import ComboHelper
from glue.core.state_objects import State


__all__ = ["ARExportDialogState"]


class ARExportDialogState(State):

    filetype = SelectionCallbackProperty()
    layer = SelectionCallbackProperty()
    compression = SelectionCallbackProperty()
    method = SelectionCallbackProperty()

    def __init__(self, layers):

        super(ARExportDialogState, self).__init__()

        self.filetype_helper = ComboHelper(self, 'filetype')
        self.filetype_helper.choices = ['glB', 'glTF', 'USDC', 'USDA']

        self.compression_helper = ComboHelper(self, 'compression')
        self.compression_helper.choices = ['None', 'Draco', 'Meshoptimizer']

        self.method_helper = ComboHelper(self, 'method')

        self.layers = layers
        self.layer_helper = ComboHelper(self, 'layer')
        self.layer_helper.choices = [state.layer.label for state in self.layers]
