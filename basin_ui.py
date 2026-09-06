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
                      "Deficit and rainfall construction": "rainfall-method", "Reference percentile and station stress": "matched-reference",
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
                                    "Station stress fraction": round(f["concurrence"], 3), "Reference sample n": f["benchmark_n"],
                                    "Reference percentile": round(f["historical_percentile"], 3),
                                    "Score": round(s.score, 2), "Revision": s.revision, "Status": s.status,
                                    "Selection reason": w.selection_reason(identifier),
                                    **{f"Score: {k}": round(v, 2) for k, v in s.components.items()}}
            st.dataframe(pd.DataFrame(rows), width="stretch")
            st.caption("Profile names describe feature patterns. With one station, concurrence means that station's stress frequency. Approval concerns rainfall content; it does not endorse later priority settings.")
        else:
            st.info("Select two or three candidates to compare their measurements and review state.")
        st.write("Preview alternative priorities on the same candidate pool")
        columns = st.columns(4)
        weights = {k: col.slider(k.title() + " alternative", 0, 100, int(w.weights[k]), key=f"alt_{w.id}_{k}")
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
