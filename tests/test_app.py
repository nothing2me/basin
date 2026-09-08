from pathlib import Path

from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parents[1]


def test_full_user_workflow(tmp_path, monkeypatch):
    from basin_core.workspace import Workspace
    original_save = Workspace.save
    monkeypatch.setattr(Workspace, "save", lambda self: original_save(self, tmp_path))
    app = AppTest.from_file(str(ROOT / "app.py"), default_timeout=60).run()
    assert not app.exception
    assert "A clearer starting point" not in str(app.markdown)
    next(b for b in app.button if b.label == "Create rainfall scenarios").click().run()
    assert not app.exception
    w = app.session_state.workspace
    assert len(w.scenarios) == 300
    next(t for t in app.text_area if t.label == "Provider notes").set_value("Private planning note").run()
    next(b for b in app.button if b.label == "Save notes").click().run()
    assert w.notes == "Private planning note"
    app.sidebar.radio[0].set_value("Workspace").run()
    assert not app.exception
    preset_box = next((s for s in app.sidebar.selectbox if s.label == "Community priority preset"), None)
    if preset_box:
        preset_box.set_value("Illustrative rural provider").run()
        assert app.session_state.workspace.weights["season"] == 50
    app.slider(key="weight_duration").set_value(80).run()
    assert app.session_state.workspace.weights["duration"] == 80
    app.sidebar.radio[0].set_value("Review").run()
    assert not app.exception
    series_radio = next((r for r in app.radio if "Cumulative rainfall" in r.options), None)
    if series_radio:
        series_radio.set_value("Reservoir simulation").run()
        assert not app.exception
        series_radio.set_value("Cumulative rainfall").run()
        assert not app.exception
    for identifier in list(w.selected):
        next(s for s in app.selectbox if s.label == "Scenario").set_value(identifier).run()
        next(b for b in app.button if b.label == "Accept").click().run()
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
    assert app.session_state.page == "Workspace"
    assert app.sidebar.radio[0].options == ["1. Check data", "2. Build scenarios", "3. Review choices", "4. Share results"]
    assert any(item.value == "2. Build scenarios" for item in app.subheader)
    assert any("Which rainfall scenarios deserve review?" in item.value for item in app.markdown)
    assert next(slider for slider in app.sidebar.slider if slider.label == "Rainfall compared with original · %")
    assert next(box for box in app.sidebar.selectbox if box.label == "Where reduced rainfall occurs")
    assert next(box for box in app.sidebar.selectbox if box.label == "Scenarios to test")
    assert next(box for box in app.sidebar.selectbox if box.label == "Scenarios to review")

    next(button for button in app.button if button.label == "Create rainfall scenarios").click().run()
    assert not app.exception
    assert app.session_state.page == "Workspace"
    assert any(item.value == "2. Build scenarios" for item in app.subheader)
    assert any("Decision summary" in item.value for item in app.markdown)
    assert any("Why it ranked here" in item.value for item in app.caption)
    assert {metric.label for metric in app.metric} >= {
        "Scenarios to review", "Approved for export"
    }

    app.sidebar.radio[0].set_value("Review").run()
    assert not app.exception
    assert any(item.value == "3. Review choices" for item in app.subheader)
    assert any("Stations stressed together" in item.value for item in app.markdown)
    assert any("How unusual vs history" in item.value for item in app.markdown)


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
    assert not app.get("file_uploader")
    assert not app.get("plotly_chart")
    next(b for b in app.button if b.label == "Try an example").click().run()
    assert not app.exception
    assert app.session_state.page == "Review"
    workspace = app.session_state.workspace
    assert workspace.params.seed == 22
    assert len(workspace.selected) == 6
    assert all(workspace.get(i).status == "unreviewed" for i in workspace.selected)
    app.sidebar.radio[0].set_value("Exports").run()
    assert next(b for b in app.button if b.label == "Build verified export").disabled


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
    next(r for r in app.radio if "Reservoir simulation" in r.options).set_value("Reservoir simulation").run()
    assert not app.exception
    assert app.session_state.appearance_colorblind
    next(b for b in app.button if b.label == "Reset colors").click().run()
    assert not app.exception
    assert app.session_state.appearance_accent == "#356273"
    assert not app.session_state.appearance_colorblind
    assert before == [(s.id, s.score, s.status) for s in workspace.scenarios]
