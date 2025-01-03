from os.path import join
from subprocess import run

from glue_ar.registries import compressor
from glue_ar.utils import PACKAGE_DIR


NODE_MODULES_DIR = join(PACKAGE_DIR, "js", "node_modules")
GLTF_TRANSFORM_FILEPATH = join(NODE_MODULES_DIR, "@gltf-transform", "cli", "bin", "cli.js")


@compressor("draco")
def compress_draco(filepath: str):
    run([GLTF_TRANSFORM_FILEPATH, "optimize", filepath, filepath, "--compress", "draco"], capture_output=True)


@compressor("meshoptimizer")
def compress_meshoptimizer(filepath: str):
    run([GLTF_TRANSFORM_FILEPATH, "optimize", filepath, filepath], capture_output=True)
