"""Performance benchmark harness measuring user-perceived latencies and rerun counts."""
import os
import socket
import time
from pathlib import Path
from types import SimpleNamespace

import pytest
from streamlit.testing.v1 import AppTest

from basin_core.engine import ScenarioParams
from basin_core.workspace import Workspace

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def offline_assistant(monkeypatch):
    def no_network(*args, **kwargs):
        raise AssertionError("Unexpected network call during UI test")

    monkeypatch.setattr(socket.socket, "connect", no_network)
    monkeypatch.setattr(socket, "create_connection", no_network)
    from basin_core import qwen_runtime
    offline_client = SimpleNamespace(status="model_missing")
    monkeypatch.setattr(qwen_runtime, "get_qwen_client", lambda: offline_client)


def test_navigation_latency_benchmarks(workspace, offline_assistant, monkeypatch, tmp_path):
    """Measure wall-clock latency for switching between pipeline stages."""
    monkeypatch.setattr(Workspace, "save", lambda self, *args, **kwargs: True)

    app = AppTest.from_file(str(ROOT / "app.py"), default_timeout=60)
    app.session_state.workspace = workspace
    app.session_state.data_accepted = True
    app.session_state.page = "Workspace"

    t0 = time.perf_counter()
    app.run()
    cold_load_ms = (time.perf_counter() - t0) * 1000
    assert not app.exception

    # Navigate to Review
    t0 = time.perf_counter()
    app.sidebar.radio[0].set_value("Review").run()
    nav_to_review_ms = (time.perf_counter() - t0) * 1000
    assert not app.exception
    assert app.session_state.page == "Review"

    # Navigate back to Workspace
    t0 = time.perf_counter()
    app.sidebar.radio[0].set_value("Workspace").run()
    nav_to_workspace_ms = (time.perf_counter() - t0) * 1000
    assert not app.exception
    assert app.session_state.page == "Workspace"

    # Warm navigation should be snappy
    assert nav_to_review_ms < 3000, f"Nav to review took {nav_to_review_ms:.1f}ms"
    assert nav_to_workspace_ms < 3000, f"Nav to workspace took {nav_to_workspace_ms:.1f}ms"


def test_notes_drawer_toggle_and_save(workspace, monkeypatch):
    """Verify Notes drawer toggles smoothly and stays open across edits and saves."""
    monkeypatch.setattr(Workspace, "save", lambda self, *args, **kwargs: True)

    app = AppTest.from_file(str(ROOT / "app.py"), default_timeout=60)
    app.session_state.workspace = workspace
    app.session_state.data_accepted = True
    app.session_state.page = "Workspace"
    app.run()
    assert not app.exception
    assert app.session_state.notes_open is False

    # 1. Open notes drawer
    t0 = time.perf_counter()
    app.button(key="btn_toggle_notes").click().run()
    open_ms = (time.perf_counter() - t0) * 1000
    assert not app.exception
    assert app.session_state.notes_open is True

    # 2. Save notes while open
    p_key = f"provider_{workspace.id}"
    app.text_area(key=p_key).set_value("Benchmark note").run()
    save_btn = next(b for b in app.button if b.key and b.key.startswith("btn_save_notes_"))
    t0 = time.perf_counter()
    save_btn.click().run()
    save_ms = (time.perf_counter() - t0) * 1000
    assert not app.exception
    assert app.session_state.notes_open is True
    assert workspace.notes == "Benchmark note"

    # 3. Close notes drawer
    t0 = time.perf_counter()
    app.button(key="btn_toggle_notes").click().run()
    close_ms = (time.perf_counter() - t0) * 1000
    assert not app.exception
    assert app.session_state.notes_open is False


def test_assistant_drawer_interactions(workspace, offline_assistant, monkeypatch):
    """Verify AI Assistant drawer toggling, chip queries, and chat operations."""
    monkeypatch.setattr(Workspace, "save", lambda self, *args, **kwargs: True)

    app = AppTest.from_file(str(ROOT / "app.py"), default_timeout=60)
    app.session_state.workspace = workspace
    app.session_state.data_accepted = True
    app.session_state.page = "Workspace"
    app.run()
    assert not app.exception
    assert app.session_state.assistant_open is False

    # 1. Open assistant via bottom tab button
    t0 = time.perf_counter()
    app.button(key="assistant_open_tab_btn").click().run()
    open_ms = (time.perf_counter() - t0) * 1000
    assert not app.exception
    assert app.session_state.assistant_open is True

    # 2. Click instant chip: Export Readiness
    t0 = time.perf_counter()
    app.button(key="quick_export").click().run()
    chip_ms = (time.perf_counter() - t0) * 1000
    assert not app.exception
    assert app.session_state.assistant_open is True
    assert any("Export readiness" in m["content"] for m in app.session_state.assistant_messages)

    # 3. Chat input query
    sid = workspace.selected[0]
    t0 = time.perf_counter()
    app.chat_input(key="assistant_chat_input").set_value(f"Describe scenario {sid}").run()
    chat_ms = (time.perf_counter() - t0) * 1000
    assert not app.exception
    assert app.session_state.assistant_open is True
    assert any(f"Scenario {sid}" in m["content"] for m in app.session_state.assistant_messages)

    # 4. Clear chat
    t0 = time.perf_counter()
    app.button(key="assistant_clear_chat").click().run()
    clear_ms = (time.perf_counter() - t0) * 1000
    assert not app.exception
    assert app.session_state.assistant_open is True
    assert len(app.session_state.assistant_messages) == 0

    # 5. Close assistant via drawer X button
    t0 = time.perf_counter()
    app.button(key="assistant_close_x").click().run()
    close_ms = (time.perf_counter() - t0) * 1000
    assert not app.exception
    assert app.session_state.assistant_open is False
