from collections.abc import Callable, Iterable
from typing import Protocol, TypeVar

from glue.config import DictRegistry

__all__ = ["Builder", "builder", "compressor"]


T = TypeVar("T", covariant=True)
class Builder(Protocol[T]):
    def build(self) -> T:
        ...

    def build_and_export(self, filepath: str):
        ...



class BuilderRegistry(DictRegistry):

    def add(self, extensions: str | Iterable[str], builder: type):
        if isinstance(extensions, str):
            self._members[extensions] = builder
        else:
            for ext in extensions:
                self._members[ext] = builder

    def __call__(self, extensions: str | Iterable[str]):
        def adder(builder: type):
            self.add(extensions, builder)
            return builder
        return adder


builder = BuilderRegistry()


B = TypeVar('B', bound=Builder)
class CompressorRegistry(DictRegistry):

    def add(self, name: str, compressor: Callable[[B], B]):
        self._members[name] = compressor

    def __call__(self, name: str):
        def adder(compressor: Callable[[B], B]):
            self.add(name, compressor)
            return compressor
        return adder


compressor = CompressorRegistry()
