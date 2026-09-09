import pytest
from basin_core import tools
from basin_ui import fallback_query_route


def test_unobserved_year_raises_value_error(workspace):
    """Assert that requesting a future or unobserved year raises an explicit ValueError
    rather than silently falling back to workspace.scenarios[0].
    """
    with pytest.raises(ValueError, match="No historical drought events found for year 2030"):
        tools.test_reservoir_infrastructure(workspace, year=2030)

    with pytest.raises(ValueError, match="No historical drought events found for year 2030"):
        tools.run_stress_spectrum(workspace, scenario_id="", year=2030)


def test_invalid_scenario_id_raises_value_error(workspace):
    """Assert that passing an invalid scenario ID raises ValueError instead of silent fallback."""
    with pytest.raises(ValueError, match="B-999"):
        tools.run_stress_spectrum(workspace, scenario_id="B-999")


def test_fallback_query_route_adversarial_year(workspace):
    """Assert that assistant natural-language queries for future years return an Analysis Boundary advisory
    rather than silently returning results computed from a 1996 event.
    """
    reply = fallback_query_route(workspace, "Simulate reservoir drawdown for the 2030 drought")
    assert "⚠️ **Analysis Boundary**" in reply
    assert "No historical drought events found for year 2030" in reply
    assert "1996" not in reply


def test_fallback_query_route_predictive_guardrails(workspace):
    """Assert that assistant refuses predictive calendar-date breach forecasting."""
    queries = [
        "When will water run out?",
        "When will the reservoir run out?",
        "What date will Choke Canyon reach empty?",
        "Forecast reservoir levels for next month",
    ]
    for q in queries:
        reply = fallback_query_route(workspace, q)
        assert "Non-Predictive Advisory" in reply
        assert "BASIN does not generate calendar-date forecasts" in reply


def test_fallback_query_route_policy_guardrails(workspace):
    """Assert that assistant refuses to issue legal or regulatory policy declarations."""
    queries = [
        "Should council declare Stage 4?",
        "Should council mandate emergency cuts?",
        "Should the city declare a drought emergency tomorrow?",
        "Should we declare Stage 3 immediately?",
    ]
    for q in queries:
        reply = fallback_query_route(workspace, q)
        assert "Policy Governance" in reply
        assert "BASIN is an analytical rainfall scenario workbench" in reply
