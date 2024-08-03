from glue.config import DictRegistry
from glue.core.state_objects import State
from glue_vispy_viewers.common.layer_state import VispyLayerState

from typing import Callable, List, Optional, Tuple, Type


__all__ = ["ar_layer_export"]


class ARExportSpecification:

    def __init__(self,
                 export_method: Callable,
                 layer_options_state: Type[State],
                 multiple: bool = False):
        self.export_method = export_method
        self.layer_options_state = layer_options_state
        self.multiple = multiple


class ARExportLayerOptionsRegistry(DictRegistry):

    def __init__(self):
        super().__init__()
        self.method_state_types = {}

    def add(self,
            layer_state_cls: Type[VispyLayerState],
            name: str,
            layer_options_state: Type[State],
            extensions: List[str],
            multiple: bool,
            export_method: Callable):
        if not issubclass(layer_options_state, State):
            raise ValueError("Layer options must be a glue State type")

        self.method_state_types[(layer_state_cls, name)] = layer_options_state

        spec = ARExportSpecification(export_method, layer_options_state, multiple)
        for extension in extensions:
            key = (layer_state_cls, name, extension)
            self._members[key] = spec

    def export_state_classes(self, layer_state_cls) -> List[Tuple[Type[State], str]]:
        return [(name, export_state_cls) for (state_cls, name), export_state_cls in
                self.method_state_types.items() if layer_state_cls == state_cls]

    def options_class(self, state_cls, name) -> Optional[Type[State]]:
        return self.method_state_types.get((state_cls, name), None)

    def export_spec(self, state_cls, name, extension) -> ARExportSpecification:
        return self._members[(state_cls, name, extension)]

    def method_names(self, layer_state_cls, extension) -> List[str]:
        extension = extension.lower()
        return [name for (state_cls, name, ext) in self._members.keys()
                if state_cls == layer_state_cls and ext == extension]


    def __call__(self,
                 layer_state_cls: Type[VispyLayerState],
                 name: str,
                 layer_options_state: Type[State],
                 extensions: List[str],
                 multiple: bool = False):
        def adder(export_method: Callable):
            self.add(layer_state_cls, name, layer_options_state, extensions, multiple, export_method)
        return adder


ar_layer_export = ARExportLayerOptionsRegistry()
