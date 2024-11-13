from ..registries import BuilderRegistry, CompressorRegistry


def test_builder_registry():

    builder_registry = BuilderRegistry()

    @builder_registry("ext")
    class ExtBuilder:
        pass

    @builder_registry(("ext1", "ext2"))
    class ExtsBuilder:
        pass

    assert builder_registry.members == {"ext": ExtBuilder,
                                        "ext1": ExtsBuilder,
                                        "ext2": ExtsBuilder}


def test_compressor_registry():

    compressor_registry = CompressorRegistry()

    @compressor_registry("dummy")
    def dummy_compressor(_filepath: str):
        pass

    assert compressor_registry.members == {"dummy": dummy_compressor}
