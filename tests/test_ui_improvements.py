"""Test suite verifying pipeline navigation gating, drawer sizing, and high-density page layouts."""
from pathlib import Path
import pytest
from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parents[1]


def test_navigation_locked_before_run_created():
    """Verify that Review and Exports stages are locked when no analysis run has been started."""
    at = AppTest.from_file(str(ROOT / "app.py"), default_timeout=45).run()
    assert not at.exception
    assert at.session_state.page == "Data"
    assert "workspace" not in at.session_state or at.session_state["workspace"] is None

    # Top navigation buttons
    btn_data = at.button(key="nav_tab_Data")
    btn_ws = at.button(key="nav_tab_Workspace")
    btn_rev = at.button(key="nav_tab_Review")
    btn_exp = at.button(key="nav_tab_Exports")

    assert not btn_data.disabled
    assert not btn_ws.disabled
    assert btn_rev.disabled
    assert btn_exp.disabled
    assert "🔒" in btn_rev.label
    assert "🔒" in btn_exp.label


def test_empty_state_on_direct_navigation_without_run():
    """Verify clean empty-state guidance when navigating directly to Review or Exports without a run."""
    at = AppTest.from_file(str(ROOT / "app.py"), default_timeout=45).run()
    assert "workspace" not in at.session_state or at.session_state["workspace"] is None

    # Switch to Review via sidebar radio
    at.sidebar.radio[0].set_value("Review").run()
    assert not at.exception
    assert any("No Active Analysis Run" in item.value for item in at.info)
    assert any(b.label == "➔ Go to Step 2: Scenario Builder" for b in at.button)
    assert "workspace" not in at.session_state or at.session_state["workspace"] is None

    # Switch to Exports via sidebar radio
    at.sidebar.radio[0].set_value("Exports").run()
    assert not at.exception
    assert any("No Active Analysis Run" in item.value for item in at.info)
    assert any(b.label == "➔ Go to Step 2: Scenario Builder" for b in at.button)
    assert "workspace" not in at.session_state or at.session_state["workspace"] is None


def test_drawer_sizing_and_smooth_transitions(monkeypatch, tmp_path):
    """Verify drawer controls and dynamic sizing attributes."""
    from basin_core.workspace import Workspace
    monkeypatch.setattr(Workspace, "save", lambda self: True)

    at = AppTest.from_file(str(ROOT / "app.py"), default_timeout=45).run()
    at.sidebar.radio[0].set_value("Workspace").run()
    next(b for b in at.button if b.label == "Create rainfall scenarios").click().run()
    assert at.session_state.workspace is not None

    # Notes drawer toggle & height selector
    at.button(key="btn_toggle_notes").click().run()
    assert at.session_state.notes_open is True
    if hasattr(at, "segmented_control"):
        sc = next((c for c in at.segmented_control if c.key == "notes_height_selector"), None)
        if sc:
            sc.set_value(600).run()
            assert at.session_state.notes_height == 600

    # Assistant drawer toggle & width selector
    at.button(key="assistant_open_tab_btn").click().run()
    assert at.session_state.assistant_open is True
    if hasattr(at, "segmented_control"):
        sc_w = next((c for c in at.segmented_control if c.key == "assistant_width_selector"), None)
        if sc_w:
            sc_w.set_value(650).run()
            assert at.session_state.assistant_width == 650


def test_simple_and_advanced_review_density(monkeypatch):
    """Simple limits the main tab row; Advanced restores the full tool set."""
    from basin_core.workspace import Workspace
    from basin_core.review_preferences import TAB_LABELS
    monkeypatch.setattr(Workspace, "save", lambda self: True)

    at = AppTest.from_file(str(ROOT / "app.py"), default_timeout=45).run()
    at.sidebar.radio[0].set_value("Workspace").run()
    next(b for b in at.button if b.label == "Create rainfall scenarios").click().run()

    # On Workspace: candidate list is directly visible
    assert any(b.label == "Open scenario review" for b in at.button)

    # On Review: Simple has two leading tabs and concise decision actions.
    at.sidebar.radio[0].set_value("Review").run()
    assert not at.exception
    assert any("Decide on the handoff" in m.value for m in at.markdown)
    assert any(b.label == "Include" for b in at.button)
    review_tabs = [t for t in at.tabs if t.label in set(TAB_LABELS.values())]
    assert len(review_tabs) == 5  # secondary tools remain reachable in More tools
    assert len([t for t in review_tabs if t.label in [tab.label for tab in at.tabs[:2]]]) == 2

    at.segmented_control(key=f"review_mode_{at.session_state.workspace.id}").set_value("advanced").run()
    assert not at.exception
    assert not any(e.label.startswith("More tools") for e in at.expander)

    # On Exports: 2-column layout and preview tabs are present
    at.sidebar.radio[0].set_value("Exports").run()
    assert not at.exception
    assert any(b.label == "Build verified export" for b in at.button)
    assert any("Export Controls & Verification" in m.value for m in at.markdown)
    assert any("Deliverable Workspace & Documentation" in m.value for m in at.markdown)
