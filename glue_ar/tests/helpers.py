def package_installed(package):
    from importlib.util import find_spec
    return find_spec(package) is not None


GLUE_QT_INSTALLED = package_installed("glue_qt")
GLUE_JUPYTER_INSTALLED = package_installed("glue_jupyter")
DRACOPY_INSTALLED = package_installed("DracoPy")
