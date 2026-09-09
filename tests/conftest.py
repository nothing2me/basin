import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from basin_core.data import CachedSource
from basin_core.engine import ScenarioParams
from basin_core.workspace import SESSION_DIR_ENV, Workspace, session_dir


@pytest.fixture(autouse=True)
def isolated_sessions(tmp_path_factory, monkeypatch):
    """Point saved-analysis storage at a throwaway directory for every test.

    Nothing in the suite may read or modify the real ``local/`` sessions, which hold a
    developer's private work and are absent from a clean checkout.
    """
    directory = tmp_path_factory.mktemp("basin-sessions")
    monkeypatch.setenv(SESSION_DIR_ENV, str(directory))
    return directory


@pytest.fixture(scope="session")
def source():
    return CachedSource()


@pytest.fixture
def workspace(source):
    return Workspace(source, ScenarioParams(tuple(source.daily.columns), candidates=30), size=3)
