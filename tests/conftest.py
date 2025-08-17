import os
import tempfile

import pytest


@pytest.fixture(scope="session", autouse=True)
def set_env():
    os.environ["ZCOMPY_FUNC_SAVE_PATH"] = tempfile.gettempdir()
