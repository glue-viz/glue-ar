from os.path import join
from subprocess import run

from glue_ar.registries import compressor
from glue_ar.utils import PACKAGE_DIR


NODE_MODULES_DIR = join(PACKAGE_DIR, "js", "node_modules")
GLTF_PIPELINE_FILEPATH = join(NODE_MODULES_DIR, "gltf-pipeline", "bin", "gltf-pipeline.js")
GLTFPACK_FILEPATH = join(NODE_MODULES_DIR, "gltfpack", "cli.js")


@compressor("draco")
def compress_gltf_pipeline(filepath: str):
    run(["node", GLTF_PIPELINE_FILEPATH, "-i", filepath, "-o", filepath, "-d"], capture_output=True)


@compressor("meshoptimizer")
def compress_gltfpack(filepath: str):
    run(["node", GLTFPACK_FILEPATH, "-i", filepath, "-o", filepath], capture_output=True)
