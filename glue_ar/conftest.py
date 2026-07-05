import pytest

from glue.core import Data
import numpy as np


def pytest_configure(config):
    from glue_ar import setup
    setup()


@pytest.fixture
def data_3d():
    x = np.arange(24).reshape((2, 3, 4))
    return Data(label="Data", x=x)


@pytest.fixture
def data2_3d():
    x = np.arange(36).reshape((3, 4, 3))
    return Data(label="Data", x=x)
