from pathlib import Path
from datetime import date

from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parents[1]


def test_searchable_station_picker_and_direct_date_range(tmp_path, monkeypatch):
    from basin_core.workspace import Workspace

    original_save = Workspace.save
    monkeypatch.setattr(Workspace, "save", lambda self: original_save(self, tmp_path))
    app = AppTest.from_file(str(ROOT / "app.py"), default_timeout=60).run()
    app.sidebar.radio[0].set_value("Workspace").run()

    station_picker = next(widget for widget in app.multiselect if widget.label == "Stations")
    assert set(station_picker.value) == {"USW00012924", "USW00012912", "USW00012921"}
    assert [widget.label for widget in app.date_input] == ["Dates"]
    assert not app.time_input

    app.date_input[0].set_value((date(2014, 3, 15), date(2014, 6, 12)))
    app.run()
    next(button for button in app.button if button.label == "Create rainfall scenarios").click().run()

    assert not app.exception
    assert app.session_state.workspace.params.calendar_ranges == (
        ("2014-03-15T00:00", "2014-06-12T23:59"),
    )


def test_full_user_workflow(tmp_path, monkeypatch):
    from basin_core.workspace import Workspace
    original_save = Workspace.save
    monkeypatch.setattr(Workspace, "save", lambda self: original_save(self, tmp_path))
    app = AppTest.from_file(str(ROOT / "app.py"), default_timeout=60).run()
    assert not app.exception
    assert "A clearer starting point" not in str(app.markdown)
    app.sidebar.radio[0].set_value("Workspace").run()
    next(b for b in app.button if b.label == "Create rainfall scenarios").click().run()
    assert not app.exception
    w = app.session_state.workspace
    assert len(w.scenarios) == 300
    detail_id = w.selected[-1]
    app.selectbox(key=f"shortfall_detail_{w.id}").set_value(detail_id).run()
    assert not app.exception
    deficit_metric = next(m for m in app.metric if m.label == "Total rainfall deficit")
    is_us = app.session_state.unit_mode == "us"
    expected_val = f"{w.get(detail_id).features['deficit_mm'] / 25.4:,.2f} in" if is_us else f"{w.get(detail_id).features['deficit_mm']:,.1f} mm"
    assert deficit_metric.value == expected_val
    next(b for b in app.button if b.label == "Open scenario review").click().run()
    assert app.session_state.inspect_id == detail_id
    assert app.session_state.page == "Review"
    app.sidebar.radio[0].set_value("Workspace").run()
    next(t for t in app.text_area if t.label == "Provider notes").set_value("Private planning note").run()
    next(b for b in app.button if b.label == "Save notes").click().run()
    assert w.notes == "Private planning note"
    app.sidebar.radio[0].set_value("Workspace").run()
    assert not app.exception
    preset_box = next((s for s in app.selectbox if s.label == "Community priority preset"), None)
    if preset_box:
        preset_box.set_value("Illustrative rural provider").run()
        assert app.session_state.workspace.weights["season"] == 50
    app.slider(key="weight_duration").set_value(80).run()
    assert app.session_state.workspace.weights["duration"] == 80
    app.sidebar.radio[0].set_value("Review").run()
    assert not app.exception
    app.segmented_control(key=f"review_mode_{w.id}").set_value("advanced").run()
    app.toggle(key="storage_experiment").set_value(True).run()
    app.radio(key="reservoir_sim_subview").set_value("Additional rainfall reductions").run()
    assert not app.exception
    app.radio(key="reservoir_sim_subview").set_value("Selected scenario").run()
    assert not app.exception
    next(t for t in app.text_input if t.label == "Review note").set_value(
        "Checked the selected system inputs and illustrative limitations"
    ).run()
    next(b for b in app.button if b.label == "Save experiment review").click().run()
    assert not app.exception
    for identifier in list(w.selected):
        next(s for s in app.selectbox if s.label == "Scenario").set_value(identifier).run()
        next(t for t in app.text_area if t.label == "Review note").set_value(
            f"Reviewed rainfall source and selected scenario {identifier} for handoff."
        ).run()
        next(b for b in app.button if b.label == "Include").click().run()
        assert not app.exception
    app.sidebar.radio[0].set_value("Exports").run()
    next(b for b in app.button if b.label == "Build verified export").click().run()
    assert not app.exception
    assert any("Rainfall Scenario Handoff" in m.value for m in app.markdown)
    assert app.session_state.packet["share"] is False
    assert app.session_state.packet["report"]["verified"]
    assert b"Hydrologist_Handoff_Brief.md" in app.session_state.packet["data"]
    app.sidebar.radio[0].set_value("Review").run()
    inspected = app.session_state.inspect_id
    next(t for t in app.text_area if t.label == "Review note").set_value("Check a drier daily sequence").run()
    next(b for b in app.button if b.label == "Apply multiplier").click().run()
    assert not app.exception
    assert app.session_state.workspace.get(inspected).status == "unreviewed"
    app.sidebar.radio[0].set_value("Exports").run()
    assert next(b for b in app.button if b.label == "Build verified export").disabled
    app.sidebar.radio[0].set_value("Data").run()
    assert not app.exception


def test_plain_language_four_stage_workflow(tmp_path, monkeypatch):
    from basin_core.workspace import Workspace
    original_save = Workspace.save
    monkeypatch.setattr(Workspace, "save", lambda self: original_save(self, tmp_path))
    app = AppTest.from_file(str(ROOT / "app.py"), default_timeout=60).run()

    assert not app.exception
    assert app.session_state.page == "Data"
    assert app.sidebar.radio[0].options == ["Data Dashboard", "Scenario Builder", "Review Selections", "Export"]
    assert any("Can I trust and use these observations?" in item.value for item in app.markdown)

    app.sidebar.radio[0].set_value("Workspace").run()
    assert not app.exception
    assert next(slider for slider in app.slider if slider.label == "Retained rainfall (% of observed rainfall)")
    assert next(box for box in app.selectbox if box.label == "Where reduced rainfall occurs")
    assert next(box for box in app.selectbox if box.label == "Scenarios to test")
    assert next(box for box in app.selectbox if box.label == "Scenarios to review")

    next(button for button in app.button if button.label == "Create rainfall scenarios").click().run()
    assert not app.exception

    assert app.session_state.page == "Workspace"
    assert any("Decision summary" in item.value for item in app.markdown)
    assert any("Why it ranked here" in item.value for item in app.caption)
    assert any("scenarios selected for review" in item.value for item in app.caption)
    assert any("approved for export" in item.value for item in app.caption)

    app.sidebar.radio[0].set_value("Review").run()
    assert not app.exception
    assert any("30-day windows with all selected stations stressed" in item.value for item in app.markdown)
    assert any("matched historical windows" in item.value for item in app.markdown)


def test_bottom_nav_syncs_sidebar_radio(tmp_path, monkeypatch):
    """Assert that clicking forward/back action buttons mutates session_state
    and cleanly re-renders the sidebar radio to the corresponding stage.
    """
    from basin_core.workspace import Workspace
    original_save = Workspace.save
    monkeypatch.setattr(Workspace, "save", lambda self: original_save(self, tmp_path))
    app = AppTest.from_file(str(ROOT / "app.py"), default_timeout=60).run()

    # Step 1 (Initial Landing)
    assert app.session_state.page == "Data"
    assert app.sidebar.radio[0].value == "Data"

    # Click forward to Step 2 via acceptance button
    next(b for b in app.button if "Accept Baseline & Proceed" in b.label).click().run()
    assert not app.exception
    assert app.session_state.page == "Workspace"
    assert app.sidebar.radio[0].value == "Workspace"

    # Click back to Step 1 via bottom button
    next(b for b in app.button if "Back to Step 1" in b.label).click().run()
    assert not app.exception
    assert app.session_state.page == "Data"
    assert app.sidebar.radio[0].value == "Data"

    # Load example scenario set
    next(b for b in app.button if b.label == "Try an example").click().run()
    assert not app.exception
    assert app.session_state.page == "Review"
    assert app.sidebar.radio[0].value == "Review"

    # Review each current revision and advance through the remaining shortlist.
    for index in range(len(app.session_state.workspace.selected)):
        current_id = app.session_state.inspect_id
        next(t for t in app.text_area if t.label == "Review note").set_value(
            f"Reviewed rainfall source and selected scenario {current_id} for handoff."
        ).run()
        next(b for b in app.button if b.label == "Include").click().run()
        if index + 1 < len(app.session_state.workspace.selected):
            before_id = app.session_state.inspect_id
            next(b for b in app.button if b.label == "Next scenario").click().run()
            assert app.session_state.inspect_id != before_id
            assert app.session_state.workspace.get(app.session_state.inspect_id).status == "unreviewed"
    assert not app.exception

    # Click forward to Step 4 via bottom button
    next(b for b in app.button if "Proceed to Step 4" in b.label).click().run()
    assert not app.exception
    assert app.session_state.page == "Exports"
    assert app.sidebar.radio[0].value == "Exports"

    # Click back to Step 3 via bottom button
    next(b for b in app.button if "Back to Step 3" in b.label).click().run()
    assert not app.exception
    assert app.session_state.page == "Review"
    assert app.sidebar.radio[0].value == "Review"


def test_interactive_tutorial_walkthrough(tmp_path, monkeypatch):
    from basin_core.workspace import Workspace
    original_save = Workspace.save
    monkeypatch.setattr(Workspace, "save", lambda self: original_save(self, tmp_path))
    app = AppTest.from_file(str(ROOT / "app.py"), default_timeout=60).run()
    assert not app.exception
    assert "tutorial_active" not in app.session_state or not app.session_state["tutorial_active"]

    # Start from Help on the first stage; restart there again later.
    start_btn = next(b for b in app.button if b.label == "Start tutorial")
    start_btn.click().run()
    assert not app.exception
    assert app.session_state.tutorial_active is True
    assert app.session_state.tutorial_step == 0
    assert app.session_state.page == "Data"

    # Step through all 7 guided steps across the pipeline.
    for step in range(1, 7):
        next_btn = next(b for b in app.button if b.label == "Next Step ▶")
        next_btn.click().run()
        assert not app.exception
        assert app.session_state.tutorial_step == step

    assert app.session_state.tutorial_step == 6
    assert app.session_state.page == "Exports"

    # The tour must explain the review gate, never silently approve demo data.
    assert next(b for b in app.button if b.label == "Build verified export").disabled
    assert any("Export is locked" in m.value for m in app.markdown)
    assert all(app.session_state.workspace.get(i).status == "unreviewed"
               for i in app.session_state.workspace.selected)

    # Manual navigation keeps a way back to the active step.
    app.sidebar.radio[0].set_value("Data").run()
    next(b for b in app.button if b.label == "Return to this step").click().run()
    assert app.session_state.page == "Exports"
    assert app.session_state.tutorial_step == 6

    # Test Previous button
    prev_btn = next(b for b in app.button if b.label == "◀ Prev")
    prev_btn.click().run()
    assert not app.exception
    assert app.session_state.tutorial_step == 5
    assert app.session_state.page == "Review"

    # Advance back to end and finish
    next_btn = next(b for b in app.button if b.label == "Next Step ▶")
    next_btn.click().run()
    assert not app.exception
    assert app.session_state.tutorial_step == 6

    finish_btn = next(b for b in app.button if b.label == "✓ Finish Tutorial")
    finish_btn.click().run()
    assert not app.exception
    assert app.session_state.tutorial_active is False

    # Verify we can restart anytime from Help and exit early
    start_btn2 = next(b for b in app.button if b.label == "Start tutorial")
    start_btn2.click().run()
    assert not app.exception
    assert app.session_state.tutorial_active is True
    exit_btn = next(b for b in app.button if b.label == "✕ Exit")
    exit_btn.click().run()
    assert not app.exception
    assert app.session_state.tutorial_active is False



def test_first_use_example_is_reviewable_not_approved(tmp_path, monkeypatch):
    from basin_core.workspace import Workspace
    original_save = Workspace.save
    monkeypatch.setattr(Workspace, "save", lambda self: original_save(self, tmp_path))
    app = AppTest.from_file(str(ROOT / "app.py"), default_timeout=60).run()
    assert not app.exception
    assert app.session_state.page == "Data"
    next(b for b in app.button if b.label == "Try an example").click().run()
    assert not app.exception
    assert app.session_state.page == "Review"
    workspace = app.session_state.workspace
    assert workspace.params.seed == 22
    assert len(workspace.selected) == 6
    assert all(workspace.get(i).status == "unreviewed" for i in workspace.selected)
    app.sidebar.radio[0].set_value("Exports").run()
    assert next(b for b in app.button if b.label == "Build verified export").disabled


def test_crisis_demo_uses_documented_starting_context_without_approval(tmp_path, monkeypatch):
    from basin_core.workspace import Workspace
    original_save = Workspace.save
    monkeypatch.setattr(Workspace, "save", lambda self: original_save(self, tmp_path))
    app = AppTest.from_file(str(ROOT / "app.py"), default_timeout=60).run()

    next(b for b in app.button if b.label == "Load 2026 crisis demo").click().run()

    assert not app.exception
    assert app.session_state.page == "Review"
    assert app.session_state.storage_experiment is True
    assert app.session_state.review_initial_storage == "7.7% (April 2026 context)"
    assert abs(app.session_state.experiment_config.initial_pct - 0.077) < 1e-12
    assert all(s.status == "unreviewed" for s in app.session_state.workspace.scenarios)
    assert any("resulting trajectory are illustrative" in item.value for item in app.caption)


def test_custom_colors_reset_and_accessible_charts(tmp_path, monkeypatch):
    from basin_core.workspace import Workspace
    from basin_theme import accent_foreground
    original_save = Workspace.save
    monkeypatch.setattr(Workspace, "save", lambda self: original_save(self, tmp_path))
    assert accent_foreground("#FFFFFF") == "#000000"
    assert accent_foreground("#000000") == "#FFFFFF"
    assert accent_foreground("#356273") == "#FFFFFF"
    app = AppTest.from_file(str(ROOT / "app.py"), default_timeout=60).run()
    app.color_picker(key="draft_accent").set_value("#FFFF00")
    app.color_picker(key="draft_selection").set_value("#AA44CC")
    app.color_picker(key="draft_sidebar").set_value("#334455")
    assert app.session_state.appearance_accent == "#356273"
    next(b for b in app.button if b.label == "Apply colors").click().run()
    assert app.session_state.appearance_accent == "#FFFF00"
    assert app.session_state.appearance_selection == "#AA44CC"
    assert app.session_state.appearance_sidebar == "#334455"
    app.toggle(key="appearance_colorblind").set_value(True).run()
    next(b for b in app.button if b.label == "Try an example").click().run()
    assert not app.exception
    workspace = app.session_state.workspace
    before = [(s.id, s.score, s.status) for s in workspace.scenarios]
    next(b for b in app.button if b.label == "Use this focus").click().run()
    app.segmented_control(key=f"review_mode_{workspace.id}").set_value("advanced").run()
    app.toggle(key="storage_experiment").set_value(True).run()
    app.radio(key="reservoir_sim_subview").set_value("Additional rainfall reductions").run()
    assert not app.exception
    assert app.session_state.appearance_colorblind
    next(b for b in app.button if b.label == "Reset custom colors").click().run()
    assert not app.exception
    assert app.session_state.appearance_accent == "#356273"
    assert not app.session_state.appearance_colorblind
    assert before == [(s.id, s.score, s.status) for s in workspace.scenarios]


def test_review_uses_rainfall_summary_and_requires_human_note(tmp_path, monkeypatch):
    from streamlit.testing.v1 import AppTest
    from basin_core.workspace import Workspace
    original_save = Workspace.save
    monkeypatch.setattr(Workspace, "save", lambda self: original_save(self, tmp_path))

    app = AppTest.from_file(str(ROOT / "app.py"), default_timeout=60).run()
    next(b for b in app.button if b.label == "Try an example").click().run()
    assert not app.exception
    assert app.session_state.page == "Review"

    assert any("Rainfall Screening Summary" in m.value for m in app.markdown)
    assert not any("AI Operational Interpretation" in m.value for m in app.markdown)

    review_area = next(t for t in app.text_area if t.label == "Review note")
    assert review_area.value == ""
    assert next(b for b in app.button if b.label == "Include").disabled

    inspected = app.session_state.inspect_id
    review_area.set_value("Selected for hydrologist review because the source window and station coverage match the screening question.").run()
    next(b for b in app.button if b.label == "Include").click().run()
    assert not app.exception
    assert app.session_state.workspace.get(inspected).status == "accepted"
    last_event = app.session_state.workspace.get(inspected).history[-1]
    assert last_event["private_note"].startswith("Selected for hydrologist review")
    assert "Engineering Assessment" not in last_event["private_note"]


def test_batch_accept_requires_and_records_specific_rationale(tmp_path, monkeypatch):
    from basin_core.workspace import Workspace
    original_save = Workspace.save
    monkeypatch.setattr(Workspace, "save", lambda self: original_save(self, tmp_path))

    app = AppTest.from_file(str(ROOT / "app.py"), default_timeout=60).run()
    next(b for b in app.button if b.label == "Try an example").click().run()
    app.sidebar.radio[0].set_value("Exports").run()

    batch_button = next(b for b in app.button if "Accept all shortlisted" in b.label)
    assert batch_button.disabled
    rationale = next(t for t in app.text_input if t.label == "Batch review rationale")
    rationale.set_value("All six source windows answer the same documented screening question.").run()
    batch_button = next(b for b in app.button if "Accept all shortlisted" in b.label)
    assert not batch_button.disabled
    batch_button.click().run()

    workspace = app.session_state.workspace
    for scenario_id in workspace.selected:
        event = workspace.get(scenario_id).history[-1]
        assert event["private_note"].startswith("included by batch decision:")
        assert event["decision_mode"] == "batch"


def test_activated_gauge_gets_consent_control_without_comparison_record(tmp_path, monkeypatch):
    import pandas as pd
    from basin_core.data import CachedSource
    from basin_core.engine import ScenarioParams
    from basin_core.workspace import Workspace

    original_save = Workspace.save
    monkeypatch.setattr(Workspace, "save", lambda self: original_save(self, tmp_path))
    base = CachedSource()
    custom = base.with_custom_station(
        "LOCAL_UI_CONSENT",
        "UI Consent Gauge",
        pd.Series(1.5, index=pd.date_range("2020-01-01", "2022-12-31")),
    )
    workspace = Workspace(
        custom,
        ScenarioParams(("LOCAL_UI_CONSENT",), (90,), (1, 4), candidates=10, seed=42),
        size=3,
    )
    for scenario_id in workspace.selected:
        workspace.get(scenario_id).review(True, "Reviewed local-gauge rainfall for recipient handoff.")
    assert workspace.custom_uploads == [] and workspace.has_custom_data

    app = AppTest.from_file(str(ROOT / "app.py"), default_timeout=60).run()
    app.session_state.workspace = workspace
    app.session_state.custom_source = custom
    app.run()
    app.sidebar.radio[0].set_value("Exports").run()

    consent = next(c for c in app.checkbox if c.label.startswith("Include custom numerical inputs"))
    build = next(b for b in app.button if b.label == "Build verified export")
    assert build.disabled
    consent.check().run()
    build = next(b for b in app.button if b.label == "Build verified export")
    assert not build.disabled

