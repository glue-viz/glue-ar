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

name = "glue_ar"

js_content_command = combine_commands(
    install_npm("js", build_cmd="glue-ar-export")
)

# Custom "command class" that (1) makes sure to create the JS content, (2)
# includes that content as extra "package data" in the Python package, and (3)
# can install special metadata files in the Python environment root.
package_data_spec = {
    name: [
        "js/**/*",
    ]
}

cmdclass = create_cmdclass(
    "js-content", package_data_spec=package_data_spec,
)
cmdclass["js-content"] = js_content_command

# TODO: Add the rest of the package data
setup_args = dict(
    name=name,
    cmdclass=cmdclass,
    include_package_data=True,
    entry_points={}
)

if __name__ == "__main__":
    setup(**setup_args)
