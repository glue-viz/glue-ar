from glue.config import exporters
from importlib.util import find_spec


def package_installed(package: str) -> bool:
    return find_spec(package) is not None



