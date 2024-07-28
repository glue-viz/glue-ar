from echo import SelectionCallbackProperty
from glue.config import DictRegistry
from glue.core.data_combo_helper import ComboHelper
from glue.core.state_objects import State


__all__ = ['ar_layer_export']


class ARExportLayerOptionsRegistry(DictRegistry):

    def add(self, layer_state_cls, name, layer_options_state):
        if not issubclass(layer_options_state, State):
            raise ValueError("Layer options must be a glue State type")
        if layer_state_cls in self._members:
            self._members[layer_state_cls].update({ name: layer_options_state })
        else:
            self._members[layer_state_cls] = { name: layer_options_state }

    def __call__(self, layer_state_cls, name):
        def adder(export_state_class):
            self.add(layer_state_cls, name, export_state_class)
        return adder


ar_layer_export = ARExportLayerOptionsRegistry()


class ARExportDialogState(State):

    filetype = SelectionCallbackProperty()
    layer = SelectionCallbackProperty()
    compression = SelectionCallbackProperty()
    method = SelectionCallbackProperty()

    def __init__(self, layers):

        super(ARExportDialogState, self).__init__()

        self.filetype_helper = ComboHelper(self, 'filetype')
        self.filetype_helper.choices = ['glTF', 'glB', 'USDA', 'USDC']

        self.compression_helper = ComboHelper(self, 'compression')
        self.compression_helper.choices = ['None', 'Draco', 'Meshoptimizer']

        self.method_helper = ComboHelper(self, 'method')

        self.layers = layers
        self.layer_helper = ComboHelper(self, 'layer')
        self.layer_helper.choices = [state.layer.label for state in self.layers]
