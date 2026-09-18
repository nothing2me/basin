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
    assert 'st.container(key="assistant_scenario_shortcuts")' in ui_source
    assert 'quick_one, quick_two = st.columns(2, gap="small")' in ui_source
    assert 'quick_five, quick_six = st.columns(2, gap="small")' in ui_source
    assert 'st.container(key="assistant_suggestions")' in ui_source
    assert "width:190px!important;height:190px!important" in theme_source
    assert 'position:sticky!important;bottom:0!important' in theme_source
    assert '.st-key-assistant_suggestions{padding:2px 0 0!important}' in theme_source

    chat_box_section = ui_source.split('chat_box = st.container(height=520, border=True, key="assistant_conversation")')[1]
    chat_box_body = chat_box_section.split('suggestion_bar = st.container(key="assistant_suggestions")')[0]
    assert "st.chat_input(" not in chat_box_body


def test_chat_message_avatar_inset_and_green_theme():
    theme_source = (ROOT / "basin_theme.py").read_text(encoding="utf-8")
    assert "--basin-user-avatar-bg:#23856d" in theme_source
    assert '[data-testid="stChatMessageAvatarUser"]{background-color:var(--basin-user-avatar-bg,#23856d)!important;' in theme_source
    assert 'padding-left:14px!important' in theme_source
    assert 'padding-left:0!important' not in theme_source
    assert '[data-testid="stChatMessage"] [data-testid^="stChatMessageAvatar"]' in theme_source



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
    assert app.button(key="quick_concur").label == "Station stress"
    sid = workspace.selected[0]
    app.chat_input(key="assistant_chat_input").set_value(f"Describe scenario {sid}").run()
    assert not app.exception
    assert app.session_state.assistant_open is True
    reply = app.session_state.assistant_messages[-1]["content"]
    assert f"Scenario {sid}" in reply
    assert "Error processing query" not in reply


def test_fresh_session_assistant_no_scenarios(source, monkeypatch):
    """In a fresh session (workspace=None), the assistant must not reference past scenarios."""
    from basin_core import qwen_runtime
    offline_client = SimpleNamespace(status="model_missing")
    monkeypatch.setattr(qwen_runtime, "get_qwen_client", lambda: offline_client)

    app = AppTest.from_string(
        "import streamlit as st\n"
        "from basin_ui import assistant_panel\n"
        "assistant_panel(st.session_state.workspace, source=st.session_state.source)\n",
        default_timeout=30,
    )
    app.session_state.workspace = None
    app.session_state.source = source
    app.session_state.assistant_open = False
    app.run()
    assert not app.exception

    # Open drawer
    app.button(key="assistant_open_tab_btn").click().run()
    assert not app.exception
    assert app.session_state.assistant_open is True

    # Status should indicate no active analysis run
    assert any("No active analysis run" in m.value for m in app.markdown)

    # Scenario calculation buttons should be disabled
    assert app.button(key="quick_top1").disabled is True
    assert app.button(key="quick_compare").disabled is True
    assert app.button(key="quick_concur").disabled is True
    assert app.button(key="quick_ranking").disabled is True
    assert app.button(key="quick_crop_et").disabled is True
    assert app.button(key="quick_export").disabled is True

    # Platform guidance buttons should be enabled
    assert app.button(key="quick_other_tools").disabled is False
    assert app.button(key="quick_next_step").disabled is False

    # Ask about scenarios when none have been run
    app.chat_input(key="assistant_chat_input").set_value("What are my scenarios?").run()
    assert not app.exception
    reply = app.session_state.assistant_messages[-1]["content"]
    assert "No active analysis run" in reply
    assert "Step 2: Scenario Builder" in reply
    assert "Try an example" in reply

    # Ask about worst scenario when none have been run
    app.chat_input(key="assistant_chat_input").set_value("What is the worst scenario?").run()
    assert not app.exception
    reply = app.session_state.assistant_messages[-1]["content"]
    assert "No active analysis run" in reply

    # Ask about specific scenario ID when none have been run
    app.chat_input(key="assistant_chat_input").set_value("Tell me about B-001").run()
    assert not app.exception
    reply = app.session_state.assistant_messages[-1]["content"]
    assert "No active analysis run" in reply
    assert "B-001" in reply

    # Data provenance and concept questions should still work
    app.chat_input(key="assistant_chat_input").set_value("Where does this data come from?").run()
    assert not app.exception
    reply = app.session_state.assistant_messages[-1]["content"]
    assert "NOAA" in reply or "GHCN" in reply

    app.chat_input(key="assistant_chat_input").set_value("What does concurrence mean?").run()
    assert not app.exception
    reply = app.session_state.assistant_messages[-1]["content"]
    assert "Concurrence" in reply
