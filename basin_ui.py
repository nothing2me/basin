"""Evidence and comparison views consuming the Workspace contract."""
from html import escape as html_escape
from pathlib import Path
import uuid

import pandas as pd
import streamlit as st

from basin_core.evidence import KINDS, STATUSES

import base64
_DIAMOND_AVATAR_PATH = Path(__file__).resolve().parent / "assets" / "basin_avatar_diamond.png"
_DIAMOND_AVATAR_B64 = (
    base64.b64encode(_DIAMOND_AVATAR_PATH.read_bytes()).decode("ascii")
    if _DIAMOND_AVATAR_PATH.exists()
    else ""
)


def evidence_panel(w, scenario, save):
    key = f"{w.id}_{scenario.id}"
    registry = {e["id"]: e for e in w.evidence}
    attached = w.evidence_refs[scenario.id]
    st.subheader("Evidence and assumptions")
    metric_sources = {"Observed rainfall": "noaa-snapshot", "Station suitability": "station-suitability",
                      "Deficit and rainfall construction": "rainfall-method", "How unusual vs history and station stress": "matched-reference",
                      "Ranking weights": "ranking-assumption"}
    metric = st.selectbox("Trace a metric or assumption", list(metric_sources), key=f"trace_{key}")
    source = registry[metric_sources[metric]]
    st.write(source["description"])
    st.caption(f"{source['title']} · {source['source_locator']} · {source['review_status']}")
    st.dataframe(pd.DataFrame([registry[i] for i in attached]).drop(columns="private_note", errors="ignore"),
                 hide_index=True, width="stretch")
    st.caption("Evidence applicability is qualitative; no automatic trust score is applied.")
    with st.expander("Record disagreement / conflict between evidence records", expanded=False):
        left, right = st.columns(2)
        first = left.selectbox("First evidence", list(registry), format_func=lambda i: registry[i]["title"], key=f"evidence_left_{key}")
        second = right.selectbox("Second evidence", list(registry), index=min(1, len(registry)-1),
                                 format_func=lambda i: registry[i]["title"], key=f"evidence_right_{key}")
        for column, identifier in ((left, first), (right, second)):
            e = registry[identifier]
            with column:
                st.write(e["title"])
                st.caption(f"{e['kind']} · {e['review_status']}")
                st.write({"Publisher": e["publisher"], "Source": e["source_locator"], "Source date": e["source_date"] or "Not supplied",
                          "Retrieved": e["retrieved_at"] or "Not supplied", "Geography": e["geographic_scope"], "Units": e["units"] or "Not applicable"})
                st.write(e["description"])
        with st.form(f"conflict_form_{key}"):
            st.write("Record a disagreement between the two records above")
            disagreement = st.text_input("Public disagreement", key=f"disagreement_{key}")
            comparability = st.text_input("Public comparability limits (dates, definitions, units, geography)", key=f"comparability_{key}")
            private = st.text_input("Private conflict annotation (excluded by default)", key=f"conflict_private_{key}")
            add = st.form_submit_button("Record unresolved disagreement")
        if add:
            try:
                w.add_conflict(first, second, disagreement, comparability, private)
                if save(w):
                    st.rerun()
            except ValueError as error:
                st.error(str(error))
    if w.conflicts:
        with st.expander("Conflict dispositions", expanded=True):
            identifier = st.selectbox("Recorded conflict", [c["id"] for c in w.conflicts], key=f"conflict_id_{key}")
            conflict = next(c for c in w.conflicts if c["id"] == identifier)
            st.write({k: v for k, v in conflict.items() if k != "private_note"})
            with st.form(f"resolve_{key}_{identifier}"):
                resolution = st.text_area("Public human disposition", value=conflict["resolution"])
                resolved = st.checkbox("Mark resolved for this exercise", value=conflict["status"] == "resolved")
                resolve = st.form_submit_button("Save disposition")
            if resolve:
                try:
                    w.resolve_conflict(identifier, resolution, resolved)
                    if save(w): st.success("Disposition saved with the previous state in the audit history.")
                except ValueError as error:
                    st.error(str(error))
    with st.expander("Add a cited evidence or assumption record"):
        with st.form(f"evidence_form_{key}"):
            title = st.text_input("Evidence title")
            publisher = st.text_input("Publisher or assumption author")
            locator = st.text_input("Source URL or docs/*.md reference")
            source_date = st.text_input("Source date/version date (blank if unknown)")
            retrieved = st.text_input("Retrieval date (blank if not applicable)")
            geography = st.text_input("Applicable geography")
            units = st.text_input("Quantity and units (blank if not applicable)")
            kind = st.selectbox("Evidence type", KINDS)
            status = st.selectbox("Applicability review status", STATUSES)
            description = st.text_area("Public description or short excerpt")
            private_note = st.text_area("Private evidence annotation (excluded by default)")
            submit = st.form_submit_button("Add evidence to this scenario")
        if submit:
            record = {"id": "evidence-" + uuid.uuid4().hex[:12], "title": title, "publisher": publisher,
                      "source_locator": locator, "source_date": source_date, "retrieved_at": retrieved,
                      "geographic_scope": geography, "units": units, "kind": kind, "review_status": status,
                      "description": description, "private_note": private_note}
            try:
                w.add_evidence(record, [scenario.id])
                if save(w):
                    st.rerun()
            except ValueError as error:
                st.error(str(error))


def comparison_panel(w, save):
    with st.expander("Compare scenarios and priorities", expanded=False):
        ids = st.multiselect("Compare two or three candidates", [s.id for s in w.scenarios],
                             default=w.selected[:3], max_selections=3, key=f"compare_ids_{w.id}")
        if len(ids) >= 2:
            rows = {}
            for identifier in ids:
                s = w.get(identifier)
                f = s.features
                rows[identifier] = {"Source dates": f"{s.provenance['source_start']} to {s.provenance['source_end']}",
                                    "Days": f["duration_days"], "Deficit mm/station": round(f["deficit_mm"], 2),
                                    "Stations stressed together": round(f["concurrence"], 3), "Reference sample n": f["benchmark_n"],
                                    "How unusual vs history": round(f["historical_percentile"], 3),
                                    "Score": round(s.score, 2), "Revision": s.revision, "Status": s.status,
                                    "Why this scenario ranked here": w.selection_reason(identifier),
                                    **{f"Ranking contribution: {k}": round(v, 2) for k, v in s.components.items()}}
            st.dataframe(pd.DataFrame(rows), width="stretch")
            st.caption("Approval covers rainfall content, not later priority weights.")
        else:
            st.info("Select two or three candidates to compare their measurements and review state.")
        st.write("Preview alternative priorities on the same candidate pool")
        columns = st.columns(4)
        weight_labels = {"severity": "How unusual vs history", "duration": "Longer scenarios",
                         "concurrence": "Stations stressed together", "season": "June–September timing"}
        weights = {k: col.slider(weight_labels[k] + " alternative", 0, 100, int(w.weights[k]), key=f"alt_{w.id}_{k}")
                   for col, k in zip(columns, w.weights)}
        if sum(weights.values()) > 0 and any(s.status != "rejected" for s in w.scenarios):
            result = w.compare_weights(weights)
            st.dataframe(pd.DataFrame(result["rows"]), hide_index=True, height=260, width="stretch")
            st.caption("Live weight preview; candidates and review status stay unchanged.")
            if st.button("Save comparison to audit", key=f"save_comparison_{w.id}"):
                w.compare_weights(weights, save_result=True)
                if save(w): st.success("Comparison saved with candidate revisions, rainfall digests and both weight configurations.")
        else:
            st.info("Use at least one positive weight and an eligible candidate.")

def fallback_query_route(w, prompt: str) -> str:
    """Deterministic routing to tools, shared with the assistant.

    One router means one interpretation of percentages, years, scenario IDs, stations,
    groups and weights; this copy previously diverged and substituted defaults silently.
    """
    from basin_core.assistant import semantic_query_route
    try:
        return semantic_query_route(w, prompt)
    except (ValueError, KeyError, TypeError) as error:
        return "⚠️ **Analysis Boundary**: Please clarify the requested analysis: " + str(error)


DIRECT_TOOLS_NEEDING_INPUT = frozenset({"query_rainfall", "find_scenarios_by_year", "run_sensitivity",
                                        "test_reservoir_infrastructure", "run_stress_spectrum"})


def direct_tool_arguments(w, tool_name: str):
    """Arguments for the input-free Direct Tool Runner, and a description of what was chosen.

    Returns None for tools whose meaning depends on a user-chosen station, dates, year,
    weights or experiment settings: those are never filled with invented values.
    """
    if tool_name in DIRECT_TOOLS_NEEDING_INPUT:
        return None
    sid = w.selected[0] if w.selected else w.scenarios[0].id
    if tool_name in ("describe_scenario", "explain_ranking", "check_concurrence", "summarize_evidence"):
        return {"scenario_id": sid}, f" for {sid} (first shortlisted scenario)"
    if tool_name == "compare_scenarios":
        id1 = w.selected[0] if w.selected else w.scenarios[0].id
        id2 = w.selected[1] if len(w.selected) > 1 else (w.scenarios[1].id if len(w.scenarios) > 1 else id1)
        return {"scenario_id_1": id1, "scenario_id_2": id2}, f" for {id1} and {id2} (first two shortlisted scenarios)"
    if tool_name == "describe_cluster":
        group = min(s.cluster for s in w.scenarios)
        return {"cluster_id": group}, f" for group {group} (lowest group number)"
    return {}, ""


@st.cache_resource(show_spinner=False)
def _get_cached_assistant_workspace(_source, station_ids_tuple):
    from basin_core.engine import ScenarioParams
    from basin_core.workspace import Workspace
    params = ScenarioParams(station_ids_tuple, (90, 180, 270), (1, 4, 7, 10), 0.35, 0.85, "All stations", 300, 22)
    return Workspace(_source, params, 6)


def _open_assistant_panel():
    st.session_state.assistant_open = True


def _close_assistant_panel():
    st.session_state.assistant_open = False


def _queue_assistant_query():
    query = st.session_state.get("assistant_chat_input")
    if query:
        st.session_state.assistant_pending_query = query
    st.session_state.assistant_open = True


def _clear_assistant_chat():
    st.session_state.assistant_messages = []
    st.session_state.assistant_history = []
    st.session_state.assistant_open = True


def assistant_panel(w, source=None, names=None):
    """Render the workspace-grounded analyst drawer."""
    from basin_core.assistant import run_assistant, run_tool_directly
    from basin_core.tools import TOOL_REGISTRY
    from basin_core.qwen_runtime import get_model_info, get_qwen_client

    st.session_state.setdefault("assistant_open", False)
    st.session_state.setdefault("assistant_messages", [])
    st.session_state.setdefault("assistant_history", [])

    is_open = st.session_state.assistant_open
    tab_class = "assistant_tab_open" if is_open else "assistant_tab_closed"
    tab_label = "Close" if is_open else "Assistant"
    tab_key = "assistant_close_tab_btn" if is_open else "assistant_open_tab_btn"
    tab_action = _close_assistant_panel if is_open else _open_assistant_panel

    with st.container(key=tab_class):
        st.button(
            tab_label,
            key=tab_key,
            help="Toggle BASIN AI Assistant",
            on_click=tab_action,
        )

    if is_open:
        st.html("<script>document.body.classList.add('basin-assistant-open');</script>", unsafe_allow_javascript=True)
    else:
        st.html("<script>document.body.classList.remove('basin-assistant-open');</script>", unsafe_allow_javascript=True)

    if w is None:
        if source is not None:
            station_ids = tuple(names.keys()) if names else tuple(source.daily.columns)
            w = _get_cached_assistant_workspace(source, station_ids)

    if w is None:
        return

    with st.container(key="assistant_drawer"):
        model_info = get_model_info()
        client = get_qwen_client()
        status = client.status
        if status == "ready":
            status_label = "Ready"
            status_detail = f'Uses this workspace’s data · Local model {model_info["quantization"]}'
        elif status == "model_missing":
            status_label = "Ready"
            status_detail = "Uses this workspace’s data · Deterministic tools"
        elif status == "loading":
            status_label = "Preparing local model"
            status_detail = "Workspace tools remain available"
        elif status == "crashed":
            status_label = "Ready with fallback"
            status_detail = "Uses this workspace’s deterministic tools"
        else:
            status_label = "Ready"
            status_detail = "Uses this workspace’s deterministic tools"

        avatar_path = _DIAMOND_AVATAR_PATH
        avatar_b64 = _DIAMOND_AVATAR_B64

        avatar_html = (
            f'<img src="data:image/png;base64,{avatar_b64}" class="basin-assistant-header-avatar" alt="BASIN AI" />'
            if avatar_b64
            else ''
        )
        st.markdown(
            '<div class="basin-assistant-header">'
            '<div style="display:flex;align-items:center;gap:12px;">'
            f'{avatar_html}'
            '<div>'
            '<div class="basin-assistant-title" style="margin:0;">Analyst Assistant</div>'
            '<div class="basin-assistant-status" role="status">'
            '<span class="basin-assistant-status-dot" aria-hidden="true"></span>'
            f'<span><strong>{html_escape(status_label)}</strong>'
            f'<small>{html_escape(status_detail)}</small></span>'
            '</div></div></div></div>',
            unsafe_allow_html=True,
        )

        pending_query = st.session_state.pop("assistant_pending_query", None)
        if pending_query:
            st.session_state.assistant_messages.append({"role": "user", "content": pending_query})
            with st.spinner("Analyzing workspace data..."):
                try:
                    import time
                    t0 = time.time()
                    reply, new_hist = run_assistant(w, pending_query, st.session_state.assistant_history)
                    dt = time.time() - t0
                    st.session_state["assistant_inference_seconds"] = st.session_state.get("assistant_inference_seconds", 0.0) + dt
                    st.session_state.assistant_history = new_hist
                    st.session_state.assistant_messages.append({"role": "assistant", "content": reply})
                except Exception as ex:
                    st.session_state.assistant_messages.append({"role": "assistant", "content": f"I could not complete that analysis: {ex}"})

        chat_box = st.container(height=520, border=True, key="assistant_conversation")
        with chat_box:
            if not st.session_state.assistant_messages:
                diamond_img = (
                    f'<img src="data:image/png;base64,{avatar_b64}" class="basin-assistant-mark" alt="BASIN Diamond Logo" />'
                    if avatar_b64
                    else '<div class="basin-assistant-mark basin-assistant-mark-fallback" role="img" aria-label="BASIN"></div>'
                )
                st.markdown(
                    f"""
                    <section class="basin-assistant-empty">
                      {diamond_img}
                      <h2>What would you like to examine?</h2>
                      <p>Ask about scenarios, rainfall, stations, or risks using your workspace data.</p>
                    </section>
                    """,
                    unsafe_allow_html=True,
                )
            for msg in st.session_state.assistant_messages:
                av = str(avatar_path) if (msg.get("role") == "assistant" and avatar_path.exists()) else None
                with st.chat_message(msg["role"], avatar=av):
                    st.markdown(msg["content"])

        direct_tool_run = None
        direct_result_added = False
        sid = w.selected[0] if w.selected else (w.scenarios[0].id if w.scenarios else "B-001")

        suggestion_bar = st.container(key="assistant_suggestions")
        with suggestion_bar:
            st.chat_input(
                "Ask about scenarios, tools, or South Texas water planning...",
                key="assistant_chat_input",
                on_submit=_queue_assistant_query,
            )
            with st.container(key="assistant_guidance_shortcuts"):
                st.markdown('<p class="basin-suggested-label basin-guidance-label">Platform &amp; Guidance Shortcuts</p>', unsafe_allow_html=True)
                help_col1, help_col2 = st.columns(2, gap="small")
                with help_col1:
                    if st.button("Other tools", key="quick_other_tools", width="stretch", help="See all independent analysis tools in BASIN"):
                        st.session_state.assistant_pending_query = "What other tools can I use besides the tutorial?"
                        st.rerun()
                with help_col2:
                    if st.button("Next step", key="quick_next_step", width="stretch", help="Get context-aware advice on what to do next"):
                        st.session_state.assistant_pending_query = "What should I do next?"
                        st.rerun()
                help_col3, help_col4 = st.columns(2, gap="small")
                with help_col3:
                    if st.button("In simple terms", key="quick_simple_terms", width="stretch", help="Plain-English explanation of BASIN"):
                        st.session_state.assistant_pending_query = "Explain what BASIN does in simple terms"
                        st.rerun()
                with help_col4:
                    if st.button("Ask custom question", key="quick_custom_q", width="stretch", help="Ask custom questions about water and drought"):
                        st.session_state.assistant_pending_query = "Can I ask a custom question about water planning?"
                        st.rerun()

            st.markdown('<p class="basin-suggested-label">Suggested questions · Scenario calculations</p>', unsafe_allow_html=True)
            quick_one, quick_two, quick_three, quick_four, quick_five, quick_six = st.columns(6, gap="small")
            with quick_one:
                if st.button("Top scenario", key="quick_top1", width="stretch", help="Explain the top-ranked scenario"):
                    direct_tool_run = ("describe_scenario", {"scenario_id": sid}, f"Tell me about scenario {sid}")
            with quick_two:
                if st.button("Compare", key="quick_compare", width="stretch", help="Compare the two highest-ranked scenarios"):
                    id1 = w.selected[0] if w.selected else sid
                    ranked_ids = [scenario.id for scenario in w.scenarios]
                    id2 = w.selected[1] if len(w.selected) > 1 else next((candidate for candidate in ranked_ids if candidate != id1), id1)
                    direct_tool_run = ("compare_scenarios", {"scenario_id_1": id1, "scenario_id_2": id2}, f"Compare scenario {id1} and {id2}")
            with quick_three:
                if st.button("Stress", key="quick_concur", width="stretch", help="Check station stress overlap"):
                    direct_tool_run = ("check_concurrence", {"scenario_id": sid}, f"Check station stress concurrence for {sid}")
            with quick_four:
                if st.button("Ranking", key="quick_ranking", width="stretch", help="Explain how the top scenario was scored"):
                    direct_tool_run = ("explain_ranking", {"scenario_id": sid}, f"Explain ranking for scenario {sid}")
            with quick_five:
                if st.button("Crop deficit", key="quick_crop_et", width="stretch", help="Estimate the crop water deficit"):
                    from basin_core.agronomics import calculate_crop_water_deficit
                    sc = w.get(sid)
                    c_res = calculate_crop_water_deficit(sc.series)
                    direct_content = f"**Crop Water Deficit ({c_res['crop_name']})**\n\n{c_res['takeaway']}\n\n| Metric | Value |\n|---|---|\n| Total Scenario Rain | {c_res['total_rain_in']:.2f} in ({c_res['total_rain_mm']:.1f} mm) |\n| Crop ET Demand | {c_res['total_etc_in']:.2f} in |\n| Net Irrigation Deficit | **{c_res['irrigation_gap_in']:.2f} in (acre-inches per acre)** |\n"
                    st.session_state.assistant_messages.append({"role": "user", "content": f"Calculate crop water deficit for {sid}"})
                    st.session_state.assistant_messages.append({"role": "assistant", "content": direct_content})
                    direct_result_added = True
            with quick_six:
                if st.button("Export", key="quick_export", width="stretch", help="Check export readiness"):
                    direct_tool_run = ("check_export_readiness", {}, "Check export readiness")

        if direct_tool_run:
            t_name, t_args, u_msg = direct_tool_run
            try:
                res = run_tool_directly(w, t_name, t_args)
                st.session_state.assistant_messages.append({"role": "user", "content": u_msg})
                st.session_state.assistant_messages.append({"role": "assistant", "content": res})
                direct_result_added = True
            except Exception as exc:
                st.session_state.assistant_messages.append({"role": "assistant", "content": f"I could not complete that calculation: {exc}"})
                direct_result_added = True

        if direct_result_added:
            st.rerun()

        with suggestion_bar:
            footer_note, footer_clear = st.columns([6, 1], gap="small", vertical_alignment="center")
            with footer_note:
                st.markdown(
                    '<p class="basin-assistant-trust">Responses use this workspace’s data and reviewed calculation tools.</p>',
                    unsafe_allow_html=True,
                )
            with footer_clear:
                if st.session_state.assistant_messages:
                    st.button(
                        "Clear",
                        key="assistant_clear_chat",
                        width="stretch",
                        help="Clear conversation",
                        on_click=_clear_assistant_chat,
                    )

        if st.session_state.get("show_assistant_developer_tools", False):
            st.markdown("**Manual calculation tools**")
            st.caption("Run a named calculation without writing a question.")
            tool_name = st.selectbox("Calculation", list(TOOL_REGISTRY.keys()), key="direct_tool_select")
            if st.button("Run calculation", key="direct_tool_run", type="primary", width="stretch"):
                try:
                    prepared = direct_tool_arguments(w, tool_name)
                    if prepared is None:
                        st.info(f"{tool_name} needs explicit inputs. Ask in the chat, naming the station and dates, year, weight values or scenario and settings.")
                    else:
                        args, described = prepared
                        tool_out = run_tool_directly(w, tool_name, args)
                        st.session_state.assistant_messages.append({"role": "user", "content": f"Run {tool_name}{described}"})
                        st.session_state.assistant_messages.append({"role": "assistant", "content": tool_out})
                        st.success("Result added to the conversation.")
                except Exception as ex:
                    st.error(f"Error running {tool_name}: {ex}")



