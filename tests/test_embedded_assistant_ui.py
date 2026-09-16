"""Exercise the actual assistant drawer without an inference service."""
import socket
from pathlib import Path
from types import SimpleNamespace

from streamlit.testing.v1 import AppTest


ROOT = Path(__file__).resolve().parents[1]


def test_assistant_drawer_is_tall_with_visible_shortcuts():
    ui_source = (ROOT / "basin_ui.py").read_text(encoding="utf-8")
    theme_source = (ROOT / "basin_theme.py").read_text(encoding="utf-8")

    assert 'st.container(height=520, border=True, key="assistant_conversation")' in ui_source
    assert '"Suggested analyses"' not in ui_source
    assert 'Suggested questions' in ui_source
    assert 'quick_one, quick_two, quick_three, quick_four, quick_five, quick_six = st.columns(6, gap="small")' in ui_source
    assert 'st.container(key="assistant_suggestions")' in ui_source
    assert "width:190px!important;height:190px!important" in theme_source
    assert 'position:sticky!important;bottom:0!important' in theme_source
    assert '.st-key-assistant_suggestions{padding:2px 0 0!important}' in theme_source


def test_embedded_drawer_chat_query(workspace, monkeypatch):
    def no_network(*args, **kwargs):
        raise AssertionError("Assistant attempted a network connection")

    monkeypatch.setattr(socket.socket, "connect", no_network)
    monkeypatch.setattr(socket, "create_connection", no_network)
    from basin_core import qwen_runtime
    offline_client = SimpleNamespace(status="model_missing")
    monkeypatch.setattr(qwen_runtime, "get_qwen_client", lambda: offline_client)
    app = AppTest.from_string(
        "import streamlit as st\n"
        "from basin_ui import assistant_panel\n"
        "assistant_panel(st.session_state.workspace)\n",
        default_timeout=30,
    )
    app.session_state.workspace = workspace
    app.session_state.assistant_open = False
    app.run()
    assert not app.exception
    app.button(key="assistant_open_tab_btn").click().run()
    assert not app.exception
    assert app.session_state.assistant_open is True
    assert any("Uses this workspace’s data" in m.value for m in app.markdown)
    assert app.button(key="quick_top1").label == "Top scenario"
    assert app.button(key="quick_compare").label == "Compare"
    assert app.button(key="quick_concur").label == "Stress"
    sid = workspace.selected[0]
    app.chat_input(key="assistant_chat_input").set_value(f"Describe scenario {sid}").run()
    assert not app.exception
    assert app.session_state.assistant_open is True
    reply = app.session_state.assistant_messages[-1]["content"]
    assert f"Scenario {sid}" in reply
    assert "Error processing query" not in reply
