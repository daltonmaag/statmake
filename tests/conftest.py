from pathlib import Path

import pytest


@pytest.fixture
def datadir() -> Path:
    return Path(__file__).parent / "data"
