"""Experiment configuration carried into report previews and exports.

Covers B17.1/B17.2: the selected scenario/revision and experiment settings reach both
rendering paths, the configuration is stated in the output, and a generated report is
invalidated when its inputs or consent change.
"""
import re

import pandas as pd
import pytest

from basin_core.pdf_report import (
    DEFAULT_CONSERVATION_PCT,
    DEFAULT_INITIAL_PCT,
    DEFAULT_PIPELINE_ACTIVE,
    DEFAULT_TIERS,
    ExperimentConfig,
    build_fallback_pdf,
    generate_pdf_report,
    render_html_report,
    report_state_token,
    resolve_config,
    select_primary_scenario,
)


@pytest.fixture
def approved(workspace):
    for identifier in workspace.selected:
        workspace.get(identifier).review(True, "Accepted for unit test")
    return workspace


def vector_text(pdf_bytes: bytes) -> str:
    """The drawn text of a vector PDF, with PDF string escaping undone."""
    drawn = []
    for line in pdf_bytes.decode("latin1").splitlines():
        match = re.search(r"Tm \((.*)\) Tj ET$", line)
        if match:
            drawn.append(match.group(1).replace(r"\(", "(").replace(r"\)", ")").replace(r"\\", "\\"))
    return " ".join(drawn)


def html_stage3_days(html: str) -> list[str]:
    return re.findall(r"<strong>Day (\d+)\*</strong>", html)


# --------------------------------------------------------------------------------------
# The configuration object itself
# --------------------------------------------------------------------------------------

def test_defaults_match_the_simulator_defaults():
    config = ExperimentConfig()
    assert (config.initial_pct, config.conservation_pct) == (DEFAULT_INITIAL_PCT, DEFAULT_CONSERVATION_PCT)
    assert config.pipeline_active is DEFAULT_PIPELINE_ACTIVE
    assert config.tiers == DEFAULT_TIERS
    assert config.selected is False


@pytest.mark.parametrize("kwargs", [
    {"initial_pct": -0.1}, {"initial_pct": 1.5}, {"initial_pct": float("nan")},
    {"conservation_pct": 1.5}, {"conservation_pct": float("inf")},
    {"pipeline_active": "yes"}, {"tiers": ()}, {"tiers": (0.0,)}, {"tiers": (-1.0,)},
    {"scenario_revision": "2"}, {"scenario_id": 5},
])
def test_invalid_configuration_is_rejected(kwargs):
    with pytest.raises(ValueError):
        ExperimentConfig(**kwargs)


def test_default_configuration_does_not_claim_to_be_a_user_choice():
    rows = dict(ExperimentConfig().describe_rows())
    assert rows["Configuration source"] == "BASIN default; no experiment was run in Review"
    chosen = dict(ExperimentConfig(selected=True, scenario_id="B-009", scenario_revision=2).describe_rows())
    assert chosen["Configuration source"] == "Selected in Review"
    assert chosen["Experiment scenario"] == "B-009 (revision 2)"


def test_legacy_percentage_arguments_still_resolve():
    assert resolve_config(None, 60.0, 30.0).initial_pct == pytest.approx(0.60)
    assert resolve_config(None, 0.35, 0.10).conservation_pct == pytest.approx(0.10)
    # Values passed positionally were never a recorded choice, so they are not "selected".
    assert resolve_config(None, 60.0, 30.0).selected is False
    explicit = ExperimentConfig(initial_pct=0.35, selected=True)
    assert resolve_config(explicit, 60.0, 30.0) is explicit


# --------------------------------------------------------------------------------------
# Settings actually reach the results
# --------------------------------------------------------------------------------------

def test_initial_storage_changes_reported_results_in_both_paths(approved):
    accepted = approved.exportable()
    high = ExperimentConfig(initial_pct=0.60)
    low = ExperimentConfig(initial_pct=0.35)

    html_high = render_html_report(approved, accepted, config=high)
    html_low = render_html_report(approved, accepted, config=low)
    assert "60% of combined capacity" in html_high
    assert "35% of combined capacity" in html_low
    assert html_stage3_days(html_high) != html_stage3_days(html_low)

    text_high = vector_text(build_fallback_pdf(approved, accepted, config=high))
    text_low = vector_text(build_fallback_pdf(approved, accepted, config=low))
    assert "60% of combined capacity" in text_high
    assert "35% of combined capacity" in text_low
    assert text_high != text_low


def test_conservation_changes_reported_results_in_both_paths(approved):
    accepted = approved.exportable()
    none_cons = ExperimentConfig(initial_pct=0.35, conservation_pct=0.0)
    heavy_cons = ExperimentConfig(initial_pct=0.35, conservation_pct=0.30)

    html_none = render_html_report(approved, accepted, config=none_cons)
    html_heavy = render_html_report(approved, accepted, config=heavy_cons)
    assert "0% demand reduction" in html_none
    assert "30% demand reduction" in html_heavy
    assert html_none != html_heavy

    assert "30% demand reduction" in vector_text(build_fallback_pdf(approved, accepted, config=heavy_cons))


def test_pipeline_assumption_reaches_the_simulation(approved):
    accepted = approved.exportable()
    on = ExperimentConfig(initial_pct=0.35, pipeline_active=True)
    off = ExperimentConfig(initial_pct=0.35, pipeline_active=False)

    html_on = render_html_report(approved, accepted, config=on)
    html_off = render_html_report(approved, accepted, config=off)
    assert "Assumed available" in html_on
    assert "Assumed unavailable" in html_off
    # Withdrawing more water without the pipeline must move the modelled loss driver.
    assert html_on != html_off
    assert "Assumed unavailable" in vector_text(build_fallback_pdf(approved, accepted, config=off))


def test_rainfall_tiers_reach_the_spectrum_table(approved):
    accepted = approved.exportable()
    config = ExperimentConfig(tiers=(1.0, 0.5))

    html = render_html_report(approved, accepted, config=config)
    assert "100%, 50%" in html
    assert html.count("<td>50.0%</td>") == 1
    assert "<td>80.0%</td>" not in html

    text = vector_text(build_fallback_pdf(approved, accepted, config=config))
    assert "100%, 50%" in text
    assert "2 rainfall retention tiers" in text


# --------------------------------------------------------------------------------------
# Scenario selection is carried, never silently replaced
# --------------------------------------------------------------------------------------

def test_configured_scenario_is_used_as_the_experiment_scenario(approved):
    accepted = approved.exportable()
    assert len(accepted) > 1
    target = accepted[1]
    config = ExperimentConfig(scenario_id=target.id, scenario_revision=target.revision, selected=True)

    scenario, note = select_primary_scenario(accepted, config)
    assert scenario is target
    assert note is None

    html = render_html_report(approved, accepted, config=config)
    assert f"{target.id} (revision {target.revision})" in html
    # The primary scenario drives the spectrum caption, so it must be the configured one.
    assert f"tiers for {target.id}" in html


def test_scenario_choice_changes_the_reported_results(approved):
    accepted = approved.exportable()
    first = ExperimentConfig(scenario_id=accepted[0].id, scenario_revision=accepted[0].revision, selected=True)
    second = ExperimentConfig(scenario_id=accepted[1].id, scenario_revision=accepted[1].revision, selected=True)

    assert render_html_report(approved, accepted, config=first) != render_html_report(approved, accepted, config=second)
    assert build_fallback_pdf(approved, accepted, config=first) != build_fallback_pdf(approved, accepted, config=second)


def test_unavailable_configured_scenario_is_stated_not_swapped(approved):
    accepted = approved.exportable()
    config = ExperimentConfig(scenario_id="B-DOES-NOT-EXIST", selected=True)

    scenario, note = select_primary_scenario(accepted, config)
    assert scenario is accepted[0]
    assert "is not among this report's accepted scenarios" in note

    assert "is not among this report" in render_html_report(approved, accepted, config=config)
    assert "is not among this report" in vector_text(build_fallback_pdf(approved, accepted, config=config))


def test_configured_revision_mismatch_is_stated(approved):
    accepted = approved.exportable()
    target = accepted[0]
    config = ExperimentConfig(scenario_id=target.id, scenario_revision=target.revision + 5, selected=True)

    scenario, note = select_primary_scenario(accepted, config)
    assert scenario is target
    assert f"revision {target.revision + 5}" in note
    assert "uses the accepted revision" in note


# --------------------------------------------------------------------------------------
# The configuration is stated in the output
# --------------------------------------------------------------------------------------

def test_both_paths_state_the_configuration(approved):
    accepted = approved.exportable()
    config = ExperimentConfig(initial_pct=0.60, conservation_pct=0.20, pipeline_active=False,
                              scenario_id=accepted[0].id, scenario_revision=accepted[0].revision, selected=True)

    html = render_html_report(approved, accepted, config=config)
    text = vector_text(build_fallback_pdf(approved, accepted, config=config))
    for label, value in config.describe_rows():
        assert label in html, label
        assert value in html, value
        assert label.upper() in text.upper(), label
        assert value in text, value


def test_configuration_sits_on_the_first_page(approved):
    """Kept compact and on page one: a full table here pushed the brief to three pages."""
    html = render_html_report(approved, approved.exportable())
    summary_at = html.index("Experiment configuration:")
    assert summary_at < html.index('<div class="page-break">')
    # One line, not a table of its own.
    assert "Experiment Configuration Used For This Report" not in html


def test_default_report_says_it_is_a_default_not_an_earlier_run(approved):
    accepted = approved.exportable()
    html = render_html_report(approved, accepted)
    text = vector_text(build_fallback_pdf(approved, accepted))

    assert "No experiment was configured in Review" in html
    assert "not a record of an earlier run" in html
    assert "No experiment was configured in Review" in text

    chosen = ExperimentConfig(selected=True, scenario_id=accepted[0].id, scenario_revision=accepted[0].revision)
    assert "No experiment was configured in Review" not in render_html_report(approved, accepted, config=chosen)


# --------------------------------------------------------------------------------------
# Stale reports cannot remain available
# --------------------------------------------------------------------------------------

def test_token_changes_when_any_relevant_input_changes(approved):
    accepted = approved.exportable()
    base = report_state_token(approved.id, accepted, False, False, ExperimentConfig())

    assert report_state_token(approved.id, accepted, False, False, ExperimentConfig()) == base

    variations = {
        "notes consent": report_state_token(approved.id, accepted, True, False, ExperimentConfig()),
        "custom consent": report_state_token(approved.id, accepted, False, True, ExperimentConfig()),
        "initial storage": report_state_token(approved.id, accepted, False, False, ExperimentConfig(initial_pct=0.60)),
        "conservation": report_state_token(approved.id, accepted, False, False, ExperimentConfig(conservation_pct=0.30)),
        "pipeline": report_state_token(approved.id, accepted, False, False, ExperimentConfig(pipeline_active=False)),
        "tiers": report_state_token(approved.id, accepted, False, False, ExperimentConfig(tiers=(1.0, 0.5))),
        "scenario": report_state_token(approved.id, accepted, False, False, ExperimentConfig(scenario_id=accepted[0].id)),
        "selected flag": report_state_token(approved.id, accepted, False, False, ExperimentConfig(selected=True)),
        "accepted set": report_state_token(approved.id, accepted[:1], False, False, ExperimentConfig()),
        "workspace": report_state_token("other-workspace", accepted, False, False, ExperimentConfig()),
    }
    for label, token in variations.items():
        assert token != base, label


def test_token_changes_when_a_scenario_revision_changes(approved):
    accepted = approved.exportable()
    before = report_state_token(approved.id, accepted, False, False, ExperimentConfig())

    target = accepted[0]
    approved.edit(target.id, "Scaled for stale-report test", factor=0.8)
    after = report_state_token(approved.id, [approved.get(target.id)], False, False, ExperimentConfig())
    assert after != before


def test_generated_reports_differ_whenever_the_token_differs(approved):
    """A changed token must correspond to genuinely different report bytes."""
    accepted = approved.exportable()
    default_config = ExperimentConfig()
    changed_config = ExperimentConfig(initial_pct=0.35, conservation_pct=0.30, selected=True)

    assert report_state_token(approved.id, accepted, False, False, default_config) != \
        report_state_token(approved.id, accepted, False, False, changed_config)
    assert generate_pdf_report(approved, accepted, config=default_config) != \
        generate_pdf_report(approved, accepted, config=changed_config)


# --------------------------------------------------------------------------------------
# Privacy controls survive the change
# --------------------------------------------------------------------------------------

def test_note_consent_still_gates_output_with_a_configuration(approved):
    for identifier in approved.selected:
        approved.get(identifier).review(True, "PRIVATE-SENTINEL")
    accepted = approved.exportable()
    config = ExperimentConfig(initial_pct=0.35, selected=True)

    assert "PRIVATE-SENTINEL" not in render_html_report(approved, accepted, config=config)
    assert "PRIVATE-SENTINEL" in render_html_report(approved, accepted, include_notes=True, config=config)
    assert b"PRIVATE-SENTINEL" not in build_fallback_pdf(approved, accepted, config=config)
    assert b"PRIVATE-SENTINEL" in build_fallback_pdf(approved, accepted, include_notes=True, config=config)


def test_pdf_still_disclaims_the_bundle_verification_contract(approved):
    accepted = approved.exportable()
    config = ExperimentConfig(initial_pct=0.60, selected=True)

    html = render_html_report(approved, accepted, config=config)
    text = vector_text(build_fallback_pdf(approved, accepted, config=config))
    assert "this PDF is outside that contract" in html
    assert "outside the bundle verification contract" in text
    assert "PDF NOT VERIFIED" in text


def test_configuration_does_not_alter_rainfall_features(approved):
    """Experiment settings must not touch the rainfall numbers themselves."""
    accepted = approved.exportable()
    before = [(s.id, s.revision, dict(s.features)) for s in accepted]

    render_html_report(approved, accepted, config=ExperimentConfig(initial_pct=0.60, conservation_pct=0.30))
    build_fallback_pdf(approved, accepted, config=ExperimentConfig(initial_pct=0.35, pipeline_active=False))

    after = [(s.id, s.revision, dict(s.features)) for s in approved.exportable()]
    assert after == before


def test_series_are_not_mutated_by_tier_scaling(approved):
    accepted = approved.exportable()
    original = accepted[0].series.copy(deep=True)
    render_html_report(approved, accepted, config=ExperimentConfig(tiers=(1.0, 0.4)))
    pd.testing.assert_frame_equal(accepted[0].series, original)
