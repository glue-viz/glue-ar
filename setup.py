from os.path import join
from setupbase import (
    create_cmdclass,
    install_npm,
    ensure_targets,
    find_packages,
    combine_commands,
    get_version,
    HERE,
)

from setuptools import setup

js_content_command = combine_commands(
    install_npm(join("js", "gltf-pipeline")),
)

setup()
