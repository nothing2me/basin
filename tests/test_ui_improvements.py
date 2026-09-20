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
    assert btn_rev.label == "Review Selections"
    assert btn_exp.label == "Export"


def test_empty_state_on_direct_navigation_without_run():
    """Verify clean empty-state guidance when navigating directly to Review or Exports without a run."""
    at = AppTest.from_file(str(ROOT / "app.py"), default_timeout=45).run()
    assert "workspace" not in at.session_state or at.session_state["workspace"] is None

    # Switch to Review via sidebar radio
    at.sidebar.radio[0].set_value("Review").run()
    assert not at.exception
    assert any("No Active Analysis Run" in item.value for item in at.info)
    assert any(b.label == "Go to Step 2: Scenario Builder" for b in at.button)
    assert "workspace" not in at.session_state or at.session_state["workspace"] is None

    # Switch to Exports via sidebar radio
    at.sidebar.radio[0].set_value("Exports").run()
    assert not at.exception
    assert any("No Active Analysis Run" in item.value for item in at.info)
    assert any(b.label == "Go to Step 2: Scenario Builder" for b in at.button)
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


def test_review_decision_gating_and_suggested_rationale(monkeypatch):
    """Verify that Include button is disabled until 20 chars are entered or suggested rationale is used."""
    from basin_core.workspace import Workspace
    monkeypatch.setattr(Workspace, "save", lambda self: True)

    at = AppTest.from_file(str(ROOT / "app.py"), default_timeout=45).run()
    at.sidebar.radio[0].set_value("Workspace").run()
    next(b for b in at.button if b.label == "Create rainfall scenarios").click().run()

    at.sidebar.radio[0].set_value("Review").run()
    assert not at.exception

    include_btn = next(b for b in at.button if b.label == "Include")
    assert include_btn.disabled  # Initially disabled because review note is empty

    # Click 'Use suggested rationale'
    suggest_btn = next(b for b in at.button if "Use suggested rationale" in b.label)
    suggest_btn.click().run()
    assert not at.exception

    # Note text area is now populated with > 20 chars
    note_area = next(t for t in at.text_area if t.label == "Review note")
    assert len(note_area.value.strip()) >= 20
    assert "verified suitable" not in note_area.value
    assert "remain unvalidated" in note_area.value

    # Include button is now unlocked
    include_btn = next(b for b in at.button if b.label == "Include")
    assert not include_btn.disabled

    # Click Include to review the scenario
    include_btn.click().run()
    assert not at.exception


def test_next_scenario_cycles_through_all_scenarios(monkeypatch):
    """Verify that clicking Next scenario navigates through all 6 scenarios in sequence without looping between 2."""
    from basin_core.workspace import Workspace
    monkeypatch.setattr(Workspace, "save", lambda self: True)

    at = AppTest.from_file(str(ROOT / "app.py"), default_timeout=45).run()
    at.sidebar.radio[0].set_value("Workspace").run()
    next(b for b in at.button if b.label == "Create rainfall scenarios").click().run()

    at.sidebar.radio[0].set_value("Review").run()
    assert not at.exception

    selected = list(at.session_state.workspace.selected)
    assert len(selected) == 6

    visited = [at.session_state.inspect_id]
    for _ in range(len(selected) - 1):
        next(b for b in at.button if b.label == "Next scenario").click().run()
        assert not at.exception
        visited.append(at.session_state.inspect_id)

    # All 6 distinct scenarios must be visited in order
    assert len(set(visited)) == 6
    assert visited == selected


def test_export_deliverable_workspace_tabs_single_row(monkeypatch):
    """Verify Deliverable Workspace & Documentation uses a single un-nested row of 6 clean tabs."""
    from basin_core.workspace import Workspace
    monkeypatch.setattr(Workspace, "save", lambda self: True)

    at = AppTest.from_file(str(ROOT / "app.py"), default_timeout=45).run()
    at.sidebar.radio[0].set_value("Workspace").run()
    next(b for b in at.button if b.label == "Create rainfall scenarios").click().run()

    at.sidebar.radio[0].set_value("Exports").run()
    assert not at.exception
    assert any("Deliverable Workspace & Documentation" in m.value for m in at.markdown)

    # Verify the 5 clean tabs exist and HTML Report is removed
    tab_labels = [t.label for t in at.tabs]
    expected_tabs = [
        ":material/monitoring: Visual Figures",
        ":material/description: Executive Brief",
        ":material/table_chart: Shortlist Details",
        ":material/fact_check: Evidence & Provenance",
        ":material/eco: Environmental Footprint",
    ]
    for tab in expected_tabs:
        assert any(tab in label for label in tab_labels), f"Missing tab: {tab}"
    assert not any("HTML Report" in label for label in tab_labels), "HTML Report tab should be removed"


def test_primary_ui_uses_one_icon_family_instead_of_emoji():
    """Visible application chrome should use Material Symbols, not platform emoji glyphs."""
    source = (ROOT / "app.py").read_text(encoding="utf-8")
    retired_emoji = ("💾", "⚙️", "❓", "📦", "📋", "⚠️", "🔍", "✅", "📈", "📄", "📊", "📁", "🌱")
    assert not any(glyph in source for glyph in retired_emoji)
    for icon in ("history", "settings", "tune", "help_outline", "unarchive", "fact_check", "rate_review"):
        assert f":material/{icon}:" in source


def test_system_theme_follows_streamlit_theme_and_defines_dark_text_contrast():
    source = (ROOT / "basin_theme.py").read_text(encoding="utf-8")
    assert "getComputedStyle(document.body).backgroundColor" in source
    assert "mode === 'System' && nativeIsLight" in source
    assert "requestAnimationFrame(() => applyBasinTheme())" in source
    assert 'body.basin-theme-dark h1' in source
    assert 'color:var(--basin-text-strong)!important' in source


def test_top_header_keeps_brand_centered_and_utilities_compact():
    """The three header regions stay balanced and Settings uses the standard gear symbol."""
    source = (ROOT / "app.py").read_text(encoding="utf-8")
    styles = (ROOT / "basin_theme.py").read_text(encoding="utf-8")

    assert 'st.columns([1, 1, 1], vertical_alignment="center")' in source
    assert 'key="top_utility_group"' in source
    assert 'st.popover("Settings", icon=":material/settings:"' in source
    assert 'st.popover("Settings", icon=":material/tune:"' not in source
    assert ".st-key-global_unit_selector{max-width:420px!important}" in styles
    assert ".st-key-top_utility_group{max-width:570px!important;margin-left:auto!important}" in styles



