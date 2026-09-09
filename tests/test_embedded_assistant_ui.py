"""Exercise the actual assistant drawer without an inference service."""
import socket

from streamlit.testing.v1 import AppTest


def test_embedded_drawer_chat_and_quick_queries(workspace, monkeypatch):
    def no_network(*args, **kwargs):
        raise AssertionError("Assistant attempted a network connection")

    monkeypatch.setattr(socket.socket, "connect", no_network)
    monkeypatch.setattr(socket, "create_connection", no_network)
    app = AppTest.from_string(
        "import streamlit as st\n"
        "from basin_ui import assistant_panel\n"
        "assistant_panel(st.session_state.workspace)\n",
        default_timeout=30,
    )
    app.session_state.workspace = workspace
    app.session_state.assistant_open = True
    app.run()
    assert not app.exception
    assert any("Ready: Qwen2.5-3B" in m.value or "Active: Deterministic Intent Router" in m.value or "Active: Embedded Intent Engine" in m.value for m in app.markdown)
    app.button(key="quick_export").click().run()
    assert not app.exception
    assert "Export readiness" in app.session_state.assistant_messages[-1]["content"]
    sid = workspace.selected[0]
    app.chat_input(key="assistant_chat_input").set_value(f"Describe scenario {sid}").run()
    assert not app.exception
    reply = app.session_state.assistant_messages[-1]["content"]
    assert f"Scenario {sid}" in reply
    assert "Error processing query" not in reply
