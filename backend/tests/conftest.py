import os
import tempfile

_tmp = tempfile.mkdtemp(prefix="qgreen_test_")
os.environ["DATA_DIR"] = _tmp
os.environ["DATABASE_URL"] = f"sqlite:///{_tmp}/test.db"  # must be set before app.config is imported

import pytest  # noqa: E402

from app.simulation.demo_data import build_demo_scenario  # noqa: E402


@pytest.fixture(scope="session")
def doc():
    return build_demo_scenario()
