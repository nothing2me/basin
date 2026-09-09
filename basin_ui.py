"""Evidence and comparison views consuming the Workspace contract."""
import uuid

import pandas as pd
import streamlit as st

from basin_core.evidence import KINDS, STATUSES


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
    st.caption("Evidence types and applicability are declarations. No numerical trust score or automatic source winner is assigned.")
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
            if save(w): st.success("Disagreement saved; both evidence records retained.")
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
            st.caption("Profile names describe feature patterns. With one station, concurrence means that station's stress frequency. Approval concerns rainfall content; it does not endorse later priority settings.")
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
            st.caption("Rejected candidates are excluded from this preview. No candidates are regenerated and no reviews or shortlist entries change.")
            if st.button("Save comparison to audit", key=f"save_comparison_{w.id}"):
                w.compare_weights(weights, save_result=True)
                if save(w): st.success("Comparison saved with candidate revisions, rainfall digests and both weight configurations.")
        else:
            st.info("Use at least one positive weight and an eligible candidate.")


def fallback_query_route(w, prompt: str) -> str:
    """Deterministic routing to tools when Ollama is offline or as fallback."""
    import re
    from basin_core.assistant import render_tool_result, TOOL_LIST_HELP
    from basin_core.tools import (
        describe_scenario,
        compare_scenarios,
        explain_ranking,
        check_concurrence,
        run_sensitivity,
        summarize_evidence,
        describe_cluster,
        check_export_readiness,
        get_data_provenance,
    )

    p = prompt.lower().strip()

    # Adversarial & Non-Predictive Advisory Guardrails
    if any(q in p for q in ["when will water run out", "when will the reservoir run out", "will water run out", "exact date of breach", "forecast reservoir levels", "what date will"]):
        return (
            "⚠️ **Analysis Boundary (Non-Predictive Advisory)**: BASIN does not generate calendar-date forecasts "
            "or operational water-supply predictions. The bundled reservoir experiment is an illustrative, "
            "uncalibrated mass-balance sensitivity model using historical rainfall proxies, not a delivery forecast."
        )

    if any(q in p for q in ["should council", "should the city", "declare stage", "mandate stage", "should we declare"]):
        return (
            "⚠️ **Analysis Boundary (Policy Governance)**: BASIN is an analytical rainfall scenario workbench, "
            "not a regulatory decision authority. Official drought stages are declared exclusively by municipal and regional "
            "authorities pursuant to the City of Corpus Christi Drought Contingency Plan."
        )

    id_matches = re.findall(r"\b[bB]-\d+\b", prompt)
    for s in w.scenarios:
        if s.id.lower() in p and s.id not in id_matches:
            id_matches.append(s.id)

    default_id = id_matches[0] if id_matches else (w.selected[0] if w.selected else w.scenarios[0].id)

    try:
        # 1. Multi-tier stress spectrum sweep check
        if any(k in p for k in ["spectrum", "stress spectrum", "multi-tier", "tiers", "tipping point", "sweep"]):
            from basin_core.tools import run_stress_spectrum
            year = 2011
            year_match = re.search(r"\b(19\d\d|20\d\d)\b", p)
            if year_match:
                year = int(year_match.group(1))
            conservation_pct = 0.0
            cons_match = re.search(r"(\d+(?:\.\d+)?)\s*%\s*(?:conservation|mandate|cut)", p)
            if cons_match:
                conservation_pct = float(cons_match.group(1))
            res = run_stress_spectrum(w, scenario_id=default_id if id_matches else "",
                                      year=year, conservation_pct=conservation_pct)
            return render_tool_result("run_stress_spectrum", res)

        # 2. Infrastructure / Reservoir survival check
        if any(k in p for k in ["survive", "infrastructure", "reservoir", "drawdown", "capacity", "storage", "restriction"]):
            from basin_core.tools import test_reservoir_infrastructure
            year = 2011
            year_match = re.search(r"\b(19\d\d|20\d\d)\b", p)
            if year_match:
                year = int(year_match.group(1))
            reduction = 0.0
            pct_match = re.search(r"(\d+(?:\.\d+)?)\s*%\s*(?:lower|less|reduction|drier)?", p)
            if pct_match:
                reduction = float(pct_match.group(1))
            res = test_reservoir_infrastructure(w, scenario_id=default_id if id_matches else "",
                                                year=year, rainfall_reduction_pct=reduction)
            return render_tool_result("test_reservoir_infrastructure", res)

        # 3. Find scenarios by year
        year_match = re.search(r"\b(19\d\d|20\d\d)\b", p)
        if year_match and (not id_matches or any(k in p for k in ["scenarios", "find", "list", "show", "search", "events", "years"])):
            from basin_core.tools import find_scenarios_by_year
            year = int(year_match.group(1))
            res = find_scenarios_by_year(w, year=year)
            return render_tool_result("find_scenarios_by_year", res)
        elif any(k in p for k in ["recent", "modern", "years", "from 20", "from 19"]):
            from basin_core.tools import find_scenarios_by_year
            year = int(year_match.group(1)) if year_match else 2011
            res = find_scenarios_by_year(w, year=year)
            return render_tool_result("find_scenarios_by_year", res)

        if any(k in p for k in ["readiness", "export ready", "can i export", "blocker"]):
            res = check_export_readiness(w)
            return render_tool_result("check_export_readiness", res)

        if any(k in p for k in ["compare", "vs", "versus", "difference"]):
            if len(id_matches) >= 2:
                id1, id2 = id_matches[0], id_matches[1]
            elif len(w.selected) >= 2:
                id1, id2 = w.selected[0], w.selected[1]
            else:
                id1, id2 = w.scenarios[0].id, w.scenarios[1].id
            id3 = id_matches[2] if len(id_matches) >= 3 else ""
            res = compare_scenarios(w, id1, id2, id3)
            return render_tool_result("compare_scenarios", res)

        if any(k in p for k in ["stress", "concurrence", "simultaneous"]):
            res = check_concurrence(w, default_id)
            return render_tool_result("check_concurrence", res)

        if any(k in p for k in ["rank", "score", "why did", "position"]):
            res = explain_ranking(w, default_id)
            return render_tool_result("explain_ranking", res)

        if any(k in p for k in ["sensitivity", "weight", "what if", "priority"]):
            res = run_sensitivity(w)
            return render_tool_result("run_sensitivity", res)

        if any(k in p for k in ["evidence", "conflict", "source", "disagreement", "citation"]):
            res = summarize_evidence(w, default_id)
            return render_tool_result("summarize_evidence", res)

        if any(k in p for k in ["cluster", "profile", "group"]):
            cid = 0
            digit_match = re.search(r"group\s*(\d+)|cluster\s*(\d+)", p)
            if digit_match:
                cid = int(digit_match.group(1) or digit_match.group(2))
            res = describe_cluster(w, cid)
            return render_tool_result("describe_cluster", res)

        if any(k in p for k in ["provenance", "noaa", "data source", "station", "manifest", "data come from", "where does this data"]):
            res = get_data_provenance(w)
            return render_tool_result("get_data_provenance", res)

        if any(k in p for k in ["scenario", "tell me about", "profile", "deficit"]) or id_matches:
            res = describe_scenario(w, default_id)
            return render_tool_result("describe_scenario", res)

        return f"**BASIN Analyst Assistant**\n\nNo exact tool matched your query. All answers must be grounded in verified tools:\n\n{TOOL_LIST_HELP}"
    except ValueError as err:
        return f"⚠️ **Analysis Boundary**: {err}"
    except Exception as ex:
        return f"⚠️ **Query Processing Error**: {ex}"


def assistant_panel(w, source=None, names=None):
    """Render the slide-out assistant panel with right-side tab, open by default."""
    from basin_core.assistant import check_ollama, run_assistant, run_tool_directly
    from basin_core.tools import TOOL_REGISTRY

    st.session_state.setdefault("assistant_open", False)
    st.session_state.setdefault("assistant_messages", [])
    st.session_state.setdefault("assistant_history", [])

    is_open = st.session_state.assistant_open
    tab_class = "assistant_tab_open" if is_open else "assistant_tab_closed"
    tab_label = "▶ Close AI" if is_open else "◀ AI Assistant"

    with st.container(key=tab_class):
        if st.button(tab_label, key="assistant_tab_btn", help="Toggle BASIN AI Assistant"):
            st.session_state.assistant_open = not is_open
            st.rerun()

    if not is_open:
        return

    if w is None and source is not None:
        from basin_core.engine import ScenarioParams
        from basin_core.workspace import Workspace
        station_ids = list(names.keys()) if names else list(source.daily.columns)
        params = ScenarioParams(tuple(station_ids), (90, 180, 270), (1, 4, 7, 10), 0.35, 0.85, "All stations", 300, 22)
        w = Workspace(source, params, 6)

    if w is None:
        return

    with st.container(key="assistant_drawer"):
        h_col, c_col = st.columns([5, 1])
        h_col.markdown('<div class="basin-assistant-title">🤖 Analyst Assistant</div>', unsafe_allow_html=True)
        h_col.markdown('<div class="basin-assistant-sub">Deterministic calculation engine · Strict templates · Read-only queries</div>', unsafe_allow_html=True)
        if c_col.button("✕", key="assistant_close_x", help="Close Assistant"):
            st.session_state.assistant_open = False
            st.rerun()

        status = check_ollama()
        if status["available"] and status["selected"]:
            st.markdown(f'<div class="basin-assistant-badge" style="color:#009E73">● Active: {status["selected"]} (Local Ollama)</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="basin-assistant-badge" style="color:#E69F00">● Direct Tool Execution (Deterministic Local Engine)</div>', unsafe_allow_html=True)

        st.caption("Quick Queries")
        q1, q2, q3, q4 = st.columns(4)
        preset_prompt = None
        if q1.button("📋 Top #1", key="quick_top1", width="stretch", help="Profile the top-ranked scenario"):
            sid = w.selected[0] if w.selected else w.scenarios[0].id
            preset_prompt = f"Tell me about scenario {sid}"
        if q2.button("⚖️ Compare", key="quick_compare", width="stretch", help="Compare top shortlisted scenarios"):
            preset_prompt = "Compare the top shortlisted scenarios"
        if q3.button("⚡ Sens.", key="quick_sens", width="stretch", help="Test ranking weight sensitivities"):
            preset_prompt = "Run sensitivity test on ranking weights"
        if q4.button("📦 Export", key="quick_export", width="stretch", help="Check export readiness"):
            preset_prompt = "Is the workspace ready for export?"

        chat_box = st.container(height=380)
        with chat_box:
            if not st.session_state.assistant_messages:
                st.info(
                    "**Hydrologist Assistant Ready.**\n\n"
                    "Ask about scenario profiles, compare candidates, check station stress, "
                    "or test priority weights.\n\n"
                    "Every response is computed from actual workspace data."
                )
            for msg in st.session_state.assistant_messages:
                with st.chat_message(msg["role"]):
                    st.markdown(msg["content"])

        user_input = st.chat_input("Ask about scenarios, rainfall, or tests...", key="assistant_chat_input")
        active_query = preset_prompt or user_input

        if active_query:
            st.session_state.assistant_messages.append({"role": "user", "content": active_query})
            with st.spinner("Analyzing workspace data..."):
                if status["available"] and status["selected"]:
                    try:
                        reply, new_hist = run_assistant(w, active_query, st.session_state.assistant_history)
                        st.session_state.assistant_history = new_hist
                        st.session_state.assistant_messages.append({"role": "assistant", "content": reply})
                    except Exception:
                        reply = fallback_query_route(w, active_query)
                        st.session_state.assistant_messages.append({"role": "assistant", "content": reply})
                else:
                    reply = fallback_query_route(w, active_query)
                    st.session_state.assistant_messages.append({"role": "assistant", "content": reply})
            st.rerun()

        f_col1, f_col2 = st.columns([2, 1])
        if f_col2.button("Clear chat", key="assistant_clear_chat", width="stretch"):
            st.session_state.assistant_messages = []
            st.session_state.assistant_history = []
            st.rerun()

        with st.expander("🛠️ Direct Tool Runner (Manual)", expanded=False):
            st.caption("Select and execute any analysis tool directly without natural language processing.")
            tool_name = st.selectbox("Select Tool", list(TOOL_REGISTRY.keys()), key="direct_tool_select")
            if st.button("Execute Tool", key="direct_tool_run", type="primary"):
                try:
                    sid = w.selected[0] if w.selected else w.scenarios[0].id
                    if tool_name in ("describe_scenario", "explain_ranking", "check_concurrence", "summarize_evidence"):
                        args = {"scenario_id": sid}
                    elif tool_name == "compare_scenarios":
                        id1 = w.selected[0] if w.selected else w.scenarios[0].id
                        id2 = w.selected[1] if len(w.selected) > 1 else (w.scenarios[1].id if len(w.scenarios) > 1 else id1)
                        args = {"scenario_id_1": id1, "scenario_id_2": id2}
                    elif tool_name == "describe_cluster":
                        args = {"cluster_id": 0}
                    elif tool_name == "query_rainfall":
                        stn = w.source.manifest["stations"][0]["id"]
                        args = {"station_id": stn, "start_date": "2011-01-01", "end_date": "2011-12-31"}
                    else:
                        args = {}
                    tool_out = run_tool_directly(w, tool_name, args)
                    st.session_state.assistant_messages.append({"role": "user", "content": f"Run {tool_name}"})
                    st.session_state.assistant_messages.append({"role": "assistant", "content": tool_out})
                    st.rerun()
                except Exception as ex:
                    st.error(f"Error running {tool_name}: {ex}")

