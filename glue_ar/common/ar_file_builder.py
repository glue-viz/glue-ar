from typing import Iterable, Tuple


class ARFileBuilder:

    def add_mesh(self,
                 points: Iterable[Iterable[float]],
                 triangles: Iterable[Iterable[int]],
                 color: Tuple[int, int, int],
                 opacity: float,
                 metallic: float = 0.0,
                 roughness: float = 1.0,
                 **kwargs):
        raise NotImplementedError()

    def build_and_export(self, filepath: str):
        raise NotImplementedError()
