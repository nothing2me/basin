"""Regression coverage for diverse, honest offline answers to common site questions."""

from basin_core.assistant import semantic_query_route
from basin_ui import ASSISTANT_QUESTION_SETS


def test_common_site_questions_route_to_specific_distinct_answers(workspace):
    questions_and_headings = {
        "I'm confused regarding the map, what is it describing?": "What the Region N Map Shows",
        "Which stations are actually used in the analysis?": "Map Stations vs. Analysis Stations",
        "How do I read the monthly rainfall-departure heatmap?": "How to Read the Monthly Rainfall-Departure Heatmap",
        "How current and accurate is the bundled rainfall data?": "Data Currency and Quality",
        "Where is my work saved, and is my data private?": "What Is Saved and Shared",
        "What are BASIN's scientific limitations?": "What BASIN Can—and Cannot—Establish",
        "What do the storage bands in the reservoir chart mean?": "How to Read the Reservoir-Storage Chart",
        "How does BASIN rank and shortlist scenarios?": "How BASIN Ranks and Shortlists Scenarios",
    }

    replies = []
    for question, heading in questions_and_headings.items():
        reply = semantic_query_route(workspace, question)
        replies.append(reply)
        assert heading in reply
        assert "Welcome to BASIN: How to Explore" not in reply

    assert len(set(replies)) == len(replies)


def test_map_answer_states_what_the_map_does_not_establish(workspace):
    reply = semantic_query_route(workspace, "What is this map showing?")
    assert "geographic reference" in reply
    assert "not a live drought or reservoir-status map" in reply
    assert "does not show current water levels, rainfall, streamflow, or drought severity" in reply


def test_unmatched_questions_are_honest_and_offer_varied_followups(workspace):
    first = semantic_query_route(workspace, "Can it optimize a desalination plant?")
    second = semantic_query_route(workspace, "Can it inspect a groundwater pump?")

    assert "could not verify a specific answer" in first
    assert "will not invent" in first
    assert "could not verify a specific answer" in second
    assert first != second


def test_suggested_question_sets_rotate_and_cover_more_than_four_prompts():
    flattened = [query for group in ASSISTANT_QUESTION_SETS for _, query in group]
    assert len(ASSISTANT_QUESTION_SETS) >= 3
    assert all(len(group) == 4 for group in ASSISTANT_QUESTION_SETS)
    assert len(flattened) == len(set(flattened))
    assert len(flattened) >= 12
