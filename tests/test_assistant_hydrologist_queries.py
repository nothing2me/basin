"""Comprehensive test battery for the BASIN Analyst Assistant.

Validates hydrologist, water resource engineer, and rural water council queries:
- Easy queries: Run / shortlist summaries, worst/top scenario auto-identification, provenance.
- Tough queries: Comparative ranking breakdowns, 35% storage threshold, dead pool / 75k ac-ft reserve,
  Mary Rhodes Pipeline 72 MGD external buffer, K-Means clustering diversity vs. top-deficit clones.
- Real-world council queries: Rural utility drought guidance, scenario vs. forecast boundary,
  rainfall deficit (mm) vs. reservoir storage (ac-ft) runoff gap, summer lake evaporation.
- Invariants & guardrails: Invariant clarification requirements, non-predictive calendar breach refusal,
  policy governance advisory.
- Conversational flow: History tracking via run_assistant().
"""
import pytest
from basin_core.assistant import run_assistant, semantic_query_route


def test_assistant_scenarios_just_run_summary(workspace):
    """Assert queries asking about scenarios just run or shortlist return the comprehensive run overview."""
    queries = [
        "Tell me about the scenarios ive just run",
        "Tell me about the scenarios I've just run",
        "Summarize my scenarios",
        "What scenarios did I run?",
        "Give me an overview of the run",
        "Summarize my shortlist",
        "Show my scenarios",
    ]
    for q in queries:
        reply = semantic_query_route(workspace, q)
        assert "Workspace Run & Shortlist Overview" in reply
        assert "candidates" in reply
        assert "shortlisted" in reply
        assert "Key Run Findings" in reply
        assert "Peak Rainfall Shortfall" in reply
        assert "Longest Multi-Season Drought" in reply
        # Verify shortlisted scenario IDs are present in the summary table
        for sid in workspace.selected:
            assert sid in reply


def test_assistant_worst_and_top_scenario_resolution(workspace):
    """Assert queries asking for the worst or top scenario auto-identify the relevant candidate."""
    worst_reply = semantic_query_route(workspace, "What is the worst scenario?")
    assert "Worst Scenario by Deficit" in worst_reply
    assert "shortfall" in worst_reply
    # Verify the scenario profile is rendered
    assert "Duration" in worst_reply
    assert "Station suitability is provisional" in worst_reply

    longest_reply = semantic_query_route(workspace, "Which scenario is the longest?")
    assert "Longest Drought Scenario" in longest_reply
    assert "days duration" in longest_reply

    top_reply = semantic_query_route(workspace, "What is the top ranked scenario?")
    assert "Top-Ranked Scenario" in top_reply
    assert workspace.selected[0] in top_reply


def test_assistant_comparative_ranking_breakdown(workspace):
    """Assert queries asking why scenario A outranked scenario B return side-by-side component scores."""
    s1, s2 = workspace.selected[0], workspace.selected[1]
    query = f"Why did {s1} rank higher than {s2}?"
    reply = semantic_query_route(workspace, query)
    assert f"Ranking Comparison: {s1} vs {s2}" in reply
    assert "Priority Component" in reply
    assert "Severity" in reply
    assert "Duration" in reply
    assert "Concurrence" in reply
    assert "Seasonality" in reply
    assert f"Why {s1} ranked higher than {s2}" in reply
    assert "active ranking weights" in reply


def test_assistant_compare_top_two_without_explicit_ids(workspace):
    """Assert queries asking to compare the top two auto-resolve to workspace.selected[:2]."""
    reply = semantic_query_route(workspace, "Compare the top two scenarios")
    assert "Scenario comparison" in reply
    assert workspace.selected[0] in reply
    assert workspace.selected[1] in reply


def test_assistant_concurrence_concept_faq(workspace):
    """Assert queries asking what concurrence means explain the hydrologic principle in plain English."""
    queries = [
        "What does concurrence mean in plain English?",
        "What is station stress concurrence?",
        "Explain concurrence",
        "Why is concurrence important?",
    ]
    for q in queries:
        reply = semantic_query_route(workspace, q)
        assert "Multi-Station Concurrence & Regional Stress" in reply
        assert "75th-percentile rolling deficit" in reply
        assert "Local storm gaps vs. Systemic drought" in reply
        assert "Rural council impact" in reply


def test_assistant_35_percent_storage_threshold_faq(workspace):
    """Assert queries asking about the 35% storage threshold explain Stage 3 critical shortage."""
    queries = [
        "What happens at 35% storage?",
        "Why is 35% storage critical?",
        "Explain the 35% threshold",
        "What is Stage 3 critical shortage?",
    ]
    for q in queries:
        reply = semantic_query_route(workspace, q)
        assert "35% Combined Storage Threshold" in reply
        assert "Stage 3: Critical Water Shortage" in reply
        assert "Mandatory Retail Curtailment" in reply
        assert "Wholesale Customer Reductions" in reply


def test_assistant_dead_pool_and_75k_reserve_faq(workspace):
    """Assert queries asking about dead pool explain the 75,000 ac-ft reserve and cavitation hazards."""
    queries = [
        "What is dead pool or inactive storage?",
        "Why does BASIN reserve 75,000 acre-feet?",
        "Explain pump cavitation and dead storage",
    ]
    for q in queries:
        reply = semantic_query_route(workspace, q)
        assert "Inactive Storage (Dead Pool) & 75,000 ac-ft Reserve" in reply
        assert "Choke Canyon Reservoir" in reply
        assert "Lake Corpus Christi" in reply
        assert "75,000 ac-ft" in reply
        assert "pump impeller cavitation" in reply


def test_assistant_mary_rhodes_pipeline_faq(workspace):
    """Assert queries asking about the Mary Rhodes Pipeline explain the 72 MGD external buffer."""
    queries = [
        "What is the Mary Rhodes Pipeline?",
        "How does the pipeline buffer reservoir drought?",
        "What happens if Mary Rhodes Pipeline is shut down?",
    ]
    for q in queries:
        reply = semantic_query_route(workspace, q)
        assert "Mary Rhodes Pipeline (72 MGD External Supply Buffer)" in reply
        assert "Lake Texana" in reply
        assert "72 million gallons per day" in reply
        assert "Reservoir Sparing" in reply


def test_assistant_kmeans_clustering_vs_clones_faq(workspace):
    """Assert queries asking why K-Means is used explain the clone problem and profile diversity."""
    queries = [
        "Why use K-Means clustering instead of just picking the top 6 deficits?",
        "Why cluster scenarios?",
        "Explain the clone problem in drought screening",
    ]
    for q in queries:
        reply = semantic_query_route(workspace, q)
        assert "K-Means Diversity vs. Top-Deficit Clones" in reply
        assert "the clone problem" in reply
        assert "5-Dimensional Feature Clustering" in reply
        assert "Representative Shortlist" in reply


def test_assistant_rural_council_drought_preparedness(workspace):
    """Assert queries asking for rural council or small utility advice return actionable guidance."""
    queries = [
        "What should rural councils prepare for based on these results?",
        "What advice do you have for small water utilities?",
        "How should rural water boards use this data?",
    ]
    for q in queries:
        reply = semantic_query_route(workspace, q)
        assert "Drought Preparedness for Rural Councils & Small Utilities" in reply
        assert "Watch Multi-Station Concurrence" in reply
        assert "Audit Wholesale Water Contracts" in reply
        assert "Inspect & Exercise Auxiliary Groundwater" in reply
        assert "Implement Tiered Demand Management Early" in reply


def test_assistant_scenario_vs_forecast_scientific_boundary(workspace):
    """Assert queries asking about forecasts clarify the boundary between scenarios and predictions."""
    queries = [
        "Is this a forecast?",
        "What is the difference between a scenario and a forecast?",
        "Can BASIN predict rainfall?",
    ]
    for q in queries:
        reply = semantic_query_route(workspace, q)
        assert "Synthetic Scenarios vs. Predictive Forecasts" in reply
        assert "Weather Forecasts (Predictive)" in reply
        assert "Drought Scenarios (Stress-Testing)" in reply


def test_assistant_deficit_mm_vs_reservoir_volume_acft(workspace):
    """Assert queries asking about deficit in mm vs volume in acre-feet explain runoff coefficients."""
    queries = [
        "Why is rainfall deficit measured in mm instead of acre-feet?",
        "How does mm deficit relate to reservoir acre-feet?",
        "Explain runoff coefficient in drought",
    ]
    for q in queries:
        reply = semantic_query_route(workspace, q)
        assert "Station Deficit (mm) vs. Reservoir Volume (ac-ft)" in reply
        assert "Point Rainfall Deficit" in reply
        assert "Reservoir Inflow (acre-feet)" in reply
        assert "The Runoff Disconnect" in reply
        assert "runoff coefficient" in reply


def test_assistant_summer_evaporation_compounding(workspace):
    """Assert queries asking about summer drought explain gross lake evaporation and demand surges."""
    queries = [
        "How does summer evaporation affect reservoir drawdown?",
        "Why are summer droughts worse?",
        "Explain summer onset in South Texas",
    ]
    for q in queries:
        reply = semantic_query_route(workspace, q)
        assert "Summer Onset & Evaporation Compounding" in reply
        assert "Gross Lake Evaporation" in reply
        assert "60 and 70 inches per year" in reply
        assert "Coincident Peak Demand" in reply


def test_assistant_unspecified_reservoir_survival_auto_resolves_top_scenario(workspace):
    """Assert queries asking about water system survival without an ID auto-resolve to the top scenario."""
    reply = semantic_query_route(workspace, "Can our water system survive if rainfall is 20% lower?")
    assert "Reservoir Infrastructure Stress Test" in reply
    assert "Lowest point reached" in reply


def test_assistant_invariant_clarifications_preserved(workspace):
    """Assert that bare queries without required entities strictly demand clarification."""
    # Bare compare scenarios without 'top two' or specific IDs must ask for IDs
    r_comp = semantic_query_route(workspace, "Compare scenarios")
    assert "Please clarify" in r_comp
    assert "name 2 scenario IDs to compare" in r_comp

    # Bare station stress without explanation keyword must ask for scenario ID
    r_stress = semantic_query_route(workspace, "What is the station stress?")
    assert "Please clarify" in r_stress
    assert "name a scenario ID to analyse station stress" in r_stress

    # Bare sensitivity without changes must ask for weight values
    r_sens = semantic_query_route(workspace, "Sensitivity of weights")
    assert "Please clarify" in r_sens
    assert "say which weight to change" in r_sens


def test_assistant_conversational_history_flow(workspace):
    """Assert that run_assistant maintains chat history and handles sequential user questions."""
    history = []
    # Turn 1: Ask about scenarios run
    reply_1, history = run_assistant(workspace, "Tell me about the scenarios ive just run", history, use_qwen=False)
    assert "Workspace Run & Shortlist Overview" in reply_1
    assert len(history) == 2
    assert history[0]["role"] == "user"
    assert history[1]["role"] == "assistant"

    # Turn 2: Follow-up question on concurrence
    reply_2, history = run_assistant(workspace, "What does concurrence mean in plain English?", history, use_qwen=False)
    assert "Multi-Station Concurrence & Regional Stress" in reply_2
    assert len(history) == 4
    assert history[2]["role"] == "user"
    assert history[3]["role"] == "assistant"
