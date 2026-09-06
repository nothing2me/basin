import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from basin_core.data import CachedSource
from basin_core.engine import ScenarioParams
from basin_core.workspace import Workspace


@pytest.fixture(scope="session")
def source():
    return CachedSource()


@pytest.fixture
def workspace(source):
    return Workspace(source, ScenarioParams(tuple(source.daily.columns), candidates=30), size=3)
