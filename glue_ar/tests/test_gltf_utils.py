from ..gltf_utils import GLTFIndexExportOption, index_export_option


def test_index_export_option():
    assert index_export_option(3) == GLTFIndexExportOption.Byte
    assert index_export_option(100) == GLTFIndexExportOption.Byte
    assert index_export_option(255) == GLTFIndexExportOption.Byte
    assert index_export_option(256) == GLTFIndexExportOption.Short
    assert index_export_option(1234) == GLTFIndexExportOption.Short
    assert index_export_option(10_000) == GLTFIndexExportOption.Short
    assert index_export_option(65_535) == GLTFIndexExportOption.Short
    assert index_export_option(65_536) == GLTFIndexExportOption.Int
    assert index_export_option(100_000) == GLTFIndexExportOption.Int
    assert index_export_option(1_000_000) == GLTFIndexExportOption.Int
