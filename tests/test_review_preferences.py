"""Tailored Review: display preferences and the boundary they must not cross.

The Review focus decides which tools lead. It must never change a number, a ranking
weight, a review decision, a consent flag or an export digest, and it must never make a
tool unreachable.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from basin_core.review_preferences import (
    DATA_SOURCES,
    FOCUS_PRIMARY,
    GOALS,
    GUIDANCE,
    TAB_KEYS,
    TAB_LABELS,
    PREFERENCES_VERSION,
    ReviewPreferences,
    load_preferences,
    preferences_path,
    save_preferences,
)

ROOT = Path(__file__).resolve().parents[1]
TAB_LABEL_VALUES = set(TAB_LABELS.values())


# --------------------------------------------------------------------------------------
# The record itself
# --------------------------------------------------------------------------------------

def test_defaults_show_everything_and_ask_for_setup():
    prefs = ReviewPreferences()
    assert prefs.needs_setup is True
    assert prefs.configured is False
    primary, secondary = prefs.tab_layout()
    assert primary == TAB_KEYS and secondary == ()
    assert "skipped" in prefs.summary()


@pytest.mark.parametrize("kwargs", [
    {"goal": "bogus"}, {"data_source": "bogus"}, {"guidance": "bogus"},
    {"configured": "yes"}, {"show_all_tools": 1}, {"version": 0},
])
def test_invalid_preferences_are_rejected(kwargs):
    with pytest.raises(ValueError):
        ReviewPreferences(**kwargs)


@pytest.mark.parametrize("goal", list(GOALS))
def test_every_focus_keeps_every_tool_reachable(goal):
    """A focus reorders the page; it must never drop a tool."""
    primary, secondary = ReviewPreferences(goal=goal, configured=True).tab_layout()
    assert set(primary) | set(secondary) == set(TAB_KEYS)
    assert not set(primary) & set(secondary)
    assert set(primary) == set(FOCUS_PRIMARY[goal])


@pytest.mark.parametrize("goal", list(GOALS))
def test_source_evidence_always_leads(goal):
    """Source identity and limitations must not be demoted by a display choice."""
    primary, _ = ReviewPreferences(goal=goal, configured=True).tab_layout()
    assert "provenance" in primary


def test_show_all_tools_overrides_the_focus():
    prefs = ReviewPreferences(goal="storage", configured=True, show_all_tools=True)
    primary, secondary = prefs.tab_layout()
    assert primary == TAB_KEYS and secondary == ()


def test_suggested_preset_is_advisory_only():
    """A focus may recommend ranking weights; it never carries them."""
    prefs = ReviewPreferences(goal="handoff", configured=True)
    assert prefs.suggested_preset() == "Illustrative rural provider"
    # Nothing on the record is a weight, and an unconfigured focus suggests nothing.
    assert ReviewPreferences().suggested_preset() is None
    assert not any("weight" in field for field in prefs.to_record())


# --------------------------------------------------------------------------------------
# Persistence, including runs saved before this feature existed
# --------------------------------------------------------------------------------------

def test_round_trip(tmp_path):
    prefs = ReviewPreferences(goal="storage", data_source="own", guidance="technical",
                              configured=True, dismissed=True, show_all_tools=True)
    save_preferences("run-1", prefs, tmp_path)
    assert load_preferences("run-1", tmp_path) == prefs


def test_a_run_saved_before_this_feature_opens_with_defaults(tmp_path):
    """No preferences file is the normal state for every older saved run."""
    assert not preferences_path("older-run", tmp_path).exists()
    assert load_preferences("older-run", tmp_path) == ReviewPreferences()


@pytest.mark.parametrize("content", [
    "", "not json", "[]", "null",
    json.dumps({"goal": "removed-in-a-later-version"}),
    json.dumps({"goal": "storage", "guidance": None, "configured": "yes"}),
])
def test_damaged_or_foreign_preferences_fall_back_instead_of_crashing(tmp_path, content):
    preferences_path("run-2", tmp_path).write_text(content, encoding="utf-8")
    prefs = load_preferences("run-2", tmp_path)
    assert isinstance(prefs, ReviewPreferences)
    assert prefs.version == PREFERENCES_VERSION


def test_saving_never_raises_on_an_unwritable_location(tmp_path):
    blocked = tmp_path / "a-file-not-a-directory"
    blocked.write_text("", encoding="utf-8")
    assert save_preferences("run-3", ReviewPreferences(), blocked / "nested") is None


def test_preferences_live_outside_the_audited_record(workspace, tmp_path):
    """Display state must not be able to change an export digest."""
    before = json.dumps(workspace.record(True, include_custom=True), sort_keys=True)
    save_preferences(workspace.id, ReviewPreferences(goal="storage", configured=True), tmp_path)
    after = json.dumps(workspace.record(True, include_custom=True), sort_keys=True)
    assert after == before
    assert preferences_path(workspace.id, tmp_path).exists()


# --------------------------------------------------------------------------------------
# The Review page itself
# --------------------------------------------------------------------------------------

@pytest.fixture
def app(tmp_path, monkeypatch):
    """An app with generated scenarios, sitting on Review."""
    from basin_core.workspace import Workspace

    original_save = Workspace.save
    monkeypatch.setattr(Workspace, "save", lambda self: original_save(self, tmp_path))
    at = AppTest.from_file(str(ROOT / "app.py"), default_timeout=90).run()
    at.sidebar.radio[0].set_value("Workspace").run()
    next(b for b in at.button if b.label == "Create rainfall scenarios").click().run()
    at.sidebar.radio[0].set_value("Review").run()
    assert not at.exception
    return at


def top_level_tab_labels(at):
    return [tab.label for tab in at.tabs if tab.label in TAB_LABEL_VALUES]


def more_tools_expander(at):
    return next((e for e in at.expander if e.label.startswith("More tools")), None)


def rendered_text(at):
    """All rendered prose: captions, markdown, info and warning blocks."""
    parts = []
    for group in (at.caption, at.markdown, at.info, at.warning):
        parts.extend(element.value for element in group)
    return " ".join(parts)


def workspace_state(at):
    """Everything a display choice is forbidden to touch."""
    w = at.session_state.workspace
    return {
        "weights": dict(w.weights),
        "selected": list(w.selected),
        "statuses": {s.id: (s.status, s.revision, s.approved_revision) for s in w.scenarios},
        "record": json.dumps(w.record(True, include_custom=True), sort_keys=True),
        "experiment_config": (at.session_state["experiment_config"]
                              if "experiment_config" in at.session_state else None),
    }


def test_setup_is_offered_and_can_be_skipped(app):
    assert any("Set up this Review" in m.value for m in app.markdown)
    next(b for b in app.button if b.label == "Skip for now").click().run()
    assert not app.exception

    # Skipping leaves every tool in one row and no More tools drawer.
    assert set(top_level_tab_labels(app)) == TAB_LABEL_VALUES
    assert more_tools_expander(app) is None
    assert app.session_state["review_prefs"][1].configured is False
    assert any("Show all tools" in t.label for t in app.toggle)


@pytest.mark.parametrize("goal", list(GOALS))
def test_each_focus_leads_with_its_tools_and_keeps_the_rest(app, goal):
    app.radio(key="review_setup_goal").set_value(goal).run()
    next(b for b in app.button if b.label == "Use this focus").click().run()
    assert not app.exception

    prefs = app.session_state["review_prefs"][1]
    assert prefs.goal == goal and prefs.configured is True

    expected_primary = [TAB_LABELS[key] for key in TAB_KEYS if key in FOCUS_PRIMARY[goal]]
    assert top_level_tab_labels(app)[:len(expected_primary)] == expected_primary

    drawer = more_tools_expander(app)
    assert drawer is not None, "tools outside the focus must still be reachable"
    assert set(top_level_tab_labels(app)) == TAB_LABEL_VALUES


def test_changing_focus_changes_nothing_numerical_or_consensual(app):
    before = workspace_state(app)

    app.radio(key="review_setup_goal").set_value("storage").run()
    next(b for b in app.button if b.label == "Use this focus").click().run()
    assert not app.exception
    assert workspace_state(app) == before

    next(b for b in app.button if b.label == "Change focus").click().run()
    app.radio(key="review_setup_goal").set_value("handoff").run()
    next(b for b in app.button if b.label == "Use this focus").click().run()
    assert not app.exception
    assert workspace_state(app) == before


def test_show_all_tools_restores_one_row_without_losing_the_focus(app):
    app.radio(key="review_setup_goal").set_value("handoff").run()
    next(b for b in app.button if b.label == "Use this focus").click().run()
    assert more_tools_expander(app) is not None

    next(t for t in app.toggle if "Show all tools" in t.label).set_value(True).run()
    assert not app.exception
    assert more_tools_expander(app) is None
    assert set(top_level_tab_labels(app)) == TAB_LABEL_VALUES
    # The focus is remembered, not discarded, so turning the toggle back off restores it.
    assert app.session_state["review_prefs"][1].goal == "handoff"


def test_focus_survives_navigation_and_is_persisted_for_reopening(app, isolated_sessions):
    app.radio(key="review_setup_goal").set_value("storage").run()
    app.radio(key="review_setup_guidance").set_value("technical").run()
    next(b for b in app.button if b.label == "Use this focus").click().run()
    workspace_id = app.session_state.workspace.id

    app.sidebar.radio[0].set_value("Data").run()
    app.sidebar.radio[0].set_value("Review").run()
    assert not app.exception
    prefs = app.session_state["review_prefs"][1]
    assert (prefs.goal, prefs.guidance, prefs.configured) == ("storage", "technical", True)
    assert more_tools_expander(app) is not None

    # Reopening the saved run reads the same choices back from disk.
    assert load_preferences(workspace_id, isolated_sessions) == prefs


def test_choosing_own_data_never_implies_an_upload_happened(app):
    app.radio(key="review_setup_data").set_value("own").run()
    warnings = " ".join(w.value for w in app.warning)
    assert "No file has been uploaded" in warnings
    assert "no data has been validated" in warnings.lower()

    next(b for b in app.button if b.label == "Use this focus").click().run()
    assert "Nothing has been uploaded or validated by that choice" in rendered_text(app)
    assert not app.session_state.workspace.custom_uploads


def test_focus_does_not_apply_ranking_weights(app):
    weights_before = dict(app.session_state.workspace.weights)
    app.radio(key="review_setup_goal").set_value("handoff").run()
    next(b for b in app.button if b.label == "Use this focus").click().run()

    assert app.session_state.workspace.weights == weights_before
    text = rendered_text(app)
    assert "Ranking weights are not changed by your focus" in text
    assert "Illustrative rural provider" in text


def test_guidance_only_adds_notes_and_never_removes_disclosures(app):
    def disclosure_text(at):
        return rendered_text(at)

    app.radio(key="review_setup_guidance").set_value("technical").run()
    next(b for b in app.button if b.label == "Use this focus").click().run()
    technical = disclosure_text(app)

    next(b for b in app.button if b.label == "Change focus").click().run()
    app.radio(key="review_setup_guidance").set_value("guided").run()
    next(b for b in app.button if b.label == "Use this focus").click().run()
    guided = disclosure_text(app)

    for disclosure in ("Catchment Weighting Disclosure", "not the probability of a future drought"):
        assert disclosure in technical, disclosure
        assert disclosure in guided, disclosure
    assert len(guided) > len(technical)


def test_an_older_saved_run_opens_without_a_preferences_file(app, isolated_sessions):
    """The upgrade path: a run that predates this feature must not error."""
    workspace_id = app.session_state.workspace.id
    assert not preferences_path(workspace_id, isolated_sessions).exists()
    assert not app.exception
    assert set(top_level_tab_labels(app)) == TAB_LABEL_VALUES
