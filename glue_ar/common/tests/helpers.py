from itertools import product


def package_installed(package):
    from importlib.util import find_spec
    return find_spec(package) is not None


APP_TYPES = []
VIEWER_TYPES = ["vispy"]
if package_installed("glue_qt"):
    APP_TYPES.append("qt")
if package_installed("glue_jupyter"):
    APP_TYPES.append("jupyter")
    VIEWER_TYPES.append("ipyvolume")


APP_VIEWER_OPTIONS = list(product(APP_TYPES, VIEWER_TYPES))
qt_ipyvolume = ("qt", "ipyvolume")
if qt_ipyvolume in APP_VIEWER_OPTIONS:
    APP_VIEWER_OPTIONS.remove(qt_ipyvolume)
