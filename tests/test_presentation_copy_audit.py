"""Automated verification of the user-visible copy replacement inventory for app.py and basin_ui.py.

This audit catalogues user-visible text that creates cognitive clutter, competing
explanations, or negative framing, and specifies concrete concise replacements along
with target placements (tooltip, expander, or Advanced View).
"""
from __future__ import annotations

from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[1]

# Concrete replacement inventory
COPY_REPLACEMENT_INVENTORY: list[dict[str, str]] = [
    {
        "location": "app.py:1241",
        "context": "Scenario Builder focus header caption",
        "current_wording": "Configures which visuals and tools appear first in Review. Does not change numerical calculations or export consent.",
        "proposed_concise_wording": "Choose what to focus on first. Does not affect calculations or export.",
        "reason": "Reduces cognitive burden prior to generation; secondary disclaimers are moved to a tooltip.",
        "target_placement": "tooltip",
    },
    {
        "location": "app.py:1252",
        "context": "Guidance question label & help",
        "current_wording": "How much guidance do you want? Guided explanations add orientation; all scientific limitations remain visible in either mode.",
        "proposed_concise_wording": "Presentation View (Simple View / Advanced View).",
        "reason": "Avoids framing presentation choice as user competence; makes Simple vs Advanced a direct view choice.",
        "target_placement": "tooltip",
    },
    {
        "location": "app.py:1284",
        "context": "Scenario Builder rainfall retention slider help",
        "current_wording": "Percentage of observed rainfall used by the scenario (e.g. 70% retained = 30% reduction from observed rainfall). Multiplies observed daily rainfall at affected stations.",
        "proposed_concise_wording": "Retained rainfall percentage (e.g., 70% retained = 30% reduction).",
        "reason": "Removes redundant sentence fragment explaining daily multiplication; preserves standard dual percentage format.",
        "target_placement": "tooltip",
    },
    {
        "location": "app.py:1490-1492",
        "context": "Review setup card header and caption",
        "current_wording": "Three questions decide which tools appear first. Every tool stays reachable, and none of this changes calculations, ranking weights, review decisions or export consent.",
        "proposed_concise_wording": "Review View: Simple for immediate decision or Advanced for full diagnostics.",
        "reason": "Replaces verbose defensive enumeration with concise actionable view description.",
        "target_placement": "expander",
    },
    {
        "location": "app.py:1552-1553",
        "context": "Review focus custom data intent reminder",
        "current_wording": "Your focus records an intent to use your own rainfall data. Nothing has been uploaded or validated by that choice; add a CSV in Step 1: Data Dashboard.",
        "proposed_concise_wording": "Note: Focus set for custom data. Upload and validate a CSV in Data Dashboard.",
        "reason": "Avoids defensive paragraph before tabs; short reminder directs user to appropriate step.",
        "target_placement": "tooltip",
    },
    {
        "location": "app.py:1556-1557",
        "context": "Review focus weight preset advisory caption",
        "current_wording": "This focus often pairs with the ranking preset. Ranking weights are not changed by your focus; apply a preset yourself in Step 2: Scenario Builder if you want it.",
        "proposed_concise_wording": "Tip: Pairs well with the suggested ranking preset in Step 2.",
        "reason": "Eliminates repetitive multi-sentence disclaimer regarding unapplied weights.",
        "target_placement": "tooltip",
    },
    {
        "location": "app.py:1680",
        "context": "Review storage experiment container caption",
        "current_wording": "Optional experiment. These settings affect storage exploration; the handoff decision above concerns the rainfall revision.",
        "proposed_concise_wording": "Optional illustrative storage experiment.",
        "reason": "Redundant disclaimer; statutory/model boundaries are already detailed in mandatory disclosures.",
        "target_placement": "tooltip",
    },
    {
        "location": "app.py:1917",
        "context": "Review agronomics tab top caption",
        "current_wording": "Cross-sector operational impacts calculated from daily scenario rainfall. Illustrative decision-support estimates based on Texas ET Network and Texas A&M Forest Service guidelines; not regulatory declarations or official crop/burn directives.",
        "proposed_concise_wording": "Decision-support estimates for crop irrigation deficit and wildfire stress.",
        "reason": "Dense multi-sentence disclaimer pushes primary visuals below fold; full citations belong in expander.",
        "target_placement": "tooltip",
    },
    {
        "location": "app.py:1964",
        "context": "Review KBDI wildfire operational takeaway disclaimer",
        "current_wording": "KBDI and crop water balance models provide exploratory scenario impacts. Official burn bans are enacted exclusively by County Commissioners Courts under Tex. Local Gov't Code § 352.081. Reservoir stages reflect illustrative operating rules, not municipal emergency orders.",
        "proposed_concise_wording": "Illustrative decision support. Official burn bans are enacted exclusively by County Commissioners Courts.",
        "reason": "Statutory code citation clutters operational decision panel; move full statutory text to Advanced View.",
        "target_placement": "advanced_only",
    },
    {
        "location": "app.py:1985",
        "context": "Review rainfall chart dashed reference line caption",
        "current_wording": "The dashed reference uses this station's 1991–2020 monthly mean daily rainfall. The scenario line includes your current edits.",
        "proposed_concise_wording": "Dashed line: 1991–2020 monthly reference mean.",
        "reason": "Shortens visual chart footnote.",
        "target_placement": "tooltip",
    },
    {
        "location": "app.py:1987",
        "context": "Review rainfall 30-day deficit axis caption",
        "current_wording": "Above zero means less rainfall than the reference over the preceding 30 days; below zero means more. The first 29 days have no complete window.",
        "proposed_concise_wording": "Positive: rainfall deficit vs 30-day reference; Negative: surplus.",
        "reason": "Converts run-on prose into clear axis interpretation guide.",
        "target_placement": "tooltip",
    },
    {
        "location": "app.py:1995",
        "context": "Review rainfall historical concurrence caption",
        "current_wording": "Each station must exceed its own historical rainfall-deficit threshold in the same window. This is a frequency over time, not a percentage of stations.",
        "proposed_concise_wording": "Concurring stress persistence frequency across eligible 30-day windows.",
        "reason": "Removes verbose explanation of what concurrence is not; defines clearly what it is.",
        "target_placement": "expander",
    },
    {
        "location": "app.py:2000",
        "context": "Review rainfall candidate ranking score caption",
        "current_wording": "This reflects your priorities; it is not a probability or an evidence-quality score.",
        "proposed_concise_wording": "Multivariate ranking score based on configured priorities.",
        "reason": "Replaces double-negative disclaimer with positive definition of the score.",
        "target_placement": "tooltip",
    },
    {
        "location": "app.py:2003",
        "context": "Review rainfall edits tab introduction",
        "current_wording": "Changing rainfall creates a revision and clears its previous acceptance. Add your reason in the review note first.",
        "proposed_concise_wording": "Edits create a new scenario revision and require review re-approval.",
        "reason": "Clear workflow invariant stated concisely.",
        "target_placement": "tooltip",
    },
    {
        "location": "basin_ui.py:25",
        "context": "Evidence panel applicability footnote",
        "current_wording": "Evidence types and applicability are declarations. No numerical trust score or automatic source winner is assigned.",
        "proposed_concise_wording": "Evidence applicability is qualitative; no automatic trust score is applied.",
        "reason": "Academic phrasing simplified for operational readers.",
        "target_placement": "tooltip",
    },
    {
        "location": "basin_ui.py:111",
        "context": "Comparison panel footnote",
        "current_wording": "Profile names describe feature patterns. With one station, concurrence means that station's stress frequency. Approval concerns rainfall content; it does not endorse later priority settings.",
        "proposed_concise_wording": "Approval confirms rainfall content validity, not downstream priority weights.",
        "reason": "Separates three conflated sentences into a direct review boundary statement.",
        "target_placement": "advanced_only",
    },
    {
        "location": "basin_ui.py:123",
        "context": "Alternative priority weights preview caption",
        "current_wording": "Rejected candidates are excluded from this preview. No candidates are regenerated and no reviews or shortlist entries change.",
        "proposed_concise_wording": "Live weight preview: candidates and review statuses remain unchanged.",
        "reason": "Eliminates repetitive negative assertions.",
        "target_placement": "tooltip",
    },
]


def test_copy_inventory_completeness():
    """Verify inventory completeness, non-empty fields, and valid placements."""
    assert len(COPY_REPLACEMENT_INVENTORY) >= 15
    valid_placements = {"tooltip", "expander", "advanced_only"}

    for item in COPY_REPLACEMENT_INVENTORY:
        assert item["location"]
        assert item["context"]
        assert item["current_wording"]
        assert item["proposed_concise_wording"]
        assert item["reason"]
        assert item["target_placement"] in valid_placements
        # Proposed text should be significantly more concise than current wording
        assert len(item["proposed_concise_wording"]) < len(item["current_wording"])


def test_copy_inventory_replacements_are_applied():
    """The audited dense phrases are replaced by their concise equivalents."""
    app_text = (ROOT / "app.py").read_text(encoding="utf-8")
    ui_text = (ROOT / "basin_ui.py").read_text(encoding="utf-8")

    replacements = [
        (app_text, "Choose what to focus on first", "Configures which visuals and tools appear first"),
        (app_text, "Presentation view", "How much guidance do you want?"),
        (app_text, "Retained rainfall percentage", "Multiplies observed daily rainfall"),
        (app_text, "Simple View supports quick decisions", "Three questions decide which tools appear first"),
        (app_text, "Custom data selected", "Your focus records an intent"),
        (app_text, "pairs well with", "Ranking weights are not changed by your focus"),
        (app_text, "Optional illustrative storage experiment", "These settings affect storage exploration"),
        (app_text, "Decision-support estimates for crop irrigation deficit", "Cross-sector operational impacts calculated"),
        (app_text, "Official burn bans are enacted by", "KBDI and crop water balance models provide"),
        (app_text, "Dashed line: 1991–2020 monthly reference mean", "monthly mean daily rainfall"),
        (app_text, "Positive: rainfall deficit", "Above zero means less rainfall"),
        (app_text, "Concurring stress frequency", "frequency over time, not a percentage"),
        (app_text, "based on the configured priorities", "It reflects your priorities"),
        (app_text, "Edits create a new scenario revision", "Changing rainfall creates a revision"),
        (ui_text, "Evidence applicability is qualitative", "Evidence types and applicability are declarations"),
        (ui_text, "Approval covers rainfall content", "Approval concerns rainfall content"),
        (ui_text, "Live weight preview", "Rejected candidates are excluded from this preview"),
    ]

    for source_text, concise, old in replacements:
        assert concise in source_text, f"Concise replacement missing: {concise!r}"
        assert old not in source_text, f"Dense wording still present: {old!r}"
