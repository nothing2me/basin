from __future__ import annotations

import calendar
from copy import deepcopy
import base64
from contextlib import contextmanager, nullcontext
from html import escape
from datetime import datetime, timezone, timedelta
import json

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

from basin_core.analysis import (comparison, COMMUNITY_PRESETS, RESERVOIR_ASSUMPTIONS, rainfall_tier_label,
                                 simulate_reservoir_drawdown, simulate_stress_spectrum, threshold_crossing_day,
                                 threshold_day_label, build_shortlist_scorecard, compare_demand_curtailment_policies)
from basin_core.simulation import SimulationSettings, describe_input_rainfall, observed_percent, spectrum_view
from basin_core.water_system import (WaterSource, WaterSystemConfig, SYSTEM_PRESETS,
                                     SYSTEM_ID_TO_LABEL, SYSTEM_LABEL_TO_ID, REGION_N_PRESET,
                                     DEFAULT_WATER_SYSTEM_ID)
from basin_core.summary import scenario_summary, reservoir_summary, format_rainfall_dual_explanation
from basin_core.review_preferences import (DATA_SOURCES, GOALS, GUIDANCE, GUIDED_TAB_NOTES,
                                           PRESENTATION_MODES,
                                           TAB_LABELS, ReviewPreferences, load_preferences,
                                           save_preferences)
from basin_ui import evidence_panel, comparison_panel, assistant_panel
from basin_theme import apply_design, appearance_picker, custom_appearance, accessible_chart, reveal_tour_target
from basin_core.data import CachedSource, ROOT
from basin_core.engine import ScenarioParams
from basin_core.exporter import export_bundle, verify_bundle, generate_brief, summary_record, rainfall_rows
from basin_core.pdf_report import ExperimentConfig, generate_pdf_report_with_status, report_state_token, render_html_report
from basin_core.workspace import Workspace, session_dir
from basin_core.analysis_context import (AnalysisContext, DECISION_USES, ORGANIZATION_TYPES,
                                         REGION_N_COUNTIES, SUPPLY_RELATIONSHIPS)
from basin_core.uploads import TEMPLATE, preview_rainfall
from basin_core.rainfall_comparison import compare_rainfall
from basin_core.custom_data import (active_ids, digest, format_custom_source_label,
                                    format_custom_coverage_dates, CUSTOM_CATCHMENT_DISCLAIMER)
from basin_core.document_ingestion import DOCUMENT_CATCHMENT_DISCLAIMER, DocumentState
from basin_core.visualizers import (pareto_frontier_figure, rainfall_reference_figure, rainfall_shortfall_figure,
                                    stage_trigger_milestone_figure, storage_trajectory_figure,
                                    drought_anomaly_matrix_figure,
                                    shortlist_cumulative_deficit_figure,
                                    multi_scenario_storage_figure)
from basin_core.agronomics import calculate_crop_water_deficit, calculate_kbdi, CROP_COEFFICIENTS

icon_file = ROOT / "assets/basin.ico"
st.set_page_config(page_title="BASIN", page_icon=str(icon_file) if icon_file.exists() else "◉", layout="wide", initial_sidebar_state="collapsed")
apply_design()
assistant_w = int(st.session_state.get("assistant_width", 520))
notes_h = int(st.session_state.get("notes_height", 420))
st.html(f"""<style>
:root {{
    --basin-assistant-width: {assistant_w}px;
    --basin-notes-height: {notes_h}px;
}}
</style>""")
if st.session_state.get("assistant_open", False):
    st.html(f"""<style>
    .block-container, [data-testid="stMainBlockContainer"] {{
        margin-right: {assistant_w + 10}px !important;
        max-width: calc(100% - {assistant_w + 20}px) !important;
        padding-right: 1.5rem !important;
    }}
    .st-key-assistant_drawer {{
        width: {assistant_w}px;
        min-width: 360px;
        max-width: 90vw;
        resize: horizontal;
    }}
    .st-key-assistant_tab_open {{
        right: {assistant_w}px !important;
        transition: right 0.35s cubic-bezier(0.16, 1, 0.3, 1) !important;
    }}
    body:has(.st-key-assistant_drawer) .st-key-notes_slide_drawer {{
        left: calc((100vw - {assistant_w + 10}px)/2) !important;
        transition: left 0.35s cubic-bezier(0.16, 1, 0.3, 1) !important;
    }}
    @media(max-width: 950px) {{
        .block-container, [data-testid="stMainBlockContainer"] {{
            margin-right: 0 !important;
            max-width: 100% !important;
        }}
        .st-key-assistant_drawer {{
            width: 92vw !important;
        }}
        .st-key-assistant_tab_open {{
            right: 92vw !important;
        }}
    }}
    </style>""")


@st.cache_resource
def load_source():
    return CachedSource()



def local_rainfall_preview(expanded=False, as_expander=False):
    ctx = st.expander("Upload and observe your custom CSV.", expanded=expanded) if as_expander else st.container(border=True)
    with ctx:
        st.markdown("##### 📤 Upload & Observe Custom Station CSV")
        st.caption("One station per file. Preview only: uploads do not change scenarios or the NOAA snapshot. Preview stays in this session until you explicitly save reviewed evidence to an active analysis.")
        col_t1, col_t2 = st.columns([1.5, 1.5])
        col_t1.download_button("Download CSV template", TEMPLATE, "local-rainfall-template.csv", "text/csv", width="stretch")
        station = st.text_input("Local station name", key="local_station")
        location = st.text_input("Location description", key="local_location", help="Town, area or gauge location. This does not establish catchment suitability.")
        unit = st.selectbox("Uploaded rainfall unit", ["Choose a unit", "mm", "inches"], key="local_unit")
        upload = st.file_uploader("Local observations CSV · date,precipitation", type=["csv"], key="local_rainfall_file")
        st.caption("Use YYYY-MM-DD dates. Blank rainfall means missing, not zero. Limit: 10 MB / 250,000 rows. Remove the file with the uploader's × to clear the preview.")
        if upload is None:
            return
        if unit == "Choose a unit" or not station.strip() or not location.strip():
            st.info("Enter the station, location and unit to preview this file.")
            return
        c_p1, c_p2 = st.columns(2)
        fmt_opt = c_p1.selectbox("Date format", ["ISO (YYYY-MM-DD)", "US (MM/DD/YYYY)", "Auto-detect"], index=0, key="local_date_format")
        flex_hdr = c_p2.checkbox("Flexible column names (e.g. date, rain)", value=False, key="local_flex_headers")
        chosen_fmt = "iso" if "ISO" in fmt_opt else ("us" if "US" in fmt_opt else "auto")
        try:
            preview = preview_rainfall(upload.getvalue(), station, location, unit,
                                       date_format=chosen_fmt, allow_flexible_headers=flex_hdr)
        except ValueError as error:
            st.error(str(error))
            return
        st.markdown(f"**Source: {format_custom_source_label(preview.station)}** — {preview.location}")
        st.caption(f"{format_custom_coverage_dates(preview.observations[0][0], preview.observations[-1][0], preview.valid_days)} · Input: {preview.unit}; charts: mm")
        a, b, c = st.columns(3)
        a.metric("Valid rainfall days", preview.valid_days)
        b.metric("Missing rainfall days", preview.missing_days)
        c.metric("Calendar coverage", f"{preview.valid_days / preview.expected_days:.1%}")
        if preview.missing_days:
            st.warning("Missing dates and blank values remain gaps. Totals cover available observations only.")
        lookup = dict(preview.observations)
        days = [preview.observations[0][0] + timedelta(days=i) for i in range(preview.expected_days)]
        frame = pd.DataFrame({"date": days, "precip_mm": [lookup.get(day) for day in days]})
        if frame.precip_mm.max() > 500:
            st.warning("Values above 500 mm/day need a unit/source check. They have not been changed or excluded.")
        plot_frame = frame if len(frame) <= 5000 else frame.iloc[::(len(frame) // 5000 + 1)]
        fig = go.Figure(go.Scatter(x=plot_frame.date, y=plot_frame.precip_mm, mode="lines+markers", connectgaps=False, name="Local observations"))
        fig.update_yaxes(title="Daily rainfall · mm")
        st.plotly_chart(accessible_chart(fig), width="stretch", config={"displayModeBar": False})
        st.dataframe(frame, hide_index=True, width="stretch")
        st.caption(f"Original file SHA-256: {preview.original_sha256}")
        st.info(f"⚠️ {CUSTOM_CATCHMENT_DISCLAIMER} No percentile, forecast or scenario change is produced by this preview.")

        with st.container(border=True):
            st.markdown("##### 🌟 Data Sovereignty: Use in Scenario Generator")
            st.caption("Register your uploaded rain gauge so you can resample drought scenarios and simulate storage drawdown directly on your own local records.")
            if st.button("🚀 Activate Gauge & Build Scenarios on Your Data", key=f"btn_activate_custom_gauge_{preview.original_sha256[:8]}", type="primary", width="stretch"):
                clean_lookup = {pd.to_datetime(d): v for d, v in preview.observations if v is not None}
                s_series = pd.Series(clean_lookup).sort_index()
                st_id = f"LOCAL_{preview.station[:10].upper().replace(' ', '_')}"
                curr_src = st.session_state.get("custom_source") or load_source()
                new_src = curr_src.with_custom_station(st_id, preview.station, s_series, preview.location)
                st.session_state["custom_source"] = new_src
                st.session_state["selected_stations"] = [st_id]
                params = ScenarioParams((st_id,), (90, 180, 270), (1, 4, 7, 10), 0.35, 0.85, "All stations", 300, 22)
                st.session_state.workspace = Workspace(
                    new_src, params, 6, analysis_context=analysis_context_for_run()
                )
                st.session_state.data_accepted = True
                st.session_state.page = "Workspace"
                st.rerun()

        uploaded_reference_comparison(preview, upload.getvalue())




def uploaded_reference_comparison(preview, raw):
    st.subheader("Compare with public rainfall")
    reference_source = load_source()
    registry = {item["id"]: item for item in reference_source.manifest["stations"]}
    station_id = st.selectbox("Public reference station", ["Choose a station", *registry],
                              format_func=lambda value: value if value not in registry else f"{registry[value]['name']} ({value})",
                              key="upload_reference_station")
    if station_id not in registry:
        st.caption("Select a station deliberately. BASIN does not infer the closest station or catchment suitability.")
        return
    metadata = registry[station_id]
    st.write({"Reference": metadata["name"], "Latitude": metadata["latitude"], "Longitude": metadata["longitude"],
              "Snapshot period": f"{reference_source.manifest['start']} to {reference_source.manifest['end']}"})
    st.caption("Source: NOAA GHCN-Daily, bundled snapshot. This is a same-date comparison, not a seasonal normal or an official drought category.")
    st.markdown(f"[Source documentation]({reference_source.manifest['documentation']})")
    token = f"{preview.original_sha256}_{preview.unit}_{preview.station}_{preview.location}_{station_id}"
    relationship = st.selectbox("Relationship to uploaded station", ["Not established", "Same physical station (user confirmed)", "Different station: regional proxy only"], key=f"relationship_{token}")
    daily = st.checkbox("I checked that the daily observation periods are comparable", key=f"daily_basis_{token}", help="Dates alone do not prove the gauges observe the same 24-hour period. Leave unchecked if unknown.")
    st.warning(f"Nearby or regional stations may experience different rain. A difference does not show which dataset is correct, establish catchment rainfall or predict a shortage. {CUSTOM_CATCHMENT_DISCLAIMER}")
    relation = "not_established" if relationship == "Not established" else "same_station" if relationship.startswith("Same") else "regional_proxy"
    persist_custom_panel(preview, raw, station_id, relation, daily, token)
    if relationship == "Not established" or not daily:
        st.info("Comparison is blocked until the location relationship and daily basis are reviewed. You can still inspect the uploaded data above.")
        return
    relation = "same_station" if relationship.startswith("Same") else "regional_proxy"
    series = reference_source.select([station_id])[station_id]
    reference = {day.date(): None if pd.isna(value) else float(value) for day, value in series.items()}
    try:
        result = compare_rainfall(preview, reference, relationship=relation, daily_basis_confirmed=daily)
    except ValueError as error:
        st.warning(str(error))
        return
    a, b, c = st.columns(3)
    a.metric("Paired valid days", f"{result.paired_days} / {len(result.rows)}")
    b.metric("Uploaded total on paired days · mm", f"{result.upload_total_mm:.2f}")
    c.metric("Reference total on paired days · mm", f"{result.reference_total_mm:.2f}")
    st.write(f"Uploaded minus reference: {result.difference_mm:+.2f} mm")
    if result.relative_difference_pct is None:
        st.caption("Relative difference unavailable: the reference total is zero.")
    else:
        st.caption(f"Relative difference: {result.relative_difference_pct:+.2f}% of the reference total, not a forecast probability.")
    st.caption(f"{len(result.rows) - result.paired_days} days excluded from both totals because one or both values are missing. No gaps are filled.")
    frame = pd.DataFrame(result.rows, columns=["date", "uploaded_mm", "reference_mm"])
    plot_frame = frame if len(frame) <= 5000 else frame.iloc[::(len(frame) // 5000 + 1)]
    fig = go.Figure()
    for field, label in [("uploaded_mm", "Uploaded rainfall"), ("reference_mm", "NOAA reference")]:
        fig.add_trace(go.Scatter(x=plot_frame.date, y=plot_frame[field], name=label, connectgaps=False))
    fig.update_yaxes(title="Daily rainfall · mm")
    st.plotly_chart(accessible_chart(fig), width="stretch", config={"displayModeBar": False})
    st.dataframe(frame, hide_index=True, width="stretch")
    st.caption("This is a live preview. Save reviewed evidence above to retain a version, link it to scenarios and include it in a consented verified packet.")
    include = st.checkbox("Include my uploaded values in a downloadable comparison report", key=f"share_comparison_{token}_{relation}")
    if include:
        report = {"schema_version": "rainfall-comparison-1", "method": "paired-valid-calendar-days-v1",
                  "upload_sha256": preview.original_sha256, "uploaded_input_unit": preview.unit,
                  "reference_snapshot_sha256": reference_source.manifest["sha256"], "reference_station_id": station_id,
                  "reference_source": reference_source.manifest["documentation"], "relationship_declared_by_user": relation,
                  "daily_basis_confirmed_by_user": True, "units": "mm", "paired_days": result.paired_days,
                  "upload_total_mm": result.upload_total_mm, "reference_total_mm": result.reference_total_mm,
                  "difference_mm": result.difference_mm, "relative_difference_pct": result.relative_difference_pct,
                  "limitations": "Descriptive same-date comparison; geography and daily basis are user declarations, not independently validated. No forecast, climatology or scenario approval.",
                  "rows": [{"date": str(day), "uploaded_mm": x, "reference_mm": y} for day, x, y in result.rows]}
        st.download_button("Download comparison JSON", json.dumps(report, indent=2, allow_nan=False), "rainfall-comparison.json", "application/json")


def persist_custom_panel(preview, raw, reference_station, relationship, daily, token):
    workspace = st.session_state.get("workspace")
    if workspace is None:
        st.info("To retain this upload, first create or open an analysis from Workspace. Preview alone does not save it.")
        return
    with st.expander("Save reviewed upload into this analysis"):
        st.caption("Links this comparison as supporting evidence; does not replace NOAA scenario rainfall. Saving or replacing evidence clears affected scenario approvals. Unknown suitability can be recorded without calculating a comparison.")
        active = active_ids(workspace.custom_uploads)
        versions = {r["id"]: r for r in workspace.custom_uploads}
        with st.form("save_custom_" + digest(token)):
            previous = st.selectbox("Evidence version to replace", ["New evidence", *sorted(active)],
                                    format_func=lambda i: i if i == "New evidence" else versions[i]["station"] + " · " + i[-8:])
            chosen = st.multiselect("Scenarios supported by this evidence", [s.id for s in workspace.scenarios], default=workspace.selected)
            provider = st.text_input("Source / provider", value="Local Municipal / Sponsor Observation")
            basis = st.text_input("Observation-day definition", value="Midnight-to-midnight local standard time; unflagged observations", help="Timezone and daily reporting window, or explicitly explain what is unknown.")
            rationale = st.text_area("Why this reference is appropriate, or what remains uncertain", value="User-provided municipal monitoring gauge provided for local observation context (unverified by BASIN).")
            reviewed = st.checkbox("I reviewed the upload and declarations and consent to saving the original bytes and metadata locally")
            submit = st.form_submit_button("Save reviewed evidence")
        if submit:
            try:
                if previous != "New evidence" and sorted(chosen) != versions[previous]["scenario_ids"]:
                    raise ValueError("Replacing a version must retain its scenario links. Select the same scenarios shown in Saved custom evidence.")
                candidate = deepcopy(workspace)
                candidate.save_custom_upload(raw, reviewed=reviewed, station=preview.station, location=preview.location,
                                             unit=preview.unit, provider=provider, observation_basis=basis,
                                             reference_station=reference_station, relationship=relationship, daily_confirmed=daily,
                                             rationale=rationale, scenario_ids=chosen,
                                             supersedes="" if previous == "New evidence" else previous)
                if save(candidate):
                    st.session_state.workspace = candidate
                    st.session_state.pop("packet", None)
                    st.rerun()
            except ValueError as error:
                st.error(str(error))


def saved_custom_panel(workspace):
    if not workspace or not workspace.custom_uploads:
        return
    with st.expander("Saved custom evidence", expanded=True):
        active = active_ids(workspace.custom_uploads)
        versions = {r["id"]: r for r in workspace.custom_uploads}
        identifier = st.selectbox("Saved upload version", list(versions), format_func=lambda i: versions[i]["station"] + " · " + i[-8:] + (" · current" if i in active else " · superseded"))
        record = versions[identifier]
        st.markdown(f"**Source: {format_custom_source_label(record['station'], record.get('provider'))}**")
        st.caption(f"{format_custom_coverage_dates(record.get('start'), record.get('end'), record.get('valid_days'))} · original unit: {record['input_unit']} · linked scenarios: {', '.join(record['scenario_ids'])}")
        st.caption(f"⚠️ {CUSTOM_CATCHMENT_DISCLAIMER}")
        with st.expander("Source identity and suitability details"):
            st.write({k: record[k] for k in ("id", "station", "location", "provider", "input_unit", "start", "end", "original_sha256", "normalized_sha256", "reference_station", "relationship", "observation_basis", "rationale", "scenario_ids")})
        result = record["comparison"]
        st.caption("Supporting evidence only; original rainfall scenarios are unchanged. Original bytes remain local. Review decisions must be renewed after a version change.")
        if result["status"] == "calculated":
            st.write({k: result[k] for k in ("paired_days", "upload_total_mm", "reference_total_mm", "difference_mm")})
            frame = pd.DataFrame(result["rows"], columns=["date", "uploaded_mm", "reference_mm"])
            fig = go.Figure()
            for field in ("uploaded_mm", "reference_mm"):
                fig.add_trace(go.Scatter(x=frame.date, y=frame[field], name=field, connectgaps=False))
            st.plotly_chart(chart(fig), width="stretch", config={"displayModeBar": False})
        else:
            st.info("Comparison unavailable: " + result["reason"])
            frame = pd.DataFrame(record["observations"], columns=["date", "uploaded_mm"])
        st.dataframe(frame, hide_index=True, width="stretch")


def save(w):
    try:
        w.save()
        return True
    except OSError as error:
        st.error(f"Save failed: {error}")
        return False


def supporting_documents_panel(workspace: Workspace | None):
    """UI for user-provided supporting document ingestion, extraction, and evidence review."""
    st.markdown("##### 📄 Supporting Documents & Cited Evidence")
    st.caption(
        f"Attach local PDF or plain-text reports as unverified context. "
        f"{DOCUMENT_CATCHMENT_DISCLAIMER} Extraction is not verification; promotion to evidence requires human review."
    )

    if workspace is None:
        st.info("Start an analysis (click 'Try an example' or build scenarios in Step 2) before adding supporting documents.")
        return

    # Section 1: Ingest New Document
    with st.container(border=True):
        st.markdown("###### Add Document")
        c_file, c_meta = st.columns([1.5, 1.5])
        with c_file:
            uploaded = st.file_uploader(
                "Upload document (.pdf or .txt)",
                type=["pdf", "txt"],
                key="supporting_doc_file_uploader",
                help="Only .pdf and .txt files up to 30 MB / 100 pages. Scripts, macros, and encryption are rejected.",
            )
        with c_meta:
            provider = st.text_input(
                "Source / Provider organization",
                key="supporting_doc_provider_input",
                placeholder="e.g. City Water Dept / River Authority",
                help="Organization or source that published the document.",
            )
            privacy = st.selectbox(
                "Privacy classification",
                ["private", "public"],
                index=0,
                key="supporting_doc_privacy_select",
                help="Private documents remain strictly on this device and are omitted from default exports.",
            )

        if st.button("Add document", key="btn_add_supporting_doc", type="primary", disabled=uploaded is None):
            if not provider.strip():
                st.error("Please enter a source / provider organization name.")
            elif uploaded is None:
                st.error("Please choose a file to upload.")
            else:
                try:
                    raw_bytes = uploaded.getvalue()
                    doc = workspace.ingest_document(
                        raw=raw_bytes,
                        filename=uploaded.name,
                        provider=provider.strip(),
                        privacy=privacy,
                    )
                    save(workspace)
                    st.success(f"Document '{doc.identity.original_filename}' added successfully ({doc.identity.sha256[:8]}…).")
                    st.rerun()
                except Exception as exc:
                    st.error(f"Failed to add document: {exc}")

    # Section 2: Compact Document List
    if not workspace.documents:
        st.caption("No supporting documents added yet.")
        return

    st.markdown("###### Document Catalog")
    table_data = [
        {
            "Document ID": d.identity.id[:12] + "…",
            "Filename": d.identity.original_filename,
            "Provider": d.identity.source_provider,
            "Size": f"{d.identity.byte_size / 1024:.1f} KB",
            "State": d.state.replace("_", " ").title(),
            "Privacy": d.identity.privacy.capitalize(),
            "Digest (SHA-256)": f"{d.identity.sha256[:12]}…",
        }
        for d in workspace.documents
    ]
    st.dataframe(pd.DataFrame(table_data), hide_index=True, width="stretch")

    # Section 3: Document Inspection & Review Workflow
    doc_map = {d.identity.id: f"{d.identity.original_filename} ({d.identity.source_provider}) — {d.state.replace('_', ' ').title()}" for d in workspace.documents}
    selected_id = st.selectbox(
        "Select document for details & review",
        list(doc_map.keys()),
        format_func=lambda did: doc_map[did],
        key="selected_doc_review_id",
    )
    doc = next((d for d in workspace.documents if d.identity.id == selected_id), None)
    if doc is None:
        return

    with st.container(border=True):
        st.markdown(f"###### Inspect: {doc.identity.original_filename}")
        d1, d2, d3, d4 = st.columns(4)
        d1.metric("State", doc.state.replace("_", " ").title())
        d2.metric("Media Type", doc.identity.media_type)
        d3.metric("Size", f"{doc.identity.byte_size / 1024:.1f} KB")
        d4.metric("Privacy", doc.identity.privacy.capitalize())

        st.caption(f"**SHA-256 Digest**: `{doc.identity.sha256}` · **Ingested**: `{doc.identity.ingested_at[:19]}`")

        # Extracted Text Excerpt (Bounded Plain-Text)
        if doc.blocks:
            st.markdown("**Extracted Text Excerpt**")
            # Render bounded excerpt (up to 5 blocks, each up to 600 chars)
            for b in doc.blocks[:5]:
                status_icon = "🟢" if b.extraction_status == "success" else ("🟡" if b.extraction_status == "partial" else "⚪")
                preview_text = b.extracted_text[:600] + ("…" if len(b.extracted_text) > 600 else "")
                if not preview_text.strip():
                    preview_text = "[Empty text block]"
                st.markdown(f"{status_icon} **Block `{b.block_id}`** (Page {b.page_number}, {len(b.extracted_text)} chars)")
                st.code(preview_text, language=None)
            if len(doc.blocks) > 5:
                st.caption(f"Showing first 5 of {len(doc.blocks)} extracted blocks. All blocks remain available for evidence citation.")
        elif doc.state == DocumentState.UPLOADED.value:
            st.info("Document text has not been extracted yet. Click **Extract text blocks** below to begin.")

        # Lifecycle Step Actions: Extract -> Submit for review -> Accept as evidence / Reject
        st.divider()

        if doc.state == DocumentState.UPLOADED.value:
            st.markdown("**Action: Extract Text**")
            st.caption("Extract text blocks from the uploaded file for inspection and human review.")
            if st.button("Extract text blocks", key=f"btn_extract_{doc.identity.id}", type="primary"):
                try:
                    workspace.extract_document(doc.identity.id)
                    save(workspace)
                    st.success("Extraction complete.")
                    st.rerun()
                except Exception as exc:
                    st.error(f"Extraction failed: {exc}")

        elif doc.state == DocumentState.EXTRACTED.value:
            st.markdown("**Action: Submit for Review**")
            st.caption("Mark extracted text as ready for formal review and evidence citation.")
            if st.button("Submit document for review", key=f"btn_submit_rev_{doc.identity.id}", type="primary"):
                try:
                    workspace.submit_document_for_review(doc.identity.id)
                    save(workspace)
                    st.success("Document submitted for review.")
                    st.rerun()
                except Exception as exc:
                    st.error(f"Submission failed: {exc}")

        elif doc.state in (DocumentState.NEEDS_REVIEW.value, DocumentState.REJECTED.value):
            st.markdown("**Action: Human Review Decision**")
            st.caption("Review extracted blocks, cite specific blocks, and provide rationale before promoting to evidence.")

            available_block_ids = [b.block_id for b in doc.blocks]
            cited_blocks = st.multiselect(
                "Select block(s) to cite",
                available_block_ids,
                default=available_block_ids[:1] if available_block_ids else [],
                key=f"cited_blocks_{doc.identity.id}",
                help="Select one or more extracted block IDs that support the confirmed statement.",
            )
            scen_options = [s.id for s in workspace.scenarios]
            linked_scenarios = st.multiselect(
                "Attach evidence to scenario(s)",
                scen_options,
                default=workspace.selected if workspace.selected else scen_options[:1],
                key=f"attach_scenarios_{doc.identity.id}",
                help="Scenarios that this document evidence will be associated with.",
            )
            confirmed_stmt = st.text_area(
                "Confirmed statement from document (required)",
                key=f"confirmed_stmt_{doc.identity.id}",
                placeholder="Specific factual or policy statement found in cited blocks...",
                help="Must state specific factual context without claiming official regulatory approval or physical validation.",
            )
            rationale = st.text_area(
                "Reviewer rationale (required)",
                key=f"rationale_{doc.identity.id}",
                placeholder="Explain why this excerpt was reviewed and how it provides context...",
                help="Must explain your evaluation without making prohibited claims.",
            )
            priv_note = st.text_input(
                "Private reviewer note (optional)",
                key=f"priv_note_{doc.identity.id}",
                help="Private to this device; excluded from unconsented public exports.",
            )

            col_acc, col_rej = st.columns(2)
            with col_acc:
                if st.button("Accept as evidence", key=f"btn_accept_{doc.identity.id}", type="primary", width="stretch"):
                    if not cited_blocks:
                        st.error("Please select at least one block to cite.")
                    elif not linked_scenarios:
                        st.error("Please select at least one scenario to attach evidence to.")
                    elif not confirmed_stmt.strip():
                        st.error("Confirmed statement is required.")
                    elif not rationale.strip():
                        st.error("Reviewer rationale is required.")
                    else:
                        try:
                            workspace.review_and_accept_document(
                                doc_id=doc.identity.id,
                                reviewer_rationale=rationale.strip(),
                                confirmed_statement=confirmed_stmt.strip(),
                                reviewed_block_ids=cited_blocks,
                                scenario_ids=linked_scenarios,
                                private_note=priv_note.strip(),
                            )
                            save(workspace)
                            st.success("Document accepted as evidence!")
                            st.rerun()
                        except Exception as exc:
                            st.error(f"Cannot accept document: {exc}")

            with col_rej:
                if st.button("Reject document", key=f"btn_reject_{doc.identity.id}", width="stretch"):
                    if not rationale.strip():
                        st.error("A rationale is required to record a rejection.")
                    else:
                        try:
                            workspace.reject_document(doc.identity.id, rationale.strip())
                            save(workspace)
                            st.info("Document rejected.")
                            st.rerun()
                        except Exception as exc:
                            st.error(f"Cannot reject document: {exc}")

        elif doc.state == DocumentState.ACCEPTED_AS_EVIDENCE.value:
            st.success("✅ **Accepted as Evidence**")
            if doc.review:
                st.markdown(f"**Confirmed statement**: {doc.review.confirmed_statement}")
                st.markdown(f"**Reviewer rationale**: {doc.review.reviewer_rationale}")
                st.caption(f"Cited blocks: {', '.join(doc.review.reviewed_blocks)} (Pages: {', '.join(str(p) for p in doc.review.reviewed_pages)}) · Reviewed: {doc.review.reviewed_at[:19]}")

            if st.button("Revoke evidence / Reject document", key=f"btn_revoke_{doc.identity.id}"):
                try:
                    workspace.reject_document(doc.identity.id, "Evidence revoked by user")
                    save(workspace)
                    st.info("Document status changed to rejected; evidence links removed.")
                    st.rerun()
                except Exception as exc:
                    st.error(f"Revocation failed: {exc}")


def analysis_context_from_widgets() -> AnalysisContext:
    """Build the validated decision context currently shown on the Data page."""
    specific = st.session_state.get("context_scope", "Region-wide screening") == "Specific community or provider"
    if not specific:
        return AnalysisContext.region_wide()
    return AnalysisContext(
        scope="specific_provider",
        organization_type=st.session_state.get("context_org_type", "municipality"),
        organization_name=st.session_state.get("context_org_name", ""),
        counties=tuple(st.session_state.get("context_counties", [])),
        community=st.session_state.get("context_community", ""),
        supply_relationship=st.session_state.get("context_supply", "unknown"),
        decision_use=st.session_state.get("context_decision", "modeling_request"),
    )


def analysis_context_for_run() -> AnalysisContext:
    """Return the context preserved across Streamlit page/widget cleanup."""
    pending = st.session_state.get("pending_analysis_context")
    if pending is not None:
        return AnalysisContext.from_record(pending)
    return analysis_context_from_widgets()


def render_analysis_context_intake(workspace=None) -> AnalysisContext | None:
    """Ask who will use the run and keep geography separate from model claims."""
    existing = getattr(workspace, "analysis_context", None)
    if "context_scope" not in st.session_state:
        st.session_state.context_scope = (
            "Specific community or provider"
            if existing and existing.scope == "specific_provider"
            else "Region-wide screening"
        )
        specific_existing = existing is not None and existing.scope == "specific_provider"
        st.session_state.context_org_type = existing.organization_type if specific_existing else "municipality"
        st.session_state.context_org_name = existing.organization_name if specific_existing else ""
        st.session_state.context_counties = list(existing.counties) if specific_existing else []
        st.session_state.context_community = existing.community if specific_existing else ""
        st.session_state.context_supply = existing.supply_relationship if specific_existing else "unknown"
        st.session_state.context_decision = existing.decision_use if specific_existing else "modeling_request"

    with st.container(border=True):
        st.markdown("### Who and what area is this screening for?")
        st.caption("This decision context is saved in the run and handoff. It does not automatically select representative gauges or calibrate a local water system.")

        def set_specific_defaults():
            if (st.session_state.get("context_scope") == "Specific community or provider"
                    and not st.session_state.get("context_org_name", "").strip()):
                st.session_state.context_org_type = "municipality"
                st.session_state.context_supply = "unknown"
                st.session_state.context_decision = "modeling_request"

        st.radio(
            "Screening scope",
            ["Region-wide screening", "Specific community or provider"],
            horizontal=True,
            key="context_scope",
            on_change=set_specific_defaults,
        )
        if st.session_state.context_scope == "Specific community or provider":
            left, right = st.columns(2)
            left.selectbox("Organization type", list(ORGANIZATION_TYPES), format_func=ORGANIZATION_TYPES.get,
                           key="context_org_type")
            left.text_input("City, provider, district or organization", key="context_org_name",
                            placeholder="Example: City of Alice or Nueces County WCID No. 3")
            left.text_input("Community or service-area label (optional)", key="context_community",
                            placeholder="Example: Mathis service area")
            right.multiselect("Region N county or counties", list(REGION_N_COUNTIES), key="context_counties")
            right.selectbox("Water-source relationship", list(SUPPLY_RELATIONSHIPS),
                            format_func=SUPPLY_RELATIONSHIPS.get, key="context_supply")
            right.selectbox("Decision being prepared", list(DECISION_USES),
                            format_func=DECISION_USES.get, key="context_decision")
        else:
            st.info("The run will be labeled for all 11 Region N counties and will remain a regional rainfall-scenario screen.")

        try:
            context = analysis_context_from_widgets()
        except ValueError as error:
            st.warning(str(error))
            return None

        if workspace is not None and context != existing:
            if st.button("Save decision context to this run", key=f"save_context_{workspace.id}", type="primary"):
                workspace.set_analysis_context(context)
                st.session_state.pending_analysis_context = context.record()
                if save(workspace):
                    st.success("Decision context saved with this run and its next export.")
        elif workspace is not None:
            st.caption(f"Current run: **{context.audience_label}** · {context.county_label}")
        return context


@st.fragment
def render_analysis_focus_card(default_goal="storage"):
    """Dedicated engineering objective card with instant fragment updates and descriptive guidance."""
    with st.container(border=True):
        st.markdown("#### Analysis Focus & Decision Context")
        st.caption("Select your primary engineering objective to tailor scenario ranking, key metrics, and review tools.")

        goal_labels = {
            "storage": "Storage Stress",
            "operations": "Agronomics",
            "handoff": "Regulatory Handoff",
            "compare": "Comparison"
        }
        g_keys = list(goal_labels.keys())
        curr_g = st.session_state.get("run_focus_goal", default_goal)
        g_idx = g_keys.index(curr_g) if curr_g in g_keys else 0

        if hasattr(st, "segmented_control"):
            chosen_goal = st.segmented_control(
                "Analysis Focus",
                g_keys,
                default=curr_g if curr_g in g_keys else "storage",
                format_func=goal_labels.get,
                label_visibility="collapsed",
                key="step1_goal_segmented",
                help="Select your primary engineering objective"
            )
            if chosen_goal:
                st.session_state["run_focus_goal"] = chosen_goal
        else:
            chosen_goal = st.selectbox(
                "Analysis Focus",
                g_keys,
                index=g_idx,
                format_func=goal_labels.get,
                label_visibility="collapsed",
                key="step1_goal_selectbox"
            )
            st.session_state["run_focus_goal"] = chosen_goal

        active_goal = st.session_state.get("run_focus_goal", "storage")

        focus_details = {
            "storage": {
                "icon": "💧",
                "title": "Storage Stress (Municipal & Industrial Water Supply)",
                "does": "Prioritizes sustained multi-month cumulative rainfall deficits and measures severe drought drawdown trajectories against the combined regional reservoir capacity (Choke Canyon + Lake Corpus Christi, 919,900 ac-ft).",
                "changes": "Weights duration and deficit severity highest in Step 2; activates Drought Contingency Plan Stages 1–4 triggers, storage drawdown curves, and mandatory conservation tests in Step 3 Review."
            },
            "operations": {
                "icon": "🌾",
                "title": "Agronomics & Soil Moisture (Irrigation & Wildfire)",
                "does": "Evaluates agricultural root-zone water deficits, crop evapotranspiration (ETc for corn, cotton, grain sorghum), and Keetch-Byram Drought Index (KBDI) wildfire risk potential.",
                "changes": "Biases scenario candidate selection toward spring/summer crop growth seasons; unlocks crop irrigation deficit tables and seasonal wildfire vulnerability gauges in Step 3 Review."
            },
            "handoff": {
                "icon": "📋",
                "title": "Regulatory Handoff & Governance (Council & Planning)",
                "does": "Emphasizes multi-criteria weighted scoring, transparent audit logs, and verifiable SHA-256 data integrity for official decision-making by city councils and regional water authorities.",
                "changes": "Highlights station completeness, review rationales, audit trail history, and one-click Executive Technical Brief PDF and verified ZIP packet exports in Step 4."
            },
            "compare": {
                "icon": "📊",
                "title": "Comparison & Sensitivity (Multi-Scenario Analysis)",
                "does": "Highlights multi-scenario deficit envelopes, historical analog percentiles across the 1991–2025 NOAA record, and comparative trade-offs between competing drought candidates.",
                "changes": "Displays the synchronized multi-scenario deficit comparison graph in Step 2, and renders side-by-side scenario metric comparisons in Step 3 Review."
            }
        }
        detail = focus_details.get(active_goal, focus_details["storage"])

        st.markdown(f"""
        <div style="margin-top:12px;padding:14px 16px;border-radius:8px;background:color-mix(in srgb,currentColor 5%,transparent);border:1px solid color-mix(in srgb,currentColor 15%,transparent);">
            <div style="font-size:0.95rem;font-weight:750;margin-bottom:6px;">{detail['icon']} {detail['title']}</div>
            <div style="font-size:0.85rem;line-height:1.45;margin-bottom:8px;"><b>What it evaluates:</b> {detail['does']}</div>
            <div style="font-size:0.83rem;line-height:1.45;opacity:0.9;border-top:1px dashed color-mix(in srgb,currentColor 20%,transparent);padding-top:6px;"><b>Tool adaptations:</b> {detail['changes']}</div>
        </div>
        """, unsafe_allow_html=True)


def chart(fig, height=300):
    fig.update_layout(height=height, margin=dict(l=5, r=8, t=10, b=5),
                      paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                      font=dict(family="Arial", size=12),
                      legend=dict(orientation="h", y=-.22),
                      colorway=["#087e8b", "#cc9145", "#638c72", "#826f9e", "#ac675d", "#4c6c94", "#858844", "#a25789"])
    fig.update_xaxes(showgrid=False, zeroline=False)
    fig.update_yaxes(zeroline=False)
    return accessible_chart(fig)


def basin_map(stations_df):
    """Render station locations on a baked-in offline GIS map or optional satellite overlay."""
    from basin_core.geo_map import build_basin_map
    satellite = st.session_state.get("map_satellite_mode", False)
    if st.session_state.get("map_offline_mode", False):
        satellite = False
    return build_basin_map(stations_df, use_satellite=satellite)


def reservoir_simulation_figure(sim_df: pd.DataFrame, pace_ms: int = 150, config: WaterSystemConfig | None = None):
    days = len(sim_df)
    step = max(1, days // 45)
    indices = list(range(0, days, step))
    if indices[-1] != days - 1:
        indices.append(days - 1)

    cfg = config or REGION_N_PRESET
    n_sources = len(cfg.sources)
    def compact_source_label(source: WaterSource) -> str:
        lines: list[str] = []
        current = ""
        for word in source.name.split():
            candidate = f"{current} {word}".strip()
            if current and len(candidate) > 11:
                lines.append(current)
                current = word
            else:
                current = candidate
        if current:
            lines.append(current)
        return "<br>".join(lines)

    source_labels = [compact_source_label(source) for source in cfg.sources]
    palette = ["#0d9488", "#087e8b", "#0284c7", "#0369a1"]
    colors = [palette[i % len(palette)] for i in range(n_sources)]
    max_cap = max(s.capacity_acft for s in cfg.sources)

    fig = make_subplots(
        rows=2, cols=1,
        row_heights=[0.42, 0.58],
        vertical_spacing=0.22,
        subplot_titles=["Active Storage (ac-ft)", "Combined Pool Trajectory (%)"],
        specs=[[{"type": "bar"}], [{"type": "xy"}]]
    )

    init_row = sim_df.iloc[-1]
    y_init = []
    text_init = []
    for i in range(n_sources):
        col_acft = f"source_{i}_acft"
        col_pct = f"source_{i}_pct"
        if col_acft in init_row:
            val_acft = init_row[col_acft]
            val_pct = init_row[col_pct]
        elif i == 0 and "lcc_acft" in init_row:
            val_acft = init_row["lcc_acft"]
            val_pct = init_row["lcc_pct"]
        elif i == 1 and "ccr_acft" in init_row:
            val_acft = init_row["ccr_acft"]
            val_pct = init_row["ccr_pct"]
        else:
            val_acft = 0.0
            val_pct = 0.0
        y_init.append(val_acft)
        text_init.append(f"{val_acft:,.0f} ac-ft<br>({val_pct:.1f}%)")

    fig.add_trace(go.Bar(
        x=source_labels,
        y=y_init,
        marker=dict(color=colors, line=dict(width=1.5, color="#123d38")),
        text=text_init,
        textposition="outside", textfont=dict(size=12), cliponaxis=False,
        customdata=[[source.name, source.capacity_acft] for source in cfg.sources],
        name="Reservoir Storage",
        hovertemplate=(
            "<b>%{customdata[0]}</b><br>Capacity: %{customdata[1]:,.0f} ac-ft"
            "<br>Storage: %{y:,.0f} ac-ft<extra></extra>"
        )
    ), row=1, col=1)

    fig.add_trace(go.Scatter(
        x=sim_df["day"],
        y=sim_df["combined_pct"],
        mode="lines",
        line=dict(color="#087e8b", width=2.5),
        name="Combined %",
        hovertemplate="Day %{x}<br>Storage: %{y:.1f}%<extra></extra>"
    ), row=2, col=1)

    b40 = cfg.stage_bands_pct[0] * 100 if len(cfg.stage_bands_pct) >= 1 else 40
    b30 = cfg.stage_bands_pct[1] * 100 if len(cfg.stage_bands_pct) >= 2 else 30
    b20 = cfg.stage_bands_pct[2] * 100 if len(cfg.stage_bands_pct) >= 3 else 20

    reference_lines = [
        (b40, "dash", "#d97706", f"Band 1 · {b40:.0f}%"),
        (b30, "dash", "#ea580c", f"Band 2 · {b30:.0f}%"),
        (b20, "dash", "#dc2626", f"Band 3 · {b20:.0f}%"),
    ]

    if len(cfg.stage_bands_pct) >= 4:
        b10 = cfg.stage_bands_pct[3] * 100
        reference_lines.append((b10, "dot", "#991b1b", f"Band 4 · {b10:.0f}%"))

    dead_acft = getattr(cfg, "dead_storage_acft", 0.0)
    if dead_acft > 0 and cfg.total_capacity_acft > 0:
        dead_pct = dead_acft / cfg.total_capacity_acft * 100
        reference_lines.append((dead_pct, "dot", "#450a0a", f"Inactive storage · {dead_pct:.1f}%"))

    marker = getattr(cfg, "context_storage_marker_pct", None)
    if marker is not None:
        marker_pct = marker * 100
        reference_lines.append((marker_pct, "dot", "#7f1d1d", f"Reference · {marker_pct:g}%"))

    # A dedicated right-side gutter keeps each label aligned with its line and
    # out of the simulated trajectory at ordinary browser zoom.
    for level, dash, color, label in reference_lines:
        fig.add_hline(y=level, line_dash=dash, line_color=color, line_width=2, row=2, col=1)
        fig.add_annotation(
            x=1.015, y=level, xref="x2 domain", yref="y2", text=label,
            showarrow=False, xanchor="left", yanchor="middle", align="left",
            font=dict(size=11, color=color),
            bgcolor="rgba(17, 24, 28, 0.88)", borderpad=2,
        )

    frames = []
    for idx in indices:
        row = sim_df.iloc[idx]
        d = row["day"]
        sub_df = sim_df.iloc[:idx+1]
        y_frame = []
        text_frame = []
        for i in range(n_sources):
            col_acft = f"source_{i}_acft"
            col_pct = f"source_{i}_pct"
            if col_acft in row:
                val_acft = row[col_acft]
                val_pct = row[col_pct]
            elif i == 0 and "lcc_acft" in row:
                val_acft = row["lcc_acft"]
                val_pct = row["lcc_pct"]
            elif i == 1 and "ccr_acft" in row:
                val_acft = row["ccr_acft"]
                val_pct = row["ccr_pct"]
            else:
                val_acft = 0.0
                val_pct = 0.0
            y_frame.append(val_acft)
            text_frame.append(f"{val_acft:,.0f} ac-ft<br>({val_pct:.1f}%)")

        frame = go.Frame(
            data=[
                go.Bar(
                    x=source_labels,
                    y=y_frame,
                    text=text_frame,
                ),
                go.Scatter(
                    x=sub_df["day"].tolist(),
                    y=sub_df["combined_pct"].tolist()
                )
            ],
            name=f"Day {d}"
        )
        frames.append(frame)

    fig.frames = frames

    fig.update_yaxes(range=[0, max_cap * 1.18], title="ac-ft", row=1, col=1)
    fig.update_xaxes(tickangle=0, tickfont=dict(size=10), automargin=True, row=1, col=1)
    fig.update_yaxes(range=[0, 100], title="Combined %", row=2, col=1)
    fig.update_xaxes(range=[0, days + 2], title="Scenario Day", row=2, col=1)

    fig.update_layout(
        height=700,
        margin=dict(l=60, r=115, t=76, b=100),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Arial", size=12),
        showlegend=False,
        updatemenus=[dict(
            type="buttons",
            showactive=False, bgcolor="#243239", font=dict(color="#ffffff"),
            direction="left",
            x=0.0, xanchor="left", y=1.12,
            buttons=[
                dict(label="▶ Play Simulation", method="animate",
                     args=[None, {"frame": {"duration": pace_ms, "redraw": True}, "fromcurrent": False, "mode": "immediate"}]),
                dict(label="⏸ Pause", method="animate",
                     args=[[None], {"frame": {"duration": 0, "redraw": False}, "mode": "immediate", "transition": {"duration": 0}}])
            ]
        )],
        sliders=[dict(
            active=len(indices) - 1,
            x=0.0, y=-0.10,
            len=1.0,
            currentvalue={"prefix": "Simulation: ", "visible": True, "xanchor": "right"},
            pad={"t": 12, "b": 8},
            steps=[dict(label=f"D{sim_df.iloc[idx]['day']}", method="animate",
                        args=[[f"Day {sim_df.iloc[idx]['day']}"], {"frame": {"duration": 0, "redraw": True}, "mode": "immediate"}])
                   for idx in indices]
        )]
    )
    fig.update_xaxes(showgrid=False, zeroline=False)
    fig.update_yaxes(zeroline=False)
    return fig


def stress_spectrum_figure(spec: dict) -> go.Figure:
    fig = go.Figure()
    tier_colors = {1.0: ("#0d9488", 2.5), 0.8: ("#d97706", 2.2), 0.6: ("#ea580c", 2.2), 0.4: ("#dc2626", 2.2)}
    for m, res in spec["tier_results"].items():
        color, width = tier_colors.get(m, ("#64748b", 2.0))
        # Same label as the tables: relative to the input rainfall, never "historical".
        name = (res.get("metrics") or {}).get("tier_label") or rainfall_tier_label(m)
        style = {"name": name, "color": color, "width": width, "dash": "solid"}
        sim_df = res["df"]
        fig.add_trace(go.Scatter(
            x=sim_df["day"],
            y=sim_df["combined_pct"],
            mode="lines",
            name=style["name"],
            line=dict(color=style["color"], width=style["width"], dash=style["dash"]),
            hovertemplate=f"<b>{style['name']}</b><br>Day %{{x}}<br>Storage: %{{y:.1f}}%<extra></extra>"
        ))

    # Threshold horizontal reference bands
    fig.add_hline(y=40, line_dash="dash", line_color="#d97706", annotation_text="Assumed 40% band",
                  annotation_position="top right")
    fig.add_hline(y=30, line_dash="dash", line_color="#ea580c", annotation_text="Assumed 30% band",
                  annotation_position="top right")
    fig.add_hline(y=20, line_dash="dash", line_color="#dc2626", annotation_text="Assumed 20% band",
                  annotation_position="top right")
    fig.add_hline(y=15, line_dash="dot", line_color="#991b1b", annotation_text="Assumed 15% band",
                  annotation_position="top right")

    fig.update_layout(
        height=360,
        margin=dict(l=10, r=10, t=60, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Arial", size=12),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1.0),
        xaxis=dict(title="Scenario Day", showgrid=False, zeroline=False),
        yaxis=dict(title="Combined Storage (%)", range=[0, 100], showgrid=True, zeroline=False),
    )
    return fig


def table(w):
    return pd.DataFrame([{"ID": s.id, "Group": s.cluster, "Profile": getattr(s, "cluster_name", f"Group {s.cluster}"),
                          "Score": round(s.score, 2),
                          "Days": s.features["duration_days"], "Onset": calendar.month_abbr[s.features["onset_month"]],
                          "Deficit mm": round(s.features["deficit_mm"], 2),
                          "Deficit in": round(s.features["deficit_mm"] / 25.4, 2),
                          "Stations stressed together %": round(s.features["concurrence"] * 100, 1),
                          "How unusual vs history %": round(s.features["historical_percentile"] * 100, 1),
                          "Dry spell days": s.features["max_dry_days"],
                          "Revision": s.revision, "Status": s.status,
                          "Selected for review": s.id in w.selected} for s in w.scenarios])


PAGE_LABELS = {
    "Data": "Data Dashboard",
    "Workspace": "Scenario Builder",
    "Review": "Review Selections",
    "Exports": "Export",
}


PAGE_QUESTIONS = {
    "Data": "Can I trust and use these observations?",
    "Workspace": "Which rainfall scenarios deserve review?",
    "Review": "Which rainfall scenarios belong in the handoff?",
    "Exports": "What evidence should the recipient receive?",
}


PAGE_ACTIONS = {
    "Data": "Check source identity, coverage, location and limitations before building scenarios.",
    "Workspace": "Configure settings, prioritize weights, and compare shortlisted candidates.",
    "Review": "Compare rainfall with its reference, check the evidence, and decide whether to include this revision.",
    "Exports": "Confirm the privacy choice, build the packet, and download the verified files.",
}


def decision_summary(w):
    lead = w.get(w.selected[0])
    evidence_count = len(w.evidence_refs.get(lead.id, []))
    unresolved = sum(conflict["status"] == "unresolved" for conflict in w.conflicts)
    approved = sum(
        scenario.status == "accepted" and scenario.approved_revision == scenario.revision
        for scenario in (w.get(identifier) for identifier in w.selected)
    )
    limitation = (
        f"{unresolved} unresolved conflict(s)"
        if unresolved else "Continuous NOAA index baseline"
    )
    next_action = (
        "Proceed to Step 4: Export Deliverables"
        if approved == len(w.selected) else f"Step 3: Review {len(w.selected) - approved} remaining scenario(s)"
    )
    unique_windows = len({(s.provenance.get("source_start"), s.provenance.get("source_end")) for s in w.scenarios})
    unique_years = len({pd.Timestamp(s.provenance.get("source_start")).year for s in w.scenarios if s.provenance.get("source_start")})
    durations_list = sorted({s.features.get("duration_days") for s in w.scenarios if "duration_days" in s.features})
    dur_str = ", ".join(f"{d}d" for d in durations_list)

    with st.container(key="decision_summary", border=True):
        st.markdown("### Decision summary: Active Shortlist")
        if unique_windows == 1:
            p = lead.provenance
            st.warning(
                f"📌 **Single Historical Source Window**: All {len(w.scenarios)} candidate scenarios are scaled variations "
                f"of **one** historical record ({p.get('source_start')} to {p.get('source_end')}, {dur_str}). "
                "This reflects retention/extent variations of that specific sequence, not an empirical multi-year screening across the 1991–2025 record."
            )
        else:
            st.info(
                f"🔍 **Multi-Year Historical Screening**: Shortlisted from {len(w.scenarios)} candidate scenarios spanning "
                f"**{unique_windows} unique historical source windows** across **{unique_years} distinct calendar years** (durations: {dur_str})."
            )
        st.caption(
            f"Scenario to review: **{lead.id}** · Why it ranked here: "
            f"**{w.selection_reason(lead.id)}** · Evidence used: **{evidence_count} records**"
        )
        st.caption(f"{len(w.selected)} scenarios selected for review · {approved} approved for export · Station proxies: {', '.join(w.reference.stations)} (catchment representativeness unvalidated)")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Lead Scenario", lead.id, f"{w.selection_reason(lead.id).split(';')[0]}")
        c2.metric("Shortlist Progress", f"{approved} / {len(w.selected)} Approved", "Pending Review" if approved < len(w.selected) else "Ready for Export")
        c3.metric("Candidate Scope", f"{unique_windows} Source Window{'s' if unique_windows != 1 else ''}", f"{unique_years} year{'s' if unique_years != 1 else ''} sampled")
        c4.metric("Recommended Next Action", next_action)


def open_review(identifier):
    st.session_state.inspect_id = identifier
    st.session_state.page = "Review"


def review_preferences(workspace_id):
    """Display preferences for this run, cached in session state across navigation."""
    cached = st.session_state.get("review_prefs")
    if not isinstance(cached, tuple) or len(cached) != 2 or cached[0] != workspace_id:
        cached = (workspace_id, load_preferences(workspace_id))
        st.session_state["review_prefs"] = cached
        st.session_state["review_setup_goal"] = cached[1].goal
        st.session_state["review_setup_data"] = cached[1].data_source
        st.session_state["review_setup_guidance"] = cached[1].guidance
    return cached[1]


def store_review_preferences(workspace_id, preferences):
    """Persist display choices beside the run. Never touches the audited record."""
    st.session_state["review_prefs"] = (workspace_id, preferences)
    save_preferences(workspace_id, preferences)


def switch_page(name):
    if name == "Workspace" and "context_scope" in st.session_state:
        try:
            st.session_state.pending_analysis_context = analysis_context_from_widgets().record()
        except ValueError:
            pass
    st.session_state.page = name
    w = st.session_state.get("workspace")
    if name == "Review" and w and w.selected and not st.session_state.get("inspect_id"):
        st.session_state.inspect_id = w.selected[0]


def render_top_navigation(current_page, w):
    has_run = w is not None
    stages = [
        ("Data", PAGE_LABELS["Data"], True),
        ("Workspace", PAGE_LABELS["Workspace"], True),
        ("Review", PAGE_LABELS["Review"], has_run),
        ("Exports", PAGE_LABELS["Exports"], has_run),
    ]

    cols = st.columns(4)
    for col, (page_key, label, is_enabled) in zip(cols, stages):
        is_active = current_page == page_key
        if is_active:
            state_class = "basin-nav-active"
        elif not is_enabled:
            state_class = "basin-nav-locked"
        else:
            state_class = "basin-nav-ready"

        with col:
            st.markdown(f'<div class="basin-header-text-btn {state_class}">', unsafe_allow_html=True)
            btn_label = label if is_enabled else f"🔒 {label}"
            st.button(
                btn_label,
                key=f"nav_tab_{page_key}",
                disabled=not is_enabled,
                on_click=switch_page,
                args=(page_key,),
                help=None if is_enabled else "Requires an active analysis run. Generate scenarios in Scenario Builder first.",
                width="stretch",
            )
            st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('<div class="basin-nav-divider"></div>', unsafe_allow_html=True)


STEP_NUMBERS = {
    "Data": 1,
    "Workspace": 2,
    "Review": 3,
    "Exports": 4,
}


def render_bottom_nav(prev_page: str | None, next_page: str | None, next_label: str, next_disabled: bool = False, on_next=None, note: str | None = None):
    st.divider()
    col_back, col_spacer, col_next = st.columns([1.5, 3, 2.5])
    with col_back:
        if prev_page:
            step_num = STEP_NUMBERS.get(prev_page)
            prefix = f"Step {step_num}: " if step_num else ""
            st.button(f"◀ Back to {prefix}{PAGE_LABELS.get(prev_page, prev_page)}", key=f"nav_back_{prev_page}", on_click=switch_page, args=(prev_page,), width="stretch")
    with col_spacer:
        if note:
            st.markdown(f'<div style="text-align:center;padding-top:8px;font-size:0.88rem;opacity:0.85;font-weight:600;">{note}</div>', unsafe_allow_html=True)
    with col_next:
        if next_page:
            st.button(f"{next_label} ➔", key=f"nav_next_{next_page}", type="primary", disabled=next_disabled, on_click=on_next or switch_page, args=() if on_next else (next_page,), width="stretch")


def personal_notes_panel(w):
    def _toggle_notes_panel():
        st.session_state.notes_open = not st.session_state.get("notes_open", False)

    st.session_state.setdefault("notes_open", False)
    is_open = st.session_state.notes_open
    current_val = w.notes if w else st.session_state.get("personal_notes", "")
    has_notes = bool(current_val.strip())

    if is_open:
        st.html("""<style>
        .st-key-notes_drawer_panel {
            transform: translateY(0) !important;
            overflow-y: auto !important;
            box-shadow: 0 -8px 36px rgba(0,0,0,.55) !important;
        }
        </style>""")
    else:
        st.html("""<style>
        .st-key-notes_drawer_panel {
            transform: translateY(calc(100% - 44px)) !important;
            overflow: hidden !important;
            box-shadow: 0 -4px 20px rgba(0,0,0,.38) !important;
        }
        </style>""")

    with st.container(key="notes_slide_drawer"):
        with st.container(key="notes_drawer_panel"):
            with st.container(key="notes_header_btn"):
                if is_open:
                    header_label = "▼ Close Operator Notes" + (" ●" if has_notes else "")
                else:
                    header_label = "Operator Notes" + (" ●" if has_notes else "")
                st.button(
                    header_label,
                    key="btn_toggle_notes",
                    width="stretch",
                    help="Click to expand or collapse Operator Notes",
                    on_click=_toggle_notes_panel,
                )

            with st.container(key="notes_body_content"):
                st.caption("Saved locally with this analysis. Included in exports only if you opt in.")
                p_key = f"provider_{w.id}" if w else "provider_default"
                def on_notes_change():
                    val = st.session_state.get(p_key, "")
                    st.session_state["personal_notes"] = val
                    if w:
                        w.notes = val
                        save(w)

                note = st.text_area("Provider notes", value=current_val, key=p_key, height=360, on_change=on_notes_change, label_visibility="collapsed")
                col_s1, col_s2 = st.columns([3.5, 1.5])
                with col_s2:
                    if st.button("Save notes", key=f"btn_save_notes_{w.id if w else 'default'}", width="stretch", type="primary"):
                        on_notes_change()
                        st.success("Notes saved locally")

    st.html("""<script>
    (() => {
        const root = document.querySelector('.st-key-notes_slide_drawer');
        if (!root) return;
        const panel = root.querySelector('.st-key-notes_drawer_panel');
        if (!panel) return;
        const btn = root.querySelector('.st-key-notes_header_btn button');
        if (btn && !btn._hasNotesSlideListener) {
            btn._hasNotesSlideListener = true;
            btn.addEventListener('click', () => {
                if (panel.style.transform === 'translateY(0px)') {
                    panel.style.transform = 'translateY(calc(100% - 44px))';
                } else {
                    panel.style.transform = 'translateY(0)';
                }
            });
        }
    })();
    </script>""")


TUTORIAL_STEPS = [
    {
        "target": "data_map",
        "page": "Data",
        "tag": "OBSERVATIONS · PROVENANCE",
        "title": "1. Inspect the Observation Sources",
        "desc": "Three provisional NOAA station proxies with a byte-verified snapshot. A checksum does not validate catchment suitability.",
        "directive": "Inspect the highlighted station map and completeness table. Open Snapshot metadata & quality policy for the missing-data rules.",
    },
    {
        "target": "sidebar_generator",
        "page": "Workspace",
        "tag": "SCENARIO ENGINE · RESAMPLING",
        "title": "2. Resample Historical Weather Windows",
        "desc": "Extracts synchronized multi-station historical windows (30–365 days) retaining 35%–85% of observed rainfall (15%–65% reduction from observed) with every transformation recorded.",
        "directive": "Use New run in the left sidebar, then click Generate. Choose Next Step to keep the current run.",
    },
    {
        "target": "sidebar_presets",
        "page": "Workspace",
        "tag": "COMMUNITY PRIORITIES · WEIGHTS",
        "title": "3. Illustrative User Priorities",
        "desc": "Illustrative presets and editable weights change scores. Your reviewed shortlist stays in place until you rebuild it.",
        "directive": "Choose a community priority preset in the highlighted Ranking weights section on the left. Scores update; rebuilding the shortlist is a separate action.",
    },
    {
        "target": "workspace_table",
        "page": "Workspace",
        "tag": "UNSUPERVISED ML · CLUSTERING",
        "title": "4. K-Means Drought Profiles",
        "desc": "Deterministic K-Means clusters candidates into explainable profiles, ensuring diverse representation across the shortlist.",
        "directive": "Select a row in the highlighted candidate table, then click Inspect to open it. Choose Next Step to continue the tour.",
    },
    {
        "target": "review_simulation",
        "page": "Review",
        "tag": "OPTIONAL · ILLUSTRATIVE EXPERIMENT",
        "title": "5. Explore an Illustrative Water Balance",
        "desc": "Uncalibrated storage-balance experiment with assumed inflow, evaporation, demand and capacity. Its outputs are excluded from the evidence packet.",
        "directive": "Inspect assumptions, then play the conditional storage trajectory. Bands are illustrative, not official restriction dates.",
        "review_mode": "Reservoir simulation"
    },
    {
        "target": "review_decision",
        "page": "Review",
        "tag": "HUMAN REVIEW · RAINFALL CONTENT",
        "title": "6. Review, Challenge and Accept Rainfall",
        "desc": "Inspect evidence, record disagreements, and edit or accept rainfall content. Acceptance is a local review decision, not professional certification.",
        "directive": "Enter an audit rationale note and click 'Include this revision in handoff' to record your decision.",
        "review_mode": "Cumulative rainfall"
    },
    {
        "target": "export_panel",
        "page": "Exports",
        "tag": "AUDITABLE HANDOFF · EXPERT REVIEW",
        "title": "7. Export a Reviewed Evidence Packet",
        "desc": "Packages reviewed rainfall, public evidence, unresolved conflicts and a readable brief. Replay checks internal consistency within its stated scope.",
        "directive": "Click Build verified export in the highlighted area to build the reviewed handoff ZIP.",
    }
]


def start_example(source, names, force=False, crisis_demo=False):
    """Open a reproducible example without approving any scenario."""
    curr_w = st.session_state.get("workspace")
    if not force and curr_w and (any(s.status == "accepted" for s in curr_w.scenarios) or curr_w.has_custom_data):
        st.session_state.confirm_reset_example = "crisis" if crisis_demo else "standard"
        return
    st.session_state.pop("confirm_reset_example", None)
    params = ScenarioParams(tuple(names), (90, 180, 270), (1, 4, 7, 10), 0.35, 0.85, "All stations", 300, 22)
    workspace = Workspace(source, params, 6)
    for report_key in (
        "experiment_config",
        "preview_pdf",
        "packet",
        "review_initial_storage",
        "review_conservation",
        "review_pipeline_active",
        "storage_experiment",
    ):
        st.session_state.pop(report_key, None)
    st.session_state.workspace = workspace
    st.session_state["report_workspace_id"] = workspace.id
    st.session_state.data_accepted = True
    st.session_state.scenarios_accepted = True
    st.session_state.page = "Review"
    st.session_state.inspect_id = workspace.selected[0]
    st.session_state["crisis_demo"] = bool(crisis_demo)
    if crisis_demo:
        st.session_state["storage_experiment"] = True
        st.session_state["review_initial_storage"] = "7.7% (April 2026 context)"
        st.session_state["review_conservation"] = 0
        st.session_state["review_pipeline_active"] = True
        store_review_preferences(
            workspace.id,
            ReviewPreferences(
                goal="storage",
                data_source="example",
                mode="simple",
                configured=True,
                dismissed=True,
            ),
        )
    save(workspace)


def start_tutorial(source, names):
    st.session_state.tutorial_visit = st.session_state.get("tutorial_visit", 0) + 1
    st.session_state.tutorial_active = True
    st.session_state.tutorial_step = 0
    st.session_state.page = TUTORIAL_STEPS[0]["page"]
    curr_w = st.session_state.get("workspace")
    if curr_w is None:
        params = ScenarioParams(tuple(names), (90, 180, 270), (1, 4, 7, 10), 0.35, 0.85, "All stations", 300, 22)
        new_w = Workspace(source, params, 6)
        st.session_state.workspace = new_w
        save(new_w)
    if st.session_state.get("workspace") and not st.session_state.get("inspect_id"):
        st.session_state.inspect_id = st.session_state.workspace.selected[0]


def tutorial_next():
    step_idx = st.session_state.get("tutorial_step", 0)
    if step_idx < len(TUTORIAL_STEPS) - 1:
        next_idx = step_idx + 1
        st.session_state.tutorial_step = next_idx
        st.session_state.page = TUTORIAL_STEPS[next_idx]["page"]
        curr_w = st.session_state.get("workspace")
        if curr_w and TUTORIAL_STEPS[next_idx]["page"] == "Review":
            if not st.session_state.get("inspect_id") and curr_w.selected:
                st.session_state.inspect_id = curr_w.selected[0]
        if TUTORIAL_STEPS[next_idx].get("review_mode"):
            st.session_state.storage_experiment = TUTORIAL_STEPS[next_idx]["review_mode"] == "Reservoir simulation"
    else:
        st.session_state.tutorial_active = False


def tutorial_prev():
    step_idx = st.session_state.get("tutorial_step", 0)
    prev_idx = max(0, step_idx - 1)
    st.session_state.tutorial_step = prev_idx
    st.session_state.page = TUTORIAL_STEPS[prev_idx]["page"]
    if TUTORIAL_STEPS[prev_idx].get("review_mode"):
        st.session_state.storage_experiment = TUTORIAL_STEPS[prev_idx]["review_mode"] == "Reservoir simulation"


def tutorial_exit():
    st.session_state.tutorial_active = False


TOUR_LOCATIONS = {
    "data_map": "Data: station map and completeness table",
    "sidebar_generator": "Left sidebar: New run",
    "sidebar_presets": "Left sidebar: Ranking weights",
    "workspace_table": "Workspace: candidate table",
    "review_simulation": "Review: reservoir playback chart",
    "review_decision": "Review: note and decision controls on the right",
    "export_panel": "Exports: build packet button",
}


def current_tour_step():
    if not st.session_state.get("tutorial_active", False):
        return None
    index = st.session_state.get("tutorial_step", 0)
    if not 0 <= index < len(TUTORIAL_STEPS):
        return None
    return TUTORIAL_STEPS[index]


def return_to_tour_step():
    step = current_tour_step()
    if step:
        st.session_state.tutorial_visit = st.session_state.get("tutorial_visit", 0) + 1
        st.session_state.page = step["page"]
        if step.get("review_mode"):
            st.session_state.storage_experiment = step["review_mode"] == "Reservoir simulation"


def render_tour_guide(workspace):
    step = current_tour_step()
    if step is None:
        return
    index = st.session_state.tutorial_step
    directive = step["directive"]
    on_page = st.session_state.page == step["page"]
    if step["target"] == "export_panel" and workspace:
        try:
            workspace.exportable()
        except ValueError:
            directive = "Export is locked. Return to Review and accept or reject every shortlisted revision, keeping at least one accepted scenario. Then build the packet. Finishing the tutorial does not approve scenarios."
    with st.container(key="tutorial_guide"):
        st.markdown(f"""<div class="tutorial-meta">GUIDED TOUR &nbsp; / &nbsp; STEP {index + 1} OF {len(TUTORIAL_STEPS)}</div>
<div class="tutorial-title">{escape(step['title'].split('. ', 1)[-1])}</div>
<p class="tutorial-description">{escape(step['desc'])}</p>
<p class="tutorial-action">{escape(directive)}</p>
<div class="tutorial-location">Current section: {escape(TOUR_LOCATIONS[step['target']])}</div>""", unsafe_allow_html=True)
        with st.container(horizontal=True, gap="small"):
            st.button("◀ Prev", key="tutorial_prev", disabled=index == 0, on_click=tutorial_prev)
            st.button("✓ Finish Tutorial" if index == len(TUTORIAL_STEPS)-1 else "Next Step ▶",
                      key="tutorial_next", type="primary", on_click=tutorial_next)
            st.button("✕ Exit", key="tutorial_exit", on_click=tutorial_exit)
            if not on_page:
                st.button("Return to this step", on_click=return_to_tour_step)



@contextmanager
def tour_target(target_id: str):
    step = current_tour_step()
    active = step is not None and step["target"] == target_id and st.session_state.page == step["page"]
    key = f"tour_target_{target_id}"
    if active:
        st.markdown(f"""<style>.st-key-{key}{{outline:2px solid currentColor;outline-offset:3px;border-radius:6px;padding:10px;box-shadow:0 0 0 5px color-mix(in srgb,currentColor 8%,transparent)}}
.st-key-{key} .stPlotlyChart{{min-width:0}}</style>""", unsafe_allow_html=True)
    with st.container(key=key, width="content" if target_id == "export_panel" else "stretch"):
        if active:
            st.markdown(f'<div id="tour-{target_id}" class="tutorial-anchor tutorial-target-label">STEP {st.session_state.tutorial_step + 1} · {escape(TOUR_LOCATIONS[target_id])}</div>', unsafe_allow_html=True)
            render_tour_guide(st.session_state.get("workspace"))
            reveal_tour_target(target_id, f"{st.session_state.get('tutorial_visit', 0)}:{st.session_state.tutorial_step}:{target_id}")
        yield


try:
    source = st.session_state.get("custom_source") or load_source()
except (OSError, ValueError, KeyError) as error:
    st.error(f"Snapshot unavailable: {error}")
    st.stop()
names = {s["id"]: s["name"].title().replace(" Intl Ap", "").replace(" Rgnl Ap", "") for s in source.manifest["stations"]}
w = st.session_state.get("workspace")
if w is not None and st.session_state.get("report_workspace_id") != w.id:
    for report_key in ("experiment_config", "preview_pdf", "packet",
                       "review_initial_storage", "review_conservation", "review_pipeline_active", "storage_experiment"):
        st.session_state.pop(report_key, None)
    st.session_state["report_workspace_id"] = w.id
curr_target = TUTORIAL_STEPS[st.session_state.get("tutorial_step", 0)]["target"] if st.session_state.get("tutorial_active") else ""

profile_context = w.id if w else "new-run"
profile_defaults = review_preferences(w.id) if w else ReviewPreferences()
if st.session_state.get("run_focus_context") != profile_context:
    st.session_state["run_focus_context"] = profile_context
    st.session_state["run_focus_goal"] = profile_defaults.goal
    st.session_state["run_focus_data"] = profile_defaults.data_source
    st.session_state["run_focus_guidance"] = profile_defaults.guidance
    st.session_state["run_focus_skip"] = profile_defaults.dismissed and not profile_defaults.configured

with st.sidebar:
    page = st.radio("View", ["Data", "Workspace", "Review", "Exports"], key="page",
                    index=0, format_func=PAGE_LABELS.get, label_visibility="collapsed")

# Centered Brand Header with Top-Right Utilities and Top-Left Unit Selector
top_l, top_c, top_r = st.columns([1.2, 1.8, 1.2])

with top_l:
    u_choice = st.selectbox(
        "Units",
        ["🇺🇸 US · in / ac-ft", "🌐 Metric · mm / m³"],
        index=0 if st.session_state.get("unit_mode", "us") == "us" else 1,
        key="global_unit_selector",
        label_visibility="collapsed",
        help="Switch units across all charts, tables, and KPI metrics.",
    )
    st.session_state["unit_mode"] = "us" if u_choice.startswith("🇺🇸") else "metric"

with top_c:
    dark_logo_file = ROOT / "assets" / "basin-logo.png"
    light_logo_file = ROOT / "assets" / "basin-logo-light.png"
    if dark_logo_file.exists():
        dark_logo_b64 = base64.b64encode(dark_logo_file.read_bytes()).decode()
        light_logo_b64 = base64.b64encode(light_logo_file.read_bytes()).decode() if light_logo_file.exists() else dark_logo_b64
        st.markdown(
            '<div class="basin-top-logo-wrap">'
            f'<img src="data:image/png;base64,{dark_logo_b64}" alt="BASIN" class="basin-top-logo-dark" />'
            f'<img src="data:image/png;base64,{light_logo_b64}" alt="BASIN" class="basin-top-logo-light" />'
            '</div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown('<div class="basin-top-brand">BASIN</div>', unsafe_allow_html=True)

if hasattr(st, "dialog"):
    @st.dialog("Start New Analysis")
    def confirm_reset_dialog():
        st.warning("⚠️ **Reset active analysis?** Unsaved notes and scenario selections will be cleared.")
        c_yes, c_no = st.columns(2)
        if c_yes.button("Yes, Reset Everything", type="primary", width="stretch", key="modal_btn_reset_yes"):
            st.session_state.clear()
            st.session_state.page = "Data"
            st.rerun()
        if c_no.button("Cancel", width="stretch", key="modal_btn_reset_no"):
            st.rerun()
else:
    def confirm_reset_dialog():
        st.session_state.clear()
        st.session_state.page = "Data"
        st.rerun()

with top_r:
    u_col1, u_col2 = st.columns(2)
    with u_col1:
        with st.popover("Saved Runs", width="stretch"):
            st.markdown("**Saved Workspace Runs**")
            saved_dir = session_dir()
            sessions = sorted(saved_dir.glob("session-*.json"), key=lambda p: p.stat().st_mtime, reverse=True) if saved_dir.exists() else []
            if sessions:
                total_mb = sum(p.stat().st_size for p in sessions) / (1024 * 1024)
                st.caption(f"💾 {len(sessions)} saved session(s) · {total_mb:.1f} MB in `{saved_dir.name}/`")
                previous = st.selectbox(
                    "Select saved run", sessions,
                    format_func=lambda p: f"{datetime.fromtimestamp(p.stat().st_mtime).strftime('%Y-%m-%d %H:%M')} · {p.stem.replace('session-', '')[:8]}…",
                    key="saved_run_select"
                )
                if st.button("Open run", key="btn_open_saved_run", width="stretch", type="primary"):
                    try:
                        restored = Workspace.load(source, previous, auto_restore_custom=True)
                        st.session_state.clear()
                        st.session_state.workspace = restored
                        st.session_state.data_accepted = True
                        st.session_state.scenarios_accepted = True
                        if getattr(restored, "legacy_warning", None):
                            st.warning(restored.legacy_warning)
                        st.rerun()
                    except (ValueError, KeyError, OSError, TypeError) as error:
                        st.error(f"Cannot open run: {error}")
                if len(sessions) > 3:
                    if st.button("🗑️ Purge drafts older than top 3", key="btn_purge_old_runs", width="stretch"):
                        for p in sessions[3:]:
                            try:
                                p.unlink()
                                audit_p = p.parent / f"audit-{p.stem.replace('session-', '')}.jsonl"
                                if audit_p.exists():
                                    audit_p.unlink()
                            except OSError:
                                pass
                        st.success("Older drafts purged.")
                        st.rerun()
            else:
                st.caption("No saved runs found in `local/`.")

            st.divider()
            if st.button("🔄 Start New Analysis", key="btn_reset_analysis_top", width="stretch", help="Clear current run and reset all parameters"):
                confirm_reset_dialog()

    with u_col2:
        with st.popover("Settings", width="stretch"):
            st.markdown("**Appearance & Preferences**")
            appearance_picker()
            custom_appearance()
            st.toggle(
                "Show manual assistant tools",
                key="show_assistant_developer_tools",
                help="Shows the direct calculation-tool selector inside the Analyst Assistant.",
            )
            def _toggle_top_assistant():
                st.session_state.assistant_open = not st.session_state.get("assistant_open", False)

            st.button(
                "🤖 " + ("Close AI Assistant" if st.session_state.get("assistant_open", False) else "Open AI Assistant"),
                key="btn_top_assistant",
                width="stretch",
                on_click=_toggle_top_assistant,
            )
            st.divider()
            st.caption("Interactive walkthrough tour")
            st.button("Start tutorial", key="start_tutorial_btn", width="stretch", type="secondary", on_click=start_tutorial, args=(source, names))
            if st.session_state.get("tutorial_active", False):
                curr_step = st.session_state.get("tutorial_step", 0)
                st.caption(f"Tour running: Step {curr_step + 1} of {len(TUTORIAL_STEPS)}")
                st.button("Exit tutorial", key="sidebar_exit_tutorial_btn", width="stretch", on_click=tutorial_exit)

# Top 4-Stage Horizontal Navigation Stepper
render_top_navigation(page, w)

if current_tour_step() and page != current_tour_step()["page"]:
    render_tour_guide(w)

if st.session_state.get("confirm_reset_example"):
    with st.container(border=True):
        st.warning("⚠️ **Active Analysis in Progress**: The current workspace contains reviewed scenarios or custom evidence. Resetting will replace this workspace.")
        col_c1, col_c2 = st.columns(2)
        pending_example = st.session_state.get("confirm_reset_example")
        confirm_label = "Yes, load crisis demo" if pending_example == "crisis" else "Yes, reset and load example"
        if col_c1.button(confirm_label, type="primary", key="btn_confirm_reset_yes", width="stretch"):
            start_example(source, names, force=True, crisis_demo=pending_example == "crisis")
            st.rerun()
        if col_c2.button("Cancel, keep my current workspace", key="btn_confirm_reset_no", width="stretch"):
            st.session_state.pop("confirm_reset_example", None)
            st.rerun()


if page == "Data":
    st.markdown("### Step 1: Observation Baseline & Data Sources")
    st.markdown(f"**{PAGE_QUESTIONS['Data']}**")
    st.caption("Verify NOAA long-term continuous meteorological index stations and data completeness before proceeding to scenario generation.")

    saved_custom_panel(w)

    # 1. Side-by-side Decision Context & Analysis Focus Cards
    col_who, col_focus = st.columns(2, gap="medium")
    with col_who:
        data_analysis_context = render_analysis_context_intake(w)
    with col_focus:
        render_analysis_focus_card(profile_defaults.goal)

    if w is None:
        with st.container(border=True):
            quick_intro, guided_demo, crisis_demo = st.columns([2.2, 1, 1.25], vertical_alignment="center")
            quick_intro.markdown(
                "**Start with a prepared example**\n\n"
                "Both examples remain unreviewed until you make a decision."
            )
            guided_demo.button(
                "Try an example",
                key="btn_try_example_step1",
                on_click=start_example,
                args=(source, names),
                width="stretch",
            )
            crisis_demo.button(
                "Load 2026 crisis demo",
                key="btn_crisis_example_step1",
                on_click=start_example,
                args=(source, names, False, True),
                type="primary",
                width="stretch",
                help="Starts an illustrative storage experiment from the documented April 2026 7.7% combined-storage context.",
            )

    # 2. Session Restoration Dropdown
    with st.expander("📦 Restore analysis from verified .zip", expanded=False):
        st.caption("Restore and re-verify a complete previously exported BASIN `.zip` data bundle. Re-validates the SHA-256 manifest and mathematical replay on this device.")
        uploaded_bundle = st.file_uploader("Upload BASIN Bundle (.zip)", type=["zip"], key="bundle_restore_uploader")
        if uploaded_bundle is not None:
            if st.button("Verify & Restore Bundle", key="btn_execute_bundle_restore", type="primary", width="stretch"):
                try:
                    payload = uploaded_bundle.getvalue()
                    restored_w, verif = Workspace.restore_from_bundle(payload, source)
                    st.session_state.clear()
                    st.session_state.workspace = restored_w
                    st.session_state.data_accepted = True
                    st.session_state.scenarios_accepted = True
                    save(restored_w)
                    st.success(f"Verified Bundle Restored: {verif['scenarios_replayed']} scenarios replayed successfully.")
                    st.session_state.page = "Review"
                    st.rerun()
                except Exception as err:
                    st.error(f"Bundle restoration failed: {err}")
    metadata = pd.DataFrame(source.manifest["stations"]).rename(columns={"id": "station_id"})
    quality = pd.DataFrame(source.manifest["quality"])
    station_table = metadata.merge(quality, on="station_id")

    with tour_target("data_map"):
        from basin_core.region_n_map import render_observation_map, load_catalog
        render_observation_map(station_table, show_catalog=False)

    st.markdown("#### Historical rainfall")
    col_ts, col_hm = st.columns(2, gap="medium")
    with col_ts:
        st.markdown("##### Rainfall over time")
        left, right = st.columns([2.5, 1.5])
        station_view = left.multiselect("Observed rainfall", list(names), default=list(names), format_func=names.get, label_visibility="collapsed")
        interval = right.selectbox("Interval", ["Annual", "Monthly", "Daily"], label_visibility="collapsed")
        if station_view:
            observations = source.select(station_view)
            if interval == "Annual":
                groups = observations.groupby(observations.index.year)
                observed = groups.sum().where(groups.count().eq(groups.size(), axis=0))
            elif interval == "Monthly":
                groups = observations.resample("MS")
                observed = groups.sum().where(groups.count().eq(groups.size(), axis=0))
            else:
                observed = observations
            is_us = st.session_state.get("unit_mode", "us") == "us"
            plot_obs = (observed / 25.4).round(2) if is_us else observed
            fig = go.Figure()
            for station in plot_obs:
                fig.add_trace(go.Scatter(x=plot_obs.index, y=plot_obs[station], name=names[station], mode="lines", connectgaps=False))
            fig.update_yaxes(title="Precipitation · inches" if is_us else "Precipitation · mm")
            st.plotly_chart(chart(fig, 360), width="stretch", config={"displayModeBar": False})
            with st.expander(f"Daily values ({'inches' if is_us else 'mm'})", expanded=False):
                table_obs = (observations / 25.4).round(2) if is_us else observations.round(1)
                st.dataframe(table_obs, width="stretch", height=220)

    with col_hm:
        st.markdown("##### Monthly rainfall departures (1991–2025)")
        st.caption("Difference from the 35-year monthly average. Crimson is drier; teal is wetter.")
        hm_station_choice = st.selectbox(
            "Heatmap station perspective",
            ["Catchment composite (All stations average)", *[f"{names[s_id]} ({s_id})" for s_id in names]],
            label_visibility="collapsed",
        )
        if hm_station_choice.startswith("Catchment"):
            hm_obs = source.select(list(names))
            hm_title = "Catchment composite"
        else:
            selected_s_id = next(s_id for s_id in names if f"({s_id})" in hm_station_choice)
            hm_obs = source.select([selected_s_id])
            hm_title = names[selected_s_id]
        st.plotly_chart(accessible_chart(drought_anomaly_matrix_figure(hm_obs, title_prefix=hm_title)), width="stretch", config={"displayModeBar": False})

    catalog = load_catalog()
    with st.expander("Data Sources, Station Catalogs & Snapshot Metadata", expanded=False):
        tab_loaded, tab_cat, tab_meta, tab_custom, tab_docs = st.tabs([
            "Loaded Analysis Stations",
            "Regional Map Station Catalog",
            "Snapshot Manifest & Quality Policies",
            "Upload Custom Catchment CSV (Optional)",
            "Supporting documents",
        ])
        with tab_loaded:
            st.markdown("**Loaded Analysis Station Registry & Observation Quality**")
            st.caption("Synchronized rainfall series loaded for analysis. Other map stations provide geographic context.")
            st.dataframe(
                station_table[["station_id", "name", "latitude", "longitude", "completeness_pct", "missing_or_excluded_days", "trace_days"]],
                hide_index=True, width="stretch", height=320,
                column_config={
                    "station_id": "ID",
                    "name": "Station Name",
                    "latitude": st.column_config.NumberColumn("Lat", format="%.2f"),
                    "longitude": st.column_config.NumberColumn("Lon", format="%.2f"),
                    "completeness_pct": st.column_config.NumberColumn("Complete %", format="%.3f"),
                    "missing_or_excluded_days": st.column_config.NumberColumn("Missing"),
                    "trace_days": st.column_config.NumberColumn("Trace"),
                }
            )
            st.download_button("Download loaded station registry (CSV)", metadata.to_csv(index=False), "stations.csv", "text/csv")
        with tab_cat:
            st.markdown("**Region N Geographic Station Catalog**")
            st.caption(f"Catalog retrieved {catalog['retrieved_at'][:10]}. Coverage: all NOAA GHCN-Daily and USGS NWIS sites inside Region N.")
            table_cat = pd.DataFrame(catalog["rain_stations"] + catalog["water_stations"])
            st.dataframe(table_cat, hide_index=True, width="stretch", height=320, column_config={
                "source_url": st.column_config.LinkColumn("Source"),
                "first_year": st.column_config.NumberColumn("First year", format="%d"),
                "last_year": st.column_config.NumberColumn("Last year", format="%d")})
            col_dl1, col_dl2 = st.columns(2)
            col_dl1.download_button("Download map station catalog (CSV)", table_cat.to_csv(index=False), file_name="region_n_map_stations.csv", mime="text/csv")
            provenance = {k: catalog[k] for k in ("schema_version", "retrieved_at", "scope", "county_names", "sources")}
            col_dl2.download_button("Download map provenance (JSON)", json.dumps(provenance, indent=2), file_name="region_n_map_sources.json", mime="application/json")
        with tab_meta:
            st.markdown("**Snapshot Manifest & Quality Policy**")
            age = (datetime.now(timezone.utc) - datetime.fromisoformat(source.manifest["downloaded_at"])).days
            st.info(f"Verified NOAA Baseline Snapshot: Downloaded {source.manifest['downloaded_at'][:10]} ({age} days ago). Pinned SHA-256: `{source.manifest['sha256'][:16]}…`")
            st.json(source.manifest)
            col_m1, col_m2 = st.columns(2)
            col_m1.download_button("Download methodology", (ROOT / "docs/methodology.md").read_bytes(), "BASIN-methodology.md", "text/markdown")
            schema_file = ROOT / "docs/export_schema.md"
            if schema_file.exists():
                col_m2.download_button("Download export schema", schema_file.read_bytes(), "BASIN-export-schema.md", "text/markdown")
            else:
                col_m2.download_button("Download export schema", (ROOT / "docs/methodology.md").read_bytes(), "BASIN-export-schema.md", "text/markdown")
        with tab_custom:
            st.markdown("**Custom Station CSV Upload & Validation**")
            st.caption("Upload local rain gauge CSV records to observe completeness and compare against the regional baseline.")
            local_rainfall_preview(as_expander=False)
        with tab_docs:
            supporting_documents_panel(w)

    def accept_data_baseline():
        st.session_state.pending_analysis_context = data_analysis_context.record()
        st.session_state.data_accepted = True
        switch_page("Workspace")

    render_bottom_nav(
        prev_page=None,
        next_page="Workspace",
        next_label="Accept Baseline & Proceed to Step 2",
        next_disabled=data_analysis_context is None,
        on_next=accept_data_baseline,
        note="Baseline Observations Verified"
    )

elif w is None and page in ("Review", "Exports"):
    st.info("💡 **No Active Analysis Run**: This section is locked until scenarios are generated. Start in **Step 2: Scenario Builder** or click 'Try an example' below.")
    col_e1, col_e2 = st.columns(2)
    with col_e1:
        st.button("➔ Go to Step 2: Scenario Builder", key=f"btn_go_workspace_{page}", type="primary", on_click=switch_page, args=("Workspace",), width="stretch")
    with col_e2:
        st.button("Try an example", key=f"btn_try_example_{page}", on_click=start_example, args=(source, names), width="stretch")
    st.button("◀ Return to Step 1: Data Dashboard", key=f"btn_return_data_{page}", on_click=switch_page, args=("Data",), width="stretch")

elif page == "Workspace":
    st.markdown("### Step 2: Scenario Builder & Shortlist Engine")
    # Review focus is chosen before generation so the resulting run opens with the
    # relevant measurements and visuals leading. Repeated runs inherit the current
    # run's profile; the profile remains presentation-only.
    profile_context = w.id if w else "new-run"
    profile_defaults = review_preferences(w.id) if w else ReviewPreferences()
    if st.session_state.get("run_focus_context") != profile_context:
        st.session_state["run_focus_context"] = profile_context
        st.session_state["run_focus_goal"] = profile_defaults.goal
        st.session_state["run_focus_data"] = profile_defaults.data_source
        st.session_state["run_focus_guidance"] = profile_defaults.guidance
        st.session_state["run_focus_skip"] = profile_defaults.dismissed and not profile_defaults.configured

    with st.container(border=True):
        st.markdown("##### 🎯 Analysis Focus & Presentation Settings")
        st.caption("Choose what to focus on first. Tailors which measurements and diagnostic tools are prioritized in Step 3 Review. Does not alter mathematical calculations or export data.")
        focus_goal_col, focus_data_col, focus_guidance_col = st.columns(3)
        run_focus_goal = focus_goal_col.selectbox(
            "What are you trying to do?", list(GOALS),
            format_func=lambda key: GOALS[key]["label"], key="run_focus_goal",
            help="BASIN will place the related measurements and visuals first in Review.")
        run_focus_data = focus_data_col.selectbox(
            "Which data will you use?", list(DATA_SOURCES),
            format_func=lambda key: DATA_SOURCES[key]["label"], key="run_focus_data",
            help="This records your intent. It does not upload, validate, or replace data.")
        run_focus_guidance = focus_guidance_col.selectbox(
            "Presentation view", list(GUIDANCE),
            format_func=lambda key: GUIDANCE[key]["label"], key="run_focus_guidance",
            help="Simple shows key results. Advanced adds technical controls and diagnostics.")
        run_focus_skip = st.checkbox(
            "Skip tailoring and show every Review tool", key="run_focus_skip",
            help="You can tailor the Review later without losing work.")
        if run_focus_data == "own":
            has_custom = any(s.startswith("LOCAL_") for s in names)
            if has_custom:
                local_name = next(names[s] for s in names if s.startswith("LOCAL_"))
                st.info(f"Custom Gauge Active: Generating scenarios from user-provided dataset '{local_name}' (unverified). {CUSTOM_CATCHMENT_DISCLAIMER}")
            else:
                st.info("Upload your rainfall CSV here to drive scenarios with your own gauge:")
                local_rainfall_preview(expanded=True, as_expander=False)
                st.caption("Tip: You can also explore full NOAA paired-station comparisons in Step 1: Data Dashboard.")
        elif run_focus_data == "example":
            col_ex1, col_ex2 = st.columns([2.5, 1.5])
            col_ex1.caption("The reproducible example pre-loads 6 diverse drought candidates (Seed 22).")
            col_ex2.button("Load Example Run ➔", key="btn_builder_load_example_inline", on_click=start_example, args=(source, names), type="primary", width="stretch")
        elif run_focus_skip:
            st.caption("This run will use the full Review layout. You can choose a focus later in Review.")

    # 1. Upfront Priority Weights & Presets
    with tour_target("sidebar_presets"):
        with st.container(border=True):
            st.markdown("##### ⚖️ Community Priority Presets & Ranking Weights")
            st.caption("Set illustrative community priorities before building scenarios or adjust to rerank existing candidates. The shortlist reflects these operational priorities.")
            preset_options = ["Custom weights"] + list(COMMUNITY_PRESETS.keys())
            matched = "Custom weights"
            curr_weights = dict(w.weights) if w else {"severity": 40, "duration": 30, "concurrence": 20, "season": 10}
            for p_name, p_vals in COMMUNITY_PRESETS.items():
                if curr_weights == p_vals:
                    matched = p_name
                    break
            col_pre1, col_pre2 = st.columns([1.5, 2.5])
            with col_pre1:
                chosen_preset = st.selectbox(
                    "Community priority preset", preset_options,
                    index=preset_options.index(matched),
                    key=f"preset_select_{w.id if w else 'initial'}",
                    help="Biases the shortlist toward your operational priority: 'Crop stress' prioritizes summer deficit; 'Chronic drought' prioritizes duration."
                )
            if chosen_preset != "Custom weights" and chosen_preset != matched:
                new_w = dict(COMMUNITY_PRESETS[chosen_preset])
                for k, v in new_w.items():
                    st.session_state[f"weight_{k}"] = v
                if w:
                    w.rerank(new_w)
                    w.rebuild_shortlist()
                    save(w)
                    st.rerun()

            slider_configs = {
                "severity": ("Deficit severity vs history", "Relative weight for severity (% of historical windows exceeded in rainfall shortfall)."),
                "duration": ("Scenario duration (days)", "Relative weight for duration (favors longer multi-season drought stress periods)."),
                "concurrence": ("Regional station concurrence", "Relative weight for concurrence (favors scenarios where all stations experience synchronized deficits)."),
                "season": ("Summer timing (June–Sept)", "Relative weight for critical warm-season timing (June–September evaporation and crop flowering)."),
            }
            w_cols = st.columns(4)
            weights = {}
            for idx, (k, (lbl, hlp)) in enumerate(slider_configs.items()):
                with w_cols[idx]:
                    val = int(st.session_state.get(f"weight_{k}", curr_weights[k]))
                    weights[k] = st.slider(lbl, 0, 100, val, key=f"weight_{k}", help=hlp)
            if w:
                if sum(weights.values()) == 0:
                    st.error("At least one weight must be positive.")
                elif weights != w.weights:
                    w.rerank(weights)
                    save(w)
                if st.button("Rebuild shortlist from current weights", key=f"btn_rebuild_shortlist_{w.id}", disabled=sum(weights.values()) == 0, width="stretch"):
                    try:
                        w.rebuild_shortlist()
                        save(w)
                        st.success(f"Shortlist rebuilt using updated priorities: {w.weights}")
                        st.rerun()
                    except ValueError as error:
                        st.error(str(error))
            else:
                st.caption("Configured weights will prioritize candidate severity, duration, concurrence, and seasonality during initial generation.")

    # 2. Scenario Generator
    c_gen = st.container()
    with c_gen:
        with tour_target("sidebar_generator"):
            with st.container(border=True):
                st.markdown("##### 🌧️ Build rainfall scenarios")
                stations = st.multiselect(
                    "Stations", list(names),
                    default=list(w.params.stations) if w else list(names), format_func=names.get,
                    help="NOAA First-Order Long-Term Continuous Index Stations (Corpus Christi, Victoria, San Antonio) providing synchronized daily precipitation records spanning 1991–2025.",
                    placeholder="Type a station name or ID",
                )

                default_gen_mode = "analog_search" if (w and not getattr(w.params, "calendar_ranges", ())) else "variations"
                gen_mode = st.radio(
                    "Scenario Generation Mode",
                    ["variations", "analog_search"],
                    index=0 if default_gen_mode == "variations" else 1,
                    format_func=lambda x: "Variations of Selected Historical Window" if x == "variations" else "Multi-Year Historical Analog Search (1991–2025)",
                    key="scenario_gen_mode",
                    help="Choose whether to generate retention variations of one specific historical window, or search across distinct historical dry windows from the 1991–2025 NOAA record."
                )

                calendar_ranges = []
                custom_range_incomplete = False
                source_start_date = pd.Timestamp(source.manifest["start"]).date()
                source_end_date = pd.Timestamp(source.manifest["end"]).date()

                if gen_mode == "variations":
                    saved_ranges = tuple(getattr(w.params, "calendar_ranges", ())) if w else ()
                    if saved_ranges:
                        saved_start = datetime.fromisoformat(saved_ranges[0][0]).date()
                        saved_end = datetime.fromisoformat(saved_ranges[0][1]).date()
                    else:
                        saved_end = source_end_date
                        saved_start = max(source_start_date, source_end_date - timedelta(days=89))
                    selected_dates = st.date_input(
                        "Dates", value=(saved_start, saved_end),
                        min_value=source_start_date, max_value=source_end_date,
                        help="Select historical start and end dates to construct retention variations from.",
                        key="scenario_dates",
                    )
                    custom_range_incomplete = len(selected_dates) != 2
                    if custom_range_incomplete:
                        st.caption("Select both a start and end date.")
                    else:
                        start_date, end_date = selected_dates
                        dur_days = (end_date - start_date).days + 1
                        st.caption(f"📌 **Single Historical Window**: {start_date} to {end_date} ({dur_days} days) · Generates scaled retention variations of this exact historical record.")
                        calendar_ranges.append((
                            datetime.combine(start_date, datetime.min.time()).isoformat(timespec="minutes"),
                            datetime.combine(end_date, datetime.strptime("23:59", "%H:%M").time()).isoformat(timespec="minutes"),
                        ))
                    durations = ((end_date - start_date).days + 1,) if not custom_range_incomplete else (90,)
                    months = (start_date.month,) if not custom_range_incomplete else (1,)
                else:
                    st.info("🔍 **Multi-Year Historical Search**: Scans the 1991–2025 NOAA record for multi-season drought sequences across distinct years and onset seasons.")
                    col_d, col_m = st.columns(2)
                    default_durs = [d for d in [90, 180, 270] if d in [30, 60, 90, 180, 270, 365]]
                    chosen_durs = col_d.multiselect("Search durations (days)", [30, 60, 90, 180, 270, 365], default=default_durs, help="Historical window durations to screen.")
                    chosen_months = col_m.multiselect("Search onset months", list(range(1, 13)), default=[1, 4, 7, 10], format_func=lambda m: calendar.month_name[m], help="Onset months for drought screening windows.")
                    durations = tuple(sorted(chosen_durs)) if chosen_durs else (90, 180, 270)
                    months = tuple(sorted(chosen_months)) if chosen_months else (1, 4, 7, 10)

                with st.form("generate", border=False):
                    retention = st.slider(
                        "Retained rainfall (% of observed rainfall)", 0, 100, (35, 85), 5,
                        help="Retained rainfall percentage (e.g., 70% retained = 30% reduction). Scales historical rainfall downwards within the window.",
                    )
                    extent = st.selectbox(
                        "Where reduced rainfall occurs", ["All stations", "One station", "Mixed"],
                        help="Regional spatial extent: 'All stations' models widespread basin-wide meteorological drought; 'One station' models localized precipitation deficits; 'Mixed' allows varied station stress."
                    )
                    a, b = st.columns(2)
                    count = a.selectbox(
                        "Scenarios to test", [100, 300, 500, 1000], index=1,
                        help="Total historical window variations sampled across the 1991–2025 record before applying multi-criteria ranking."
                    )
                    size = b.selectbox(
                        "Scenarios to review", [3, 4, 6, 8], index=2,
                        help="Number of top-ranked, representative drought candidate profiles shortlisted for engineering review."
                    )
                    seed = st.number_input(
                        "Repeatable run seed", 0, 4294967295, w.params.seed if w else 22,
                        help="Seed integer ensuring exact mathematical repeatability and audit replay across sessions."
                    )
                    generate = st.form_submit_button("Create rainfall scenarios", type="primary", width="stretch")
        if generate:
            if not stations:
                st.error("Select at least one station before generating scenarios.")
            elif custom_range_incomplete:
                st.error("Select both a start and end date.")
            else:
                try:
                    with st.spinner("Computing…"):
                        params = ScenarioParams(
                            tuple(stations), tuple(durations), tuple(months), retention[0]/100,
                            retention[1]/100, extent, count, int(seed),
                            calendar_ranges=tuple(calendar_ranges),
                        )
                        new = Workspace(source, params, size, analysis_context=analysis_context_for_run())
                        if weights and weights != new.weights:
                            new.rerank(weights)
                            new.rebuild_shortlist()
                        if w:
                            new.notes = w.notes
                        st.session_state.workspace = new
                        st.session_state.data_accepted = True
                        st.session_state.scenarios_accepted = True
                        for key in list(st.session_state):
                            if key.startswith(("review_", "note_", "edit_", "swap_", "provider_")):
                                del st.session_state[key]
                        st.session_state.pop("inspect_id", None)
                        st.session_state.pop("packet", None)
                        save(new)
                        run_preferences = ReviewPreferences(
                            goal=run_focus_goal,
                            data_source=run_focus_data,
                            guidance=run_focus_guidance,
                            configured=not run_focus_skip,
                            dismissed=True,
                        )
                        store_review_preferences(new.id, run_preferences)
                    st.rerun()
                except (ValueError, OSError) as error:
                    st.error(str(error))

    # 2. Candidate Shortlist & Diversity Inspection
    if w is not None:
        selected = [w.get(i) for i in w.selected]
        decision_summary(w)
        approved_count = sum(s.status == "accepted" and s.approved_revision == s.revision for s in selected)
        st.caption(f"{len(selected)} scenarios selected for review · {approved_count} approved for export")
        view = table(w)
        st.markdown("**Compare rainfall shortfalls by duration**")
        st.caption("Each dot is a scenario. Panels share the same deficit scale; sideways spacing only separates dots. Rings mark selections for review, diamonds mark each duration's highest deficit, and the square marks the scenario shown in details.")
        plot_area, detail_area = st.columns([4, 1.3], gap="medium")
        with detail_area:
            detail_ids = view["ID"].tolist()
            initial_id = w.selected[0] if w.selected else detail_ids[0]
            focused_id = st.selectbox("Scenario details", detail_ids,
                                      index=detail_ids.index(initial_id), key=f"shortfall_detail_{w.id}")
            detail = view.loc[view["ID"] == focused_id].iloc[0]
            st.caption(f"{detail['Days']:g} days · {detail['Onset']} onset")
            is_us = st.session_state.get("unit_mode", "us") == "us"
            if is_us:
                st.metric("Total rainfall deficit", f"{detail['Deficit in']:,.2f} in", delta=f"{detail['Deficit mm']:,.1f} mm", delta_color="off")
            else:
                st.metric("Total rainfall deficit", f"{detail['Deficit mm']:,.1f} mm", delta=f"{detail['Deficit in']:,.2f} in", delta_color="off")
            st.caption(detail["Profile"])
            concurrence = float(detail["Stations stressed together %"])
            concurrence_label = (
                "30-day windows with all selected stations stressed"
                if len(w.params.stations) > 1
                else "Single Station Drought Stress Persistence"
            )
            st.progress(min(1.0, max(0.0, concurrence / 100)),
                        text=f"{concurrence_label}: {concurrence:.1f}%")
            st.caption("Selected for review" if focused_id in w.selected else "Not selected for review")
            st.button("Open scenario review", key=f"shortfall_review_{w.id}",
                      on_click=open_review, args=(focused_id,))
        with plot_area:
            is_us = st.session_state.get("unit_mode", "us") == "us"
            st.plotly_chart(rainfall_shortfall_figure(
                view, w.selected, focused_id,
                colorblind=st.session_state.get("appearance_colorblind", False),
                unit="in" if is_us else "mm",
            ), width="stretch", config={"displayModeBar": False})
        st.caption("Totals accumulate over the whole scenario. A larger deficit in a longer window does not, by itself, mean greater drought intensity.")

        tab_candidates, tab_cross_compare, tab_ranking, tab_diagnostics = st.tabs([
            "Candidate Scenarios & Filters",
            "Cross-Scenario Comparison",
            "Ranking Score Breakdown",
            "Selection Diagnostics"
        ])
        with tab_candidates:
            a, b, c, d = st.columns([2, 1, 1, 1])
            query = a.text_input("Find scenario", placeholder="Scenario ID")
            group_filter = b.selectbox("Group", ["All"] + sorted(view.Group.unique().tolist()))
            review_filter = c.selectbox("Status", ["All", "unreviewed", "accepted", "rejected"])
            only_selected = d.checkbox("Selected only", value=True)
            filtered = view[view.ID.str.contains(query, case=False, regex=False)].copy()
            if group_filter != "All":
                filtered = filtered[filtered.Group.eq(group_filter)]
            if review_filter != "All":
                filtered = filtered[filtered.Status.eq(review_filter)]
            if only_selected:
                filtered = filtered[filtered["Selected for review"]]
            filtered = filtered.sort_values(["Score", "ID"], ascending=[False, True]).reset_index(drop=True)
            with tour_target("workspace_table"):
                selection = st.dataframe(filtered, hide_index=True, width="stretch", height=min(430, 40+len(filtered)*35),
                                         on_select="rerun", selection_mode="single-row", key=f"candidates_{w.id}")
            rows = selection.selection.rows
            if rows and rows[0] < len(filtered):
                selected_id = filtered.iloc[rows[0]].ID
                st.button(f"Inspect {selected_id}", key=f"btn_inspect_table_{selected_id}", on_click=open_review, args=(selected_id,), type="primary")

        with tab_cross_compare:
            st.markdown("#### Multi-Scenario Shortlist Comparison")
            st.caption("Side-by-side analysis of all shortlisted drought candidates across cumulative rainfall deficit, reservoir drawdown trajectory, and multi-criteria performance metrics.")

            c_sc1, c_sc2, c_sc3, c_sc4 = st.columns(4)
            shortlist_scenarios = [w.get(i) for i in w.selected]
            avg_def = sum(s.features["deficit_mm"] for s in shortlist_scenarios) / len(shortlist_scenarios) if shortlist_scenarios else 0
            max_def = max(s.features["deficit_mm"] for s in shortlist_scenarios) if shortlist_scenarios else 0
            max_dur = max(s.features["duration_days"] for s in shortlist_scenarios) if shortlist_scenarios else 0
            is_us = st.session_state.get("unit_mode", "us") == "us"
            u_txt = "in" if is_us else "mm"
            scale = 1.0 / 25.4 if is_us else 1.0

            c_sc1.metric("Shortlist Pool", f"{len(shortlist_scenarios)} Scenarios")
            c_sc2.metric(f"Avg Deficit ({u_txt})", f"{avg_def * scale:.2f} {u_txt}")
            c_sc3.metric(f"Max Deficit ({u_txt})", f"{max_def * scale:.2f} {u_txt}")
            c_sc4.metric("Max Duration", f"{max_dur} days")

            st.markdown("##### 1. Cumulative Rainfall Deficit Envelope")
            st.caption("Compares the accumulation of meteorological drought stress over elapsed scenario days across all candidates. Shaded envelope shows the min–max range across the shortlist; dashed line indicates the shortlist average trajectory.")
            st.plotly_chart(
                accessible_chart(shortlist_cumulative_deficit_figure(w, unit="in" if is_us else "mm", highlight_id=st.session_state.get("inspect_id"))),
                width="stretch", config={"displayModeBar": True}
            )

            st.markdown("##### 2. Reservoir Drawdown Simulation Overlay")
            st.caption("Synchronized combined storage (% of capacity) for all shortlisted scenarios under standard baseline assumptions (48% initial storage, 0% conservation, pipeline active). Stage 1 (40%), Stage 2 (30%), Critical Reserve (20%), and Emergency (15%) bands indicated.")
            st.plotly_chart(
                accessible_chart(multi_scenario_storage_figure(w, initial_pct=0.48, conservation_pct=0.0, pipeline_active=True, unit="us" if is_us else "metric", highlight_id=st.session_state.get("inspect_id"))),
                width="stretch", config={"displayModeBar": True}
            )

            st.markdown("##### 3. Comprehensive Shortlist Scorecard Matrix")
            st.caption("Unified multi-criteria comparison matrix detailing shortfall magnitude, monthly deficit rate, historical rarity, threshold breach milestones, and ranking contribution.")
            scorecard_df = build_shortlist_scorecard(w, initial_pct=0.48, conservation_pct=0.0, pipeline_active=True, unit="us" if is_us else "metric")
            st.dataframe(scorecard_df, hide_index=True, width="stretch")
            st.download_button("Download shortlist scorecard (CSV)", scorecard_df.to_csv(index=False), file_name="basin_shortlist_scorecard.csv", mime="text/csv")

        with tab_ranking:
            st.markdown("**How Ranking Scores Are Calculated**")
            st.caption("Contribution of severity, duration, concurrence, and season weights to each candidate's priority score.")
            fig = go.Figure()
            for key in w.weights:
                fig.add_trace(go.Bar(name=key.title(), y=[s.id for s in selected], x=[s.components[key] for s in selected], orientation="h"))
            fig.update_layout(barmode="stack")
            fig.update_xaxes(range=[0,100], title="Contribution to ranking score")
            st.plotly_chart(chart(fig, 290), width="stretch", config={"displayModeBar": False})

        with tab_diagnostics:
            st.markdown("**Selection Diagnostics & Algorithm Clustering**")
            st.dataframe(pd.DataFrame(comparison(w.scenarios, w.selected, w.params.seed)), hide_index=True, width="stretch")
            st.json({"clustering": w.clustering, "generation": w.generation, "selection_history": w.selection_history})

        comparison_panel(w, save)

        def accept_shortlist():
            st.session_state.scenarios_accepted = True
            open_review(w.selected[0])

        render_bottom_nav(
            prev_page="Data",
            next_page="Review",
            next_label="Confirm Shortlist & Proceed to Step 3",
            next_disabled=False,
            on_next=accept_shortlist,
            note=f"Candidate Shortlist Confirmed ({len(w.selected)} Scenarios)"
        )
    else:
        st.info("💡 Configure settings above and click 'Create rainfall scenarios' (or 'Try an example') to generate candidates.")
        render_bottom_nav(
            prev_page="Data",
            next_page=None,
            next_label=""
        )

elif page == "Review":
    if w is None:
        st.info("💡 **No Active Analysis Run**: To review drought scenarios, first configure and start a run in **Scenario Builder**.")
        st.button("➔ Go to Step 2: Scenario Builder", key="btn_review_to_workspace_empty", on_click=switch_page, args=("Workspace",), type="primary")
    else:
        context = w.analysis_context
        st.info(
            f"**Screening for:** {context.audience_label} · **Service area:** {context.county_label} · "
            f"**Purpose:** {DECISION_USES[context.decision_use]}. "
            "This identifies the intended decision context; gauge suitability and local system calibration still require review."
        )
        prefs = review_preferences(w.id)
        if st.session_state.get("crisis_demo", False):
            st.caption("2026 crisis demo · 7.7% is the April 2026 starting-storage context; the selected rainfall sequence and resulting trajectory are illustrative.")

        is_editing = st.session_state.get(f"review_editing_{w.id}", False)
        if prefs.needs_setup or is_editing:
            with st.container(border=True):
                st.markdown("#### Set up this Review (optional)")
                st.caption("Simple View supports quick decisions. Advanced View adds full diagnostics.")
                setup_goal, setup_data, setup_guide = st.columns(3)
                chosen_goal = setup_goal.radio(
                    "What are you trying to do?", list(GOALS),
                    format_func=lambda key: GOALS[key]["label"],
                    captions=[GOALS[key]["help"] for key in GOALS], key="review_setup_goal")
                chosen_data = setup_data.radio(
                    "Which data will you use?", list(DATA_SOURCES),
                    format_func=lambda key: DATA_SOURCES[key]["label"],
                    captions=[DATA_SOURCES[key]["help"] for key in DATA_SOURCES], key="review_setup_data")
                chosen_guidance = setup_guide.radio(
                    "Presentation view", list(GUIDANCE),
                    format_func=lambda key: GUIDANCE[key]["label"],
                    captions=[GUIDANCE[key]["help"] for key in GUIDANCE], key="review_setup_guidance")
                if chosen_data == "own":
                    st.warning("This choice only records a preference; it does not upload or validate a file. "
                               "Existing data is unchanged. Add and review a CSV in Step 1: Data Dashboard when you are ready.")
                if chosen_data == "example":
                    st.caption("The example run opens from Step 1 or Step 2 using the existing 'Try an example' control.")
                if is_editing:
                    apply_col, cancel_col, skip_col = st.columns([1, 1, 1])
                    if apply_col.button("Use this focus", key="btn_review_setup_apply", type="primary", width="stretch"):
                        st.session_state[f"review_editing_{w.id}"] = False
                        store_review_preferences(w.id, prefs.replace(
                            goal=chosen_goal, data_source=chosen_data, guidance=chosen_guidance,
                            configured=True, dismissed=True))
                        st.rerun()
                    if cancel_col.button("Cancel", key="btn_review_setup_cancel", width="stretch"):
                        st.session_state[f"review_editing_{w.id}"] = False
                        st.rerun()
                    if skip_col.button("Skip for now", key="btn_review_setup_skip", width="stretch"):
                        st.session_state[f"review_editing_{w.id}"] = False
                        store_review_preferences(w.id, prefs.replace(configured=False, dismissed=True))
                        st.rerun()
                else:
                    apply_col, skip_col, _ = st.columns([1, 1, 2])
                    if apply_col.button("Use this focus", key="btn_review_setup_apply", type="primary", width="stretch"):
                        store_review_preferences(w.id, prefs.replace(
                            goal=chosen_goal, data_source=chosen_data, guidance=chosen_guidance,
                            configured=True, dismissed=True))
                        st.rerun()
                    if skip_col.button("Skip for now", key="btn_review_setup_skip", width="stretch"):
                        store_review_preferences(w.id, prefs.replace(dismissed=True))
                        st.rerun()
        else:
            u_bar_l, u_bar_r = st.columns([2.2, 1.8])
            with u_bar_l:
                st.caption(f"**Focus**: {prefs.summary()}")
                if prefs.configured and prefs.data_source == "own":
                    st.caption("Custom data selected. Upload and validate a CSV in Data Dashboard.")
                suggested = prefs.suggested_preset()
                if suggested and prefs.advanced:
                    st.caption(f"Tip: this focus pairs well with *{suggested}* in Scenario Builder.")
            with u_bar_r:
                btn_c1, btn_c2 = st.columns([1.5, 1])
                with btn_c1:
                    if hasattr(st, "segmented_control"):
                        chosen_mode = st.segmented_control(
                            "View mode", list(PRESENTATION_MODES), default=prefs.mode,
                            format_func=lambda key: PRESENTATION_MODES[key]["label"],
                            key=f"review_mode_{w.id}",
                            label_visibility="collapsed",
                        )
                    else:
                        chosen_mode = st.radio(
                            "View mode", list(PRESENTATION_MODES), index=list(PRESENTATION_MODES).index(prefs.mode),
                            format_func=lambda key: PRESENTATION_MODES[key]["label"], horizontal=True,
                            key=f"review_mode_{w.id}",
                            label_visibility="collapsed",
                        )
                    if chosen_mode and chosen_mode != prefs.mode:
                        prefs = prefs.replace(mode=chosen_mode)
                        store_review_preferences(w.id, prefs)
                        st.rerun()
                with btn_c2:
                    if st.button("Change focus", key=f"btn_review_change_focus_{w.id}", width="stretch"):
                        st.session_state[f"review_editing_{w.id}"] = True
                        st.session_state["review_setup_goal"] = prefs.goal
                        st.session_state["review_setup_data"] = prefs.data_source
                        st.session_state["review_setup_guidance"] = prefs.guidance
                        st.rerun()

        simple_view = prefs.simple

        col_scen_sel, col_scen_opt = st.columns([3, 1])
        show_all_candidates = col_scen_opt.checkbox("Show all candidates", value=False, key=f"review_show_all_{w.id}", help="Expand dropdown beyond the 6 shortlisted candidates to all generated candidates")
        if show_all_candidates:
            candidates = w.selected + [s.id for s in w.scenarios if s.id not in w.selected]
        else:
            candidates = list(w.selected)
            current_inspect = st.session_state.get("inspect_id")
            if current_inspect and current_inspect not in candidates and w.has(current_inspect):
                candidates.insert(0, current_inspect)
        current = st.session_state.get("inspect_id", candidates[0])
        if current not in candidates:
            current = candidates[0]
        selected_id = col_scen_sel.selectbox("Scenario", candidates, index=candidates.index(current),
                                             format_func=lambda i: f"{i} · {w.get(i).status} · r{w.get(i).revision}" + (" · shortlisted" if i in w.selected else ""))
        st.session_state.inspect_id = selected_id
        s = w.get(selected_id)
        f = s.features
        is_us = st.session_state.get("unit_mode", "us") == "us"
        unit_arg = "in" if is_us else "mm"

        # Top section: Scenario overview and review decision side-by-side
        top_left, top_right = st.columns([2.1, 1.4], gap="large")
        with top_left:
            st.markdown(f"### Understand Scenario {s.id}")
            factors = list(s.provenance['retention_by_station'].values())
            if min(factors) == max(factors):
                construction = f"Original construction retained {format_rainfall_dual_explanation(factors[0], 'observed rainfall')} at every station."
            else:
                min_ret = round(min(factors) * 100, 1)
                max_ret = round(max(factors) * 100, 1)
                min_red = round((1.0 - max(factors)) * 100, 1)
                max_red = round((1.0 - min(factors)) * 100, 1)
                construction = f"Original construction retained {min_ret:g}%–{max_ret:g}% of observed rainfall ({min_red:g}%–{max_red:g}% reduction from observed rainfall), depending on station."
            rainfall_edits = any(h['action'] in ('scale', 'replace') for h in s.history)

            st.caption(f"Historical source window: **{s.provenance['source_start']}** to **{s.provenance['source_end']}** ({f['duration_days']} days · {len(s.series.columns)} index stations)")

            # Structured 4-metric overview grid
            c_sc1, c_sc2, c_sc3, c_sc4 = st.columns(4)
            shortfall_disp = f"{f['deficit_mm']/25.4:.2f} in" if is_us else f"{f['deficit_mm']:.1f} mm"
            shortfall_sub = f"{f['deficit_mm']:.1f} mm" if is_us else f"{f['deficit_mm']/25.4:.2f} in"
            c_sc1.metric("Mean Shortfall", shortfall_disp, f"({shortfall_sub})")

            pct_val = f"{f['historical_percentile']*100:.0f}%"
            c_sc2.metric("Historical Severity", f"≥ {pct_val}", f"Rank vs {f['benchmark_n']} windows")

            conc_val = f"{f['concurrence']*100:.0f}%"
            c_sc3.metric("Station Concurrence", conc_val, "Widespread stress")

            dry_val = f"{f.get('max_dry_days', 0)} days"
            c_sc4.metric("Longest Dry Run", dry_val, "< 1 mm/day")

            with st.container(border=True):
                st.markdown("**Rainfall Screening Summary**")
                st.markdown(scenario_summary(f, names, unit_system=st.session_state.get("unit_mode", "us")))
                st.markdown("---")
                st.markdown("**Factual Construction & Climatological Baseline**")
                st.markdown(f"• **Precipitation Baseline:** {construction}" + (" (Includes later rainfall edits; see revision history.)" if rainfall_edits else ""))
                st.markdown(f"• **Climatological Reference:** Net rainfall deficit equals or exceeds **{pct_val}** of {f['benchmark_n']} matched historical windows with the same duration and starting month (1991–2020 NOAA reference baseline).")
                st.markdown(f"• **Spatial Scope:** Direct observations from NOAA index stations (Corpus Christi, Victoria, San Antonio) weighted equally across the regional basin.")

        with top_right:
            with tour_target("review_decision"):
                st.markdown("### Decide on the handoff")
                status_label = {"accepted": "🟢 Included", "rejected": "🔴 Excluded", "unreviewed": "🟡 Needs review"}[s.status]
                if s.status == "accepted" and s.approved_revision != s.revision:
                    status_label = "🟡 Needs review of current revision"
                st.write(f"**{s.id} · Revision {s.revision} · {status_label}**")
                pending = [i for i in w.selected if w.get(i).status == 'unreviewed' or
                           (w.get(i).status == 'accepted' and w.get(i).approved_revision != w.get(i).revision)]
                st.caption(f"{len(w.selected) - len(pending)} of {len(w.selected)} shortlisted scenarios reviewed")
                attached = set(w.evidence_refs[s.id])
                conflicts = [c for c in w.conflicts if c['status'] == 'unresolved' and
                             (c['left_id'] in attached or c['right_id'] in attached)]
                for conflict in conflicts:
                    st.warning("Unresolved evidence issue: " + conflict['disagreement'])
                note_key = f"note_{s.id}_{w.id}"
                if note_key not in st.session_state:
                    prior_note = None
                    if s.history:
                        for ev in reversed(s.history):
                            if ev.get("private_note"):
                                prior_note = ev["private_note"]
                                break
                    if prior_note:
                        st.session_state[note_key] = prior_note
                    else:
                        st.session_state[note_key] = ""

                note = st.text_area("Review note", key=note_key, height=100,
                                    help="Record your own reason for including or excluding this revision. Notes are private unless explicitly included during export.")
                valid_review_note = len(note.strip()) >= 20
                if not valid_review_note:
                    st.caption("Add at least 20 characters of your own rationale to enable Include or Exclude.")
                st.caption("Inclusion records your choice of rainfall content. It does not certify hydrologic validity or approve the storage experiment.")
                if s.id not in w.selected:
                    st.info("This candidate is outside the shortlist. Use Edit Rainfall & Refine Shortlist below to replace an entry first.")
                include_col, exclude_col = st.columns(2)
                with include_col:
                    if st.button("Include", key=f"btn_accept_{s.id}_{s.revision}",
                                 type="primary", width="stretch", disabled=s.id not in w.selected or not valid_review_note,
                                 help="Include this revision in the handoff."):
                        s.review(True, note)
                        save(w)
                        st.rerun()
                with exclude_col:
                    if st.button("Exclude", key=f"btn_reject_{s.id}_{s.revision}", width="stretch", disabled=s.id not in w.selected or not valid_review_note,
                                 help="Exclude this revision from the handoff."):
                        try:
                            s.review(False, note)
                            save(w)
                            st.rerun()
                        except ValueError as error:
                            st.error(str(error))
                remaining = [i for i in pending if i != s.id]
                st.button("Next scenario", disabled=not remaining,
                          on_click=open_review, args=(remaining[0] if remaining else s.id,), width="stretch")

        with st.expander("Method and limitations", expanded=False):
            st.markdown(
                "**Catchment Weighting Disclosure:** BASIN currently weights the selected NOAA index "
                "stations equally. This supports regional rainfall screening; it is not calibrated catchment weighting."
            )
            st.markdown(
                "A historical rank describes matched windows in the available observation record. "
                "It is not the probability of a future drought."
            )

        primary_keys, secondary_keys = prefs.primary_panes(), prefs.secondary_panes()
        if simple_view and secondary_keys:
            panes = dict(zip(primary_keys, st.tabs([TAB_LABELS[key] for key in primary_keys])))
            with st.expander(
                f"More tools ({len(secondary_keys)})",
                expanded=curr_target == "review_simulation" and "storage" in secondary_keys,
            ):
                st.caption("Secondary tools outside active focus profile.")
                panes.update(zip(secondary_keys, st.tabs([TAB_LABELS[key] for key in secondary_keys])))
        else:
            all_tool_keys = list(prefs.primary_panes()) + [k for k in prefs.secondary_panes() if k not in prefs.primary_panes()]
            panes = dict(zip(all_tool_keys, st.tabs([TAB_LABELS[key] for key in all_tool_keys])))
        if prefs.guided and prefs.configured:
            for pane_key, pane in panes.items():
                with pane:
                    st.caption(GUIDED_TAB_NOTES[pane_key])
        tab_storage = panes["storage"]
        tab_agro = panes["agronomics"]
        tab_rainfall = panes["rainfall"]
        tab_edits = panes["edits"]
        tab_provenance = panes["provenance"]

        with tab_storage:
            experiment = st.toggle("Explore storage under assumed conditions", value=curr_target == "review_simulation" or st.session_state.get("storage_experiment", False),
                                   key="storage_experiment", help="Show the optional storage experiment and its assumptions.")
            if experiment:
                with st.container(border=True):
                    st.caption("Optional illustrative storage experiment.")

                    st.markdown("##### 💧 Water Storage System")
                    sys_options = list(SYSTEM_PRESETS.keys()) + ["Custom System Configuration..."]
                    active_selection = w.water_system_selection
                    selected_label = SYSTEM_ID_TO_LABEL.get(active_selection.identifier, "Custom System Configuration...")

                    # Rural / farm / district persona alignment
                    org_type = getattr(w.analysis_context, "organization_type", "")
                    org_name = getattr(w.analysis_context, "organization_name", "").lower()
                    is_rural_or_district = org_type in ("rural_provider", "water_district") or any(
                        kw in org_name for kw in ("farm", "ranch", "irrigation", "wcid", "mud", "rural")
                    )
                    if f"sys_preset_choice_{w.id}" not in st.session_state and selected_label == SYSTEM_ID_TO_LABEL.get(DEFAULT_WATER_SYSTEM_ID):
                        if is_rural_or_district:
                            selected_label = "Rural Farm Pond (1.5k ac-ft)" if any(k in org_name for k in ("farm", "ranch", "irrigation")) else "Small Municipal District (12k ac-ft)"
                            st.session_state[f"sys_preset_choice_{w.id}"] = selected_label

                    curr_sys_choice = st.session_state.get(f"sys_preset_choice_{w.id}", selected_label)
                    sys_choice = st.selectbox("Storage Infrastructure", sys_options,
                                              index=sys_options.index(curr_sys_choice) if curr_sys_choice in sys_options else 0,
                                              key=f"sys_preset_choice_{w.id}",
                                              help="Select a regional preset or configure custom storage pools and demand for your local district or farm.")

                    if sys_choice == "Custom System Configuration...":
                        st.markdown("**Custom Infrastructure Setup**")
                        custom_default = active_selection.config if active_selection.identifier == "custom" else None
                        c_cname, c_csrcs, c_cdemand = st.columns([2, 1, 1])
                        cust_name = c_cname.text_input("System / District Name", value=custom_default.name if custom_default else "Local Water District", key=f"cust_sys_name_{w.id}")
                        default_count = len(custom_default.sources) if custom_default else 1
                        cust_n_sources = c_csrcs.selectbox("Number of Storage Pools", [1, 2, 3], index=default_count - 1, key=f"cust_sys_n_{w.id}")
                        cust_demand = c_cdemand.number_input("Daily Demand (ac-ft/day)", min_value=0.1, value=float(custom_default.demand_acft_day) if custom_default else 12.0, step=1.0, key=f"cust_sys_demand_{w.id}")

                        src_list = []
                        for s_idx in range(cust_n_sources):
                            col_sn, col_scap = st.columns([2, 2])
                            saved_source = custom_default.sources[s_idx] if custom_default and s_idx < len(custom_default.sources) else None
                            s_name = col_sn.text_input(f"Source {s_idx+1} Name", value=saved_source.name if saved_source else f"Storage Pool {s_idx+1}", key=f"cust_src_name_{w.id}_{s_idx}")
                            s_cap = col_scap.number_input(f"Capacity (ac-ft)", min_value=1.0, value=float(saved_source.capacity_acft) if saved_source else (8000.0 if s_idx == 0 else 4000.0), step=100.0, key=f"cust_src_cap_{w.id}_{s_idx}")
                            src_list.append(WaterSource.scaled_for_capacity(s_name, float(s_cap)))
                        # No separate no-pipeline demand is collected for a custom system. Leaving the
                        # dataclass default would silently switch to the regional 554 ac-ft/day.
                        chosen_sys = WaterSystemConfig(name=cust_name, sources=tuple(src_list), demand_acft_day=float(cust_demand),
                                                       demand_no_pipeline_acft_day=None)
                        chosen_system_id = "custom"
                    else:
                        chosen_sys = SYSTEM_PRESETS[sys_choice]
                        chosen_system_id = SYSTEM_LABEL_TO_ID[sys_choice]
                    w.select_water_system(chosen_sys, chosen_system_id)

                    previous_config = st.session_state.get("experiment_config")
                    if isinstance(previous_config, ExperimentConfig) and previous_config.selected:
                        restored_settings = {
                            "review_initial_storage": f"{previous_config.initial_pct * 100:.0f}% (illustrative)",
                            "review_conservation": int(round(previous_config.conservation_pct * 100)),
                            "review_pipeline_active": previous_config.pipeline_active,
                        }
                        for key, value in restored_settings.items():
                            if key not in st.session_state:
                                st.session_state[key] = value

                    simple_view = prefs.simple if f"view_mode_{w.id}" not in st.session_state else (st.session_state.get(f"view_mode_{w.id}") == "Simple View")
                    if simple_view:
                        sim_subview = "Selected scenario"
                        pace_ms = 150
                        init_choice = st.session_state.get("review_initial_storage", "48% (illustrative)")
                        conserve_choice = int(st.session_state.get("review_conservation", 0))
                        pipeline_active = bool(st.session_state.get("review_pipeline_active", True))
                        pipe_desc = f"pipeline {'available' if pipeline_active else 'unavailable'}" if chosen_sys.demand_no_pipeline_acft_day is not None else "no pipeline required"
                        st.caption(
                            f"{init_choice.split()[0]} starting storage · {conserve_choice}% demand reduction · "
                            f"{pipe_desc}. Choose Advanced View to change assumptions."
                        )
                    else:
                        sim_subview = st.radio(
                            "Simulation view", ["Selected scenario", "Additional rainfall reductions"],
                            horizontal=True, key="reservoir_sim_subview")
                        c_pace, c_init, c_conserve = st.columns([1, 1, 1])
                        pace_choice = c_pace.selectbox("Playback pace", ["Slow", "Medium", "Fast"])
                        pace_ms = 2500 if pace_choice == "Slow" else (800 if pace_choice == "Medium" else 150)
                        initial_storage_options = [
                            "48% (illustrative)",
                            "60% (illustrative)",
                            "35% (illustrative)",
                            "7.7% (April 2026 context)",
                        ]
                        init_choice = c_init.selectbox("Initial storage", initial_storage_options, key="review_initial_storage")
                        conserve_choice = c_conserve.select_slider("Demand reduction", options=[0, 10, 20, 30], value=0, format_func=lambda v: f"{v}%", key="review_conservation")
                        if chosen_sys.demand_no_pipeline_acft_day is not None:
                            pipeline_active = st.checkbox("Pipeline supply available (Mary Rhodes Pipeline)", value=True, key="review_pipeline_active")
                        else:
                            pipeline_active = True
                            st.caption("ℹ️ *Pipeline import is specific to regional municipal utilities (not applicable to this storage system).*")
                    init_pct = {
                        "48% (illustrative)": 0.48,
                        "60% (illustrative)": 0.60,
                        "35% (illustrative)": 0.35,
                        "7.7% (April 2026 context)": 0.077,
                    }[init_choice]

                    settings = SimulationSettings(
                        initial_storage_fraction=init_pct,
                        conservation_fraction=conserve_choice / 100.0,
                        pipeline_active=pipeline_active,
                    )
                    preview_run = w.preview_simulation(s.id, settings)
                    active_run = w.active_simulation(s.id)
                    if active_run is not None and active_run["id"] != preview_run["id"]:
                        w.active_simulations.pop(s.id, None)
                        active_run = None
                    reviewed_run = (
                        active_run is not None
                        and active_run["id"] == preview_run["id"]
                        and active_run["id"] in w.simulation_reviews
                    )
                    spec = spectrum_view(preview_run)

                    # Preserve one configuration across Review, assistant, reports and replay.
                    st.session_state["experiment_config"] = ExperimentConfig(
                        initial_pct=init_pct,
                        conservation_pct=conserve_choice / 100.0,
                        pipeline_active=pipeline_active,
                        scenario_id=s.id,
                        scenario_revision=s.revision,
                        selected=True,
                        saved_run_id=preview_run["id"] if reviewed_run else None,
                        system_config=chosen_sys,
                    )
                    if not simple_view:
                        st.caption(f"Configured for **{chosen_sys.name}** ({chosen_sys.total_capacity_acft:,.0f} ac-ft capacity, {chosen_sys.demand_acft_day:,.1f} ac-ft/day demand). Review and the assistant use this selection. Preview `{preview_run['id'][:16]}…` is saved when its review is recorded.")
                    st.info("**Illustrative experiment:** conditional storage under assumed inputs. It is not calibrated or forecast.")

                    if reviewed_run:
                        st.success("This exact system, rainfall revision and settings have a recorded experiment review.")
                    else:
                        simulation_rationale = st.text_input(
                            "Review note",
                            placeholder="What did you check?",
                            key=f"simulation_rationale_{preview_run['id']}",
                        )
                        if st.button("Save experiment review", key=f"review_simulation_{preview_run['id']}"):
                            try:
                                saved_run = w.run_simulation(s.id, settings)
                                w.review_simulation(saved_run["id"], simulation_rationale)
                                st.rerun()
                            except ValueError as error:
                                st.error(str(error))

                    if sim_subview == "Additional rainfall reductions":
                        st.plotly_chart(accessible_chart(stress_spectrum_figure(spec)), width="stretch", config={"displayModeBar": False})

                        st.markdown("**Time spent in assumed storage bands**")
                        st.caption(f"Colors show storage bands during the simulated window ({', '.join(f'{b*100:.0f}%' for b in chosen_sys.stage_bands_pct)}). These boundaries are experiment assumptions, not official restriction triggers.")
                        st.plotly_chart(accessible_chart(stage_trigger_milestone_figure(spec, chosen_sys.stage_bands_pct)), width="stretch", config={"displayModeBar": False})

                        # Describe only the tested window and threshold crossings.
                        input_rainfall = describe_input_rainfall(s, "scenario_revision", s.revision)
                        passed = [r for r in spec["summary_table"] if r["day_stage3_20"] is None]
                        failed = [r for r in spec["summary_table"] if r["day_stage3_20"] is not None]
                        crit_pct = chosen_sys.stage_bands_pct[2] * 100 if len(chosen_sys.stage_bands_pct) >= 3 else 20.0
                        if passed and failed:
                            lowest_pass = min(passed, key=lambda x: x["retention_pct"])
                            highest_fail = max(failed, key=lambda x: x["retention_pct"])
                            st.warning(
                                f"During this {len(s.series)}-day experiment, storage stays above {crit_pct:.0f}% with **{lowest_pass['retention_pct']:g}% of the selected scenario rainfall** ({lowest_pass['reduction_pct']:g}% reduction), "
                                f"and reaches the assumed {crit_pct:.0f}% band with **{highest_fail['retention_pct']:g}% of the selected scenario rainfall** ({highest_fail['reduction_pct']:g}% reduction) ({threshold_day_label(highest_fail['day_stage3_20'])}). Only these tested reductions are compared."
                            )
                        elif not failed:
                            st.success(f"Storage stays above the assumed {crit_pct:.0f}% band throughout this {len(s.series)}-day window for all tested rainfall inputs.")
                        else:
                            highest_fail = max(failed, key=lambda x: x["retention_pct"])
                            st.warning(f"All tested inputs reach the assumed {crit_pct:.0f}% band within this window. The {highest_fail['retention_pct']:g}% of input rainfall tier ({highest_fail['reduction_pct']:g}% reduction) reaches it at {threshold_day_label(highest_fail['day_stage3_20'])}.")

                        countdown_df = pd.DataFrame([
                            {
                                "Rainfall input": r["tier_label"],
                                "Retained % of selected scenario": f"{r['retention_pct']:g}% retained ({r['reduction_pct']:g}% reduction)",
                                "≈ % of observed rainfall": (f"{observed_percent(r['tier_multiplier'], input_rainfall):g}% retained ({round(100 - observed_percent(r['tier_multiplier'], input_rainfall), 1):g}% reduction)"
                                                            if input_rainfall["observed_fraction"] is not None else "n/a"),
                                "Lowest Storage": f"{r['min_pct']:.1f}% ({r['min_acft']:,.0f} ac-ft)",
                                "Final Storage": f"{r['final_pct']:.1f}%",
                                "At or below 40%": threshold_day_label(r["day_stage1_40"]),
                                "At or below 30%": threshold_day_label(r["day_stage2_30"]),
                                "At or below 20%": threshold_day_label(r["day_stage3_20"]),
                                "Critical band": "Not reached in window" if r["day_stage3_20"] is None else "Reached in window",
                                "Active-storage / inactive-storage marker": (
                                    f"Day {r['day_zero']}" if r.get("day_zero") is not None
                                    else f"Day {r['day_dead_storage']}" if r.get("day_dead_storage") is not None
                                    else "Not reached"
                                ),
                            }
                            for r in spec["summary_table"]
                        ])
                        st.dataframe(countdown_df, hide_index=True, width="stretch")
                        st.caption(f"100% means the selected scenario: {input_rainfall['summary']}. Other inputs reduce that rainfall again; they do not reconstruct the original historical observations. Day 0 means storage was already at or below that band at the start.")
                    else:
                        sim_df = spec["tier_results"][1.0]["df"]

                        with tour_target("review_simulation"):
                            st.markdown("#### Combined storage")
                            st.caption("⚠️ **Uncalibrated Toy Mass-Balance Planning Model**: Illustrative mathematical simulation under fixed evaporation and inflow coefficients. Not a safe-yield forecast; does not determine statutory drought stages or restriction dates.")
                            if simple_view:
                                st.plotly_chart(accessible_chart(storage_trajectory_figure(sim_df, chosen_sys.stage_bands_pct)), width="stretch", config={"displayModeBar": False})
                            else:
                                st.caption("Use playback or the day slider to inspect storage by source and combined pool.")
                                st.plotly_chart(accessible_chart(reservoir_simulation_figure(sim_df, pace_ms=pace_ms, config=chosen_sys)), width="stretch", config={"displayModeBar": False})
                                st.markdown("#### Time in each storage band")
                                st.plotly_chart(accessible_chart(stage_trigger_milestone_figure({"tier_results": {1.0: {"df": sim_df}}}, chosen_sys.stage_bands_pct)), width="stretch", config={"displayModeBar": False})

                        # Active-storage exhaustion in the configured experiment.
                        if sim_df["is_day_zero"].any():
                            day_zero_val = int(sim_df.loc[sim_df["is_day_zero"], "day"].iloc[0])
                            st.error(
                                f"**Modeled active-storage limit reached on Day {day_zero_val}.** The configured inactive-storage "
                                f"assumption prevents further withdrawals; cumulative unmet modeled demand is "
                                f"**{sim_df['unmet_demand_acft'].sum():,.0f} ac-ft** in this window."
                            )
                        elif (chosen_sys.context_storage_marker_pct is not None
                              and sim_df["combined_pct"].min() <= chosen_sys.context_storage_marker_pct * 100):
                            marker_pct = chosen_sys.context_storage_marker_pct * 100
                            st.warning(f"Modeled storage falls below the preset's configured {marker_pct:g}% comparison marker, reaching **{sim_df['combined_pct'].min():.1f}%**. The marker is context, not a calibrated limit.")

                        # Same inclusive rule as the spectrum, tools and PDF, including day 0.
                        bands = chosen_sys.stage_bands_pct
                        band_1 = (bands[0] if len(bands) >= 1 else 0.40) * 100
                        band_2 = (bands[1] if len(bands) >= 2 else 0.30) * 100
                        band_crit = (bands[2] if len(bands) >= 3 else 0.20) * 100
                        s1 = threshold_crossing_day(sim_df, init_pct, band_1)
                        s2 = threshold_crossing_day(sim_df, init_pct, band_2)
                        s_crit = threshold_crossing_day(sim_df, init_pct, band_crit)

                        if s_crit is not None:
                            st.markdown(f'''<div class="basin-callout-card alert" style="border-left: 5px solid #dc2626;">
                                <div class="metric-label">🔴 Decision Metric · Critical Storage Breach (≤{band_crit:.0f}%)</div>
                                <div class="metric-val" style="color: var(--basin-danger-text); font-size: 1.4rem; font-weight: 800;">Day {s_crit}</div>
                                <div class="metric-desc">Critical threshold crossed: modeled combined storage reaches or breaches the {band_crit:.0f}% emergency planning band on Day {s_crit}.</div>
                            </div>''', unsafe_allow_html=True)
                        else:
                            st.markdown(f'''<div class="basin-callout-card" style="border-left: 5px solid #16a34a;">
                                <div class="metric-label">🟢 Decision Metric · Critical Storage Breach (≤{band_crit:.0f}%)</div>
                                <div class="metric-val" style="color: var(--basin-success-text); font-size: 1.4rem; font-weight: 800;">Not Breached in Window</div>
                                <div class="metric-desc">Modeled combined storage stays above the {band_crit:.0f}% emergency band throughout this {len(sim_df)}-day window.</div>
                            </div>''', unsafe_allow_html=True)

                        term = sim_df.iloc[-1]
                        metric_columns = st.columns(3 if simple_view else 4)
                        m1, m2, m3 = metric_columns[:3]
                        m1.metric("Storage at window end", f"{term['combined_pct']:.1f}%")
                        m2.metric("Lowest storage", f"{sim_df['combined_pct'].min():.1f}%")
                        m3.metric(f"At or below {band_1:g}%", threshold_day_label(s1))
                        if not simple_view:
                            m1.caption(f"{term['combined_acft']:,.0f} ac-ft combined")
                            metric_columns[3].metric(f"At or below {band_2:g}%", threshold_day_label(s2))

                        # Multi-Sector Delivery Breakdown
                        if not simple_view and "served_domestic_acft" in sim_df.columns and sim_df["served_demand_acft"].sum() > 0:
                            st.markdown("##### 👥 Multi-Sector Water Delivery")
                            sec1, sec2, sec3 = st.columns(3)
                            sec1.metric("Domestic category", f"{sim_df['served_domestic_acft'].sum():,.0f} ac-ft")
                            sec2.metric("Industrial category", f"{sim_df['served_industrial_acft'].sum():,.0f} ac-ft")
                            sec3.metric("Outdoor category", f"{sim_df['served_outdoor_acft'].sum():,.0f} ac-ft")
                            st.caption("Category shares and curtailments are preset assumptions, not observed deliveries or adopted allocations.")

                        # Demand-Policy Comparison (Sector Curtailment)
                        if not simple_view and len(chosen_sys.stage_bands_pct) >= 4:
                            with st.expander("⚖️ Demand-policy comparison (sector curtailment)", expanded=False):
                                comp = compare_demand_curtailment_policies(
                                    s.series,
                                    initial_pct=init_pct,
                                    conservation_pct=conserve_choice / 100.0,
                                    pipeline_active=pipeline_active,
                                    config=chosen_sys,
                                )

                                def _fmt_comp_day(d):
                                    return f"Day {d}" if d is not None else "Not reached in window"

                                def _fmt_comp_delta_day(d):
                                    if d is None:
                                        return "—"
                                    return f"+{d} days" if d > 0 else (f"{d} days" if d < 0 else "0 days")

                                comp_table = pd.DataFrame([
                                    {
                                        "Modeled Output": f"Critical band (≤{comp['crit_band_pct']:.0f}%) reached",
                                        comp["configured_label"]: _fmt_comp_day(comp["crit_day_configured"]),
                                        comp["flat_label"]: _fmt_comp_day(comp["crit_day_flat"]),
                                        "Delta": _fmt_comp_delta_day(comp["crit_day_delta"]),
                                    },
                                    {
                                        "Modeled Output": "Active-storage limit reached",
                                        comp["configured_label"]: _fmt_comp_day(comp["active_limit_day_configured"]),
                                        comp["flat_label"]: _fmt_comp_day(comp["active_limit_day_flat"]),
                                        "Delta": _fmt_comp_delta_day(comp["active_limit_day_delta"]),
                                    },
                                    {
                                        "Modeled Output": "Total unmet modeled demand",
                                        comp["configured_label"]: f"{comp['unmet_demand_configured_acft']:,.0f} ac-ft",
                                        comp["flat_label"]: f"{comp['unmet_demand_flat_acft']:,.0f} ac-ft",
                                        "Delta": f"{comp['unmet_demand_delta_acft']:+,.0f} ac-ft" if comp["unmet_demand_delta_acft"] != 0 else "0 ac-ft",
                                    },
                                    {
                                        "Modeled Output": "Domestic and industrial curtailed",
                                        comp["configured_label"]: f"{comp['curtailed_domestic_configured_acft']:,.0f} / {comp['curtailed_industrial_configured_acft']:,.0f} ac-ft",
                                        comp["flat_label"]: f"{comp['curtailed_domestic_flat_acft']:,.0f} / {comp['curtailed_industrial_flat_acft']:,.0f} ac-ft",
                                        "Delta": f"{comp['curtailed_domestic_delta_acft']:+,.0f} / {comp['curtailed_industrial_delta_acft']:+,.0f} ac-ft",
                                    },
                                ])
                                st.dataframe(comp_table, hide_index=True, width="stretch")
                                st.caption(comp["boundary_statement"])

                        # Pipeline Outage Resilience Counterfactual
                        if not simple_view and pipeline_active and getattr(chosen_sys, "pipeline_capacity_mgd", 0) > 0 and chosen_sys.demand_no_pipeline_acft_day is not None:
                            sim_no_pipe = simulate_reservoir_drawdown(s.series, initial_pct=init_pct, conservation_pct=conserve_choice/100.0, pipeline_active=False, config=chosen_sys)
                            crit_pct = chosen_sys.stage_bands_pct[2] * 100 if len(chosen_sys.stage_bands_pct) >= 3 else 20.0
                            s_crit_with = threshold_crossing_day(sim_df, init_pct, crit_pct)
                            s_crit_without = threshold_crossing_day(sim_no_pipe, init_pct, crit_pct)
                            if s_crit_with is not None and s_crit_without is not None and s_crit_with > s_crit_without:
                                st.info(f"The configured pipeline-available demand case delays reaching the illustrative {crit_pct:.0f}% band by **{s_crit_with - s_crit_without} days** versus the pipeline-unavailable demand case.")
                            elif s_crit_without is not None and s_crit_with is None:
                                st.info(f"The pipeline-available demand case stays above the illustrative {crit_pct:.0f}% band in this window; the pipeline-unavailable case reaches it on Day {s_crit_without}.")

                        # TCEQ Emergency Inflow Status
                        if not simple_view and getattr(chosen_sys, "estuary_order_active", False) and sim_df["estuary_pass_through_acft"].sum() == 0:
                            st.caption(f"Configured estuary pass-through assumption: {chosen_sys.estuary_pass_through_fraction:.0%} of modeled inflow, capped at {chosen_sys.estuary_pass_through_cap_acft_day:g} ac-ft/day, is passed through above {chosen_sys.estuary_threshold_pct:.0%} storage; none is passed through at or below it. This is a preset input, not a live regulatory-status determination.")

                        st.info("📢 **Modeled storage result**: " + reservoir_summary(
                            sim_df, chosen_sys.name, stage_bands_pct=chosen_sys.stage_bands_pct,
                            initial_pct=init_pct))
                        st.caption(f"Results cover this {len(s.series)}-day window. Threshold timing depends on these assumptions and is not an official restriction date.")

                        if not simple_view:
                            with st.container(border=True):
                                st.markdown("##### 🏛️ Regional Context (Corpus Christi / Region N)")
                                st.markdown(
                                    """
                                    This panel supplies context for the configured experiment; it is not a live policy or operating-status feed.

                                    - The City's [April 24, 2026 water-supply memo](https://www.corpuschristitx.gov/media/btvn01mr/20260424_memo_water-supply-update.pdf) reported **7.8% combined storage on April 16, 2026**. BASIN's 7.8% line is a dated reference marker, not a forecast or physical failure threshold.
                                    - The City's [water-supply dashboard](https://www.corpuschristitx.gov/department-directory/corpus-christi-water/water-supply-dashboard/) describes Level 1 in terms of a projected 180-day supply-versus-demand condition. BASIN's 10% line is only an illustrative band.
                                    - The City reported [72–79 MGD operation](https://www.corpuschristitx.gov/news/posts/city-council-approves-critical-infrastructure-upgrades-for-mary-rhodes-pipeline/) for the Mary Rhodes Pipeline in March 2025. The experiment's pipeline toggle compares the two configured demand cases shown above; it does not reproduce pipeline hydraulics or guarantee delivery.
                                    - Sector shares and storage-dependent curtailments are configurable modeling assumptions. They do not implement a ballot measure, adopted drought plan, customer contract, or regulatory order.
                                    """
                                )

        with tab_agro:
            st.caption("Decision-support estimates for crop irrigation deficit and wildfire stress.")
            c_agro_tab, c_fire_tab = st.tabs(["🌾 Crop Water Deficit (ETc)", "🔥 Wildfire Risk (KBDI)"])
            with c_agro_tab:
                st.markdown("##### 🌾 Crop Evapotranspiration & Irrigation Deficit")
                c1, c2 = st.columns([2, 1])
                crop_choice = c1.selectbox("Crop Type", list(CROP_COEFFICIENTS.keys()), key=f"crop_sel_{s.id}_{w.id}")
                crop_def = calculate_crop_water_deficit(s.series, crop_name=crop_choice)
                c2.metric("Crop Coefficient (Kc)", f"{crop_def['kc']:.2f}")

                gap_val = f"{crop_def['irrigation_gap_in']:.2f} in" if is_us else f"{crop_def['irrigation_gap_mm']:.1f} mm"
                st.markdown(f'''<div class="basin-callout-card" style="border-left: 5px solid #087e8b;">
                    <div class="metric-label">🌾 Decision Metric · Illustrative Net Atmospheric Deficit (ETc - P)</div>
                    <div class="metric-val" style="color: var(--basin-info-text); font-size: 1.4rem; font-weight: 800;">{gap_val}</div>
                    <div class="metric-desc">Illustrative Net Atmospheric Deficit (ETc - P): Daily crop evapotranspiration demand minus rainfall, assuming fixed regional ETo and crop coefficients without field soil-moisture carryover or irrigation application efficiency.</div>
                </div>''', unsafe_allow_html=True)

                a1, a2, a3 = st.columns(3)
                if is_us:
                    a1.metric("Scenario Rainfall", f"{crop_def['total_rain_in']:.2f} in")
                    a2.metric("Reference ET (ETo)", f"{crop_def['total_eto_in']:.2f} in")
                    a3.metric("Crop ET (ETc)", f"{crop_def['total_etc_in']:.2f} in")
                else:
                    a1.metric("Scenario Rainfall", f"{crop_def['total_rain_mm']:.1f} mm")
                    a2.metric("Reference ET (ETo)", f"{crop_def['total_eto_in']*25.4:.1f} mm")
                    a3.metric("Crop ET (ETc)", f"{crop_def['total_etc_in']*25.4:.1f} mm")

                st.info("📢 **Agronomic Takeaway**: " + crop_def["takeaway"])

                with st.container(border=True):
                    st.markdown("##### 📅 Monthly Irrigation Deficit Breakdown")
                    m_df = pd.DataFrame(crop_def["monthly_summary"])
                    st.dataframe(m_df, hide_index=True, width="stretch")

            with c_fire_tab:
                st.markdown("##### 🔥 Keetch-Byram Drought Index (KBDI) & Wildfire Stress")
                if simple_view:
                    start_kbdi = int(st.session_state.get(f"kbdi_start_{s.id}_{w.id}", 400))
                    f2 = st.container()
                    st.caption("Starting KBDI: 400. Choose Advanced View to change this assumption.")
                else:
                    f1, f2 = st.columns([2, 1])
                    start_kbdi = f1.slider("Starting KBDI (soil dryness)", 0, 800, 400, 10, key=f"kbdi_start_{s.id}_{w.id}",
                                          help="0 = saturated; 800 = extreme drought. The 600 marker is illustrative, not an official declaration.")
                kbdi_res = calculate_kbdi(s.series, initial_kbdi=float(start_kbdi))
                f2.metric("Danger Class", kbdi_res.danger_class)

                if kbdi_res.burn_ban_breached:
                    st.markdown(f'''<div class="basin-callout-card alert" style="border-left: 5px solid #dc2626;">
                        <div class="metric-label">🔴 Decision Metric · Illustrative KBDI Stress Marker (≥ 600)</div>
                        <div class="metric-val" style="color: var(--basin-danger-text); font-size: 1.4rem; font-weight: 800;">Crossed on Day {kbdi_res.burn_ban_day} (Peak: {kbdi_res.peak_kbdi:.0f} on Day {kbdi_res.peak_day})</div>
                        <div class="metric-desc">Illustrative meteorological stress marker crossed; county burn bans are legal determinations issued by County Commissioners Courts based on local conditions, not an automated dashboard trigger.</div>
                    </div>''', unsafe_allow_html=True)
                else:
                    st.markdown(f'''<div class="basin-callout-card" style="border-left: 5px solid #16a34a;">
                        <div class="metric-label">🟢 Decision Metric · Illustrative KBDI Stress Marker (≥ 600)</div>
                        <div class="metric-val" style="color: var(--basin-success-text); font-size: 1.4rem; font-weight: 800;">Below 600 (Peak: {kbdi_res.peak_kbdi:.0f} on Day {kbdi_res.peak_day})</div>
                        <div class="metric-desc">Soil moisture deficit index remains below typical Texas county stress markers throughout the scenario.</div>
                    </div>''', unsafe_allow_html=True)

                k1, k2, k3 = st.columns(3)
                k1.metric("Initial KBDI", f"{kbdi_res.initial_kbdi:.0f}")
                k2.metric("Peak KBDI", f"{kbdi_res.peak_kbdi:.0f}")
                k3.metric("Final KBDI", f"{kbdi_res.final_kbdi:.0f}")

                if kbdi_res.burn_ban_breached:
                    st.warning(
                        f"⚠️ **Illustrative KBDI Stress Marker (≥600) Crossed on Day {kbdi_res.burn_ban_day}**: "
                        f"Soil moisture depletion marker crossed at Day {kbdi_res.burn_ban_day}; peak KBDI reaches {kbdi_res.peak_kbdi:.0f} on Day {kbdi_res.peak_day}. "
                        "Texas county outdoor burn bans are legal determinations made by County Commissioners Courts under Local Government Code § 352.081 based on local fire conditions, not an automated dashboard trigger. "
                        "Consult the [Texas A&M Forest Service Official Burn Ban Map](https://tfsweb.tamu.edu/wildfire-and-other-disasters/burn-bans-and-information/) for current statutory declarations."
                    )
                else:
                    st.success(f"✅ KBDI peaks at {kbdi_res.peak_kbdi:.0f} on Day {kbdi_res.peak_day}, remaining below the illustrative 600 meteorological stress marker.")

                st.info("📢 **Operational Takeaway**: " + kbdi_res.takeaway)
                st.caption("Illustrative decision support. Official burn bans are enacted by County Commissioners Courts.")

        with tab_rainfall:
            st.markdown("### Compare rainfall with its reference")
            station = st.selectbox("Station to compare", list(s.series.columns), format_func=lambda i: names[i], key=f"review_station_{w.id}")
            mode = st.radio("Rainfall view", ["Cumulative rainfall", "Daily rainfall", "30-day deficit"], horizontal=True, key="review_rainfall_view")
            expected = pd.DataFrame(w.reference.expected(s.series.index), index=s.series.index, columns=s.series.columns)
            fig = rainfall_reference_figure(s.series[station], expected[station], mode, unit=unit_arg)
            fig = chart(fig, 340)
            if mode != "30-day deficit":
                fig.data[0].line.dash = "dash"
                fig.data[1].line.dash = "solid"
            st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})
            actual_total, reference_total = s.series[station].sum(), expected[station].sum()
            difference = reference_total - actual_total
            if is_us:
                st.write(f"Over these {len(s.series)} days, **{names[station]}** receives **{actual_total/25.4:.2f} in ({actual_total:.1f} mm)** in the scenario "
                         f"versus **{reference_total/25.4:.2f} in ({reference_total:.1f} mm)** in the reference: **{abs(difference)/25.4:.2f} in ({abs(difference):.1f} mm) {'less' if difference >= 0 else 'more'} rainfall**.")
            else:
                st.write(f"Over these {len(s.series)} days, **{names[station]}** receives **{actual_total:.1f} mm ({actual_total/25.4:.2f} in)** in the scenario "
                         f"versus **{reference_total:.1f} mm ({reference_total/25.4:.2f} in)** in the reference: **{abs(difference):.1f} mm ({abs(difference)/25.4:.2f} in) {'less' if difference >= 0 else 'more'} rainfall**.")
            st.caption("Dashed line: 1991–2020 monthly reference mean.")
            if mode == "30-day deficit":
                st.caption("Positive: rainfall deficit versus the 30-day reference. Negative: surplus.")

            with st.container(border=True):
                st.markdown("##### Historical Comparison & Station Concurrence")
                st.markdown(f"**30-day windows with all selected stations stressed:** {f['concurrence']:.1%} of {f['eligible_concurrence_days']} eligible windows.")
                rc1, rc2, rc3 = st.columns(3)
                if len(w.params.stations) == 1:
                    rc1.metric("Station Stress Persistence", f"{f['concurrence']:.1%}", f"{f['eligible_concurrence_days']} eligible windows")
                else:
                    rc1.metric("Station Concurrence", f"{f['concurrence']:.1%}", f"{f['eligible_concurrence_days']} eligible windows")
                shortfall_bm = f"{f['benchmark_mm']/25.4:.2f} in" if is_us else f"{f['benchmark_mm']:.1f} mm"
                rc2.metric("Benchmark Shortfall", shortfall_bm, "Largest matched historical window")
                rc3.metric("Composite Ranking Score", f"{s.score:.2f}", "Configured Priorities")
                st.caption("Concurring stress frequency across eligible windows. Composite ranking score is based on the configured priorities.")

        with tab_edits:
            st.caption("Edits create a new scenario revision and require review again.")
            col_scale, col_csv, col_swap = st.columns(3, gap="large")
            with col_scale:
                st.markdown("##### 1. Scale Rainfall")
                factor = st.number_input("Multiplier", 0.0, 2.0, 0.8, 0.05, key=f"edit_{s.id}_{w.id}")
                if st.button("Apply multiplier", key=f"btn_apply_multiplier_{s.id}_{s.revision}", width="stretch"):
                    try:
                        w.edit(s.id, note, factor=factor)
                        save(w)
                        st.rerun()
                    except ValueError as error:
                        st.error(str(error))
            with col_csv:
                st.markdown("##### 2. Replace from CSV")
                st.download_button("CSV template", s.series.rename_axis("date").to_csv(), f"{s.id}-template.csv", "text/csv", key=f"dl_template_{s.id}_{s.revision}", width="stretch")
                upload = st.file_uploader("Daily rainfall · mm", type="csv", key=f"replacement_{w.id}_{s.id}")
                if st.button("Apply CSV", key=f"btn_apply_csv_{s.id}_{s.revision}", disabled=upload is None, width="stretch"):
                    try:
                        replacement = pd.read_csv(upload, index_col="date", parse_dates=["date"])
                        w.edit(s.id, note, replacement=replacement)
                        save(w)
                        st.rerun()
                    except (ValueError, KeyError, TypeError) as error:
                        st.error(str(error))
            with col_swap:
                st.markdown("##### 3. Shortlist Candidates")
                if s.id in w.selected:
                    alternatives = [x.id for x in w.scenarios if x.id not in w.selected and x.status != "rejected"]
                    if alternatives:
                        other = st.selectbox("Candidate", alternatives, format_func=lambda i: f"{i} · {w.get(i).score:.1f}", key=f"sel_alt_{s.id}_{w.id}")
                        if st.button("Replace entry", key=f"btn_replace_entry_{s.id}_{w.id}", width="stretch"):
                            st.session_state["last_swap"] = (s.id, other)
                            w.swap(s.id, other)
                            save(w)
                            st.session_state.inspect_id = other
                            st.rerun()
                    if "last_swap" in st.session_state:
                        last_out, last_in = st.session_state["last_swap"]
                        if last_in in w.selected:
                            if st.button(f"↩️ Undo Swap ({last_in} ➔ {last_out})", key=f"btn_undo_swap_{w.id}", width="stretch"):
                                w.swap(last_in, last_out)
                                st.session_state.inspect_id = last_out
                                del st.session_state["last_swap"]
                                save(w)
                                st.rerun()
                else:
                    old = st.selectbox("Replace shortlisted scenario", w.selected, key=f"sel_shortlist_target_{s.id}_{w.id}")
                    if st.button("Use this candidate", key=f"btn_use_candidate_{s.id}_{w.id}", disabled=s.status == "rejected", width="stretch"):
                        w.swap(old, s.id)
                        save(w)
                        st.rerun()

        with tab_provenance:
            evidence_tab, data_tab, history_tab = st.tabs(["Source evidence", "Daily values", "Revision history"])
            with data_tab:
                edited = st.data_editor(s.series.rename_axis("date"), width="stretch", height=300,
                                        key=f"daily_editor_{w.id}_{s.id}_{s.revision}",
                                        column_config={col: st.column_config.NumberColumn(names[col] + " · mm", min_value=0, format="%.3f") for col in s.series})
                c_note, c_save = st.columns([3, 1])
                daily_note = c_note.text_input("Edit rationale", value=note, key=f"daily_note_{w.id}_{s.id}_{s.revision}", placeholder="Reason for adjusting daily rainfall")
                if c_save.button("Save daily edits", key=f"btn_save_daily_edits_{s.id}_{s.revision}", width="stretch"):
                    if not daily_note.strip():
                        st.warning("Please enter a brief rationale for the edit.")
                    elif edited.to_numpy().tolist() == s.series.to_numpy().tolist():
                        st.info("No daily values were modified.")
                    else:
                        try:
                            w.edit(s.id, daily_note, replacement=edited)
                            save(w)
                            st.rerun()
                        except (ValueError, TypeError) as error:
                            st.error(str(error))
            with evidence_tab:
                is_us = st.session_state.get("unit_mode", "us") == "us"
                ev_data = {
                    "Station": list(s.provenance["retention_by_station"]),
                    "Scenario rainfall (% of observed rainfall)": [
                        f"{v*100:g}% retained ({round((1.0 - v)*100, 1):g}% reduction)"
                        for v in s.provenance["retention_by_station"].values()
                    ],
                    "Current deficit mm": [f["station_deficits_mm"][i] for i in s.provenance["retention_by_station"]],
                }
                if is_us:
                    ev_data["Current deficit in"] = [round(f["station_deficits_mm"][i] / 25.4, 2) for i in s.provenance["retention_by_station"]]
                st.dataframe(pd.DataFrame(ev_data), hide_index=True, width="stretch")
                evidence_panel(w, s, save)
                st.json({"source": s.provenance, "features": f, "score_contributions": s.components, "snapshot_sha256": source.manifest["sha256"]})
            with history_tab:
                if s.history:
                    st.dataframe(pd.DataFrame([{k:v for k,v in event.items() if k != "replacement_values"} for event in s.history]), hide_index=True, width="stretch")
                else:
                    st.caption("No revisions or review decisions")
    st.divider()
    all_reviewed = all(w.get(i).status in ("accepted", "rejected") for i in w.selected)
    has_accepted = any(w.get(i).status == "accepted" for i in w.selected)
    export_ready = all_reviewed and has_accepted and all(
        w.get(i).approved_revision == w.get(i).revision for i in w.selected if w.get(i).status == "accepted")

    if export_ready:
        nav_note = f"Step 3 Complete · {sum(w.get(i).status == 'accepted' for i in w.selected)} scenario(s) included for export"
    else:
        unreviewed_count = len(pending)
        nav_note = f"{unreviewed_count} scenario(s) need review" if unreviewed_count else "Include at least 1 scenario to export"

    render_bottom_nav(
        prev_page="Workspace",
        next_page="Exports",
        next_label="Proceed to Step 4: Export",
        next_disabled=not export_ready,
        note=nav_note
    )

elif page == "Exports":
    if w is None:
        st.info("💡 **No Active Analysis Run**: To prepare and verify an export packet, first configure and run scenarios in **Scenario Builder**.")
        st.button("➔ Go to Step 2: Scenario Builder", key="btn_exports_to_workspace_empty", on_click=switch_page, args=("Workspace",), type="primary")
    else:
        chosen = [w.get(i) for i in w.selected]
        context = w.analysis_context
        h_exp_l, h_exp_r = st.columns([3.2, 1.2])
        with h_exp_l:
            st.markdown("**Review what your recipient will receive**")
            st.caption(
                f"Prepared for {context.audience_label} ({context.county_label}). A readable rainfall brief, daily values, "
                "source evidence and a replayable audit are included. Review decisions control what can be exported."
            )
        with h_exp_r:
            if st.button("🔄 Start New Analysis", key="btn_reset_analysis_export", width="stretch", help="Reset all scenarios, reviews and session state to start fresh"):
                confirm_reset_dialog()

        # Single experiment configuration every report on this page is generated from.
        experiment_config = st.session_state.get("experiment_config")
        if not isinstance(experiment_config, ExperimentConfig):
            experiment_config = ExperimentConfig()

        col_export_ctrl, col_export_view = st.columns([1.0, 1.45], gap="large")

        with col_export_ctrl:
            st.markdown("#### 1. Export Controls & Verification")
            share = st.checkbox("Include provider notes and free-text review notes", value=False, key=f"share_notes_{w.id}")
            share_custom = False
            if w.has_custom_data:
                st.warning("This analysis contains custom evidence. Replay requires all saved normalized upload versions, station/location/source metadata and suitability rationale.")
                share_custom = st.checkbox(
                    "Include custom numerical inputs and source metadata in this replayable export",
                    key="custom_export_" + digest({"uploads": w.custom_uploads, "snapshot": w.source.manifest.get("sha256")}),
                )

            def report_token(accepted_scenarios):
                return report_state_token({"id": w.id, "content": digest(w.record(share, include_custom=True))}, accepted_scenarios, share, share_custom, experiment_config)

            # 1. READINESS GATE & PRIMARY EXPORT TRIGGER
            try:
                w.exportable()
                ready = True
                st.success("✅ **Export verified:** All shortlisted candidates are reviewed and ready for bundle generation.")
            except ValueError as error:
                ready = False
                st.warning(f"⚠️ **Export prerequisite:** {error}")
                unreviewed = [s for s in chosen if s.status == "unreviewed" or (s.status == "accepted" and s.approved_revision != s.revision)]
                if unreviewed:
                    st.info(
                        f"**{len(unreviewed)} shortlisted candidate(s) require review before export:** "
                        f"{', '.join(s.id for s in unreviewed)}.\n\n"
                        "BASIN's scientific provenance standard requires each shortlisted scenario to have a deliberate human decision (Accept or Reject) before generating a verified engineering bundle."
                    )
                    col_a, col_b = st.columns([1, 1])
                    batch_rationale = col_a.text_input(
                        "Batch review rationale",
                        value="",
                        key="input_batch_rationale",
                        help="Explain why one decision applies to this entire shortlist (minimum 20 characters). The audit identifies this as a batch decision."
                    )
                    valid_batch_rationale = len(batch_rationale.strip()) >= 20
                    if col_a.button("✅ Accept all shortlisted with batch decision", key="btn_accept_all_for_export", type="primary", disabled=not valid_batch_rationale):
                        note = f"included by batch decision: {batch_rationale.strip()}"
                        for s in unreviewed:
                            s.review(True, note, decision_mode="batch")
                        save(w)
                        st.success("All shortlisted candidates included by batch decision.")
                        st.rerun()
                    if col_b.button("🔍 Review candidates in Review tab", key="btn_goto_review_tab"):
                        switch_page("Review")
                        st.rerun()

            with tour_target("export_panel"):
                if not ready:
                    st.warning("⚠️ **Export locked:** Review decisions required before generating verified bundle. Use '✅ Accept all shortlisted with batch decision' above or review each scenario individually.")
                elif w.has_custom_data and not share_custom:
                    st.warning("⚠️ **Custom Evidence Consent Required:** Check 'Include custom numerical inputs and source metadata' above to enable verified export.")
                if st.button("Build verified export", key="btn_build_verified_export", type="primary", disabled=not ready or (w.has_custom_data and not share_custom)):
                    try:
                        payload = export_bundle(w, share, include_custom=share_custom)
                        report = verify_bundle(payload)
                        out_dir = ROOT / "output"
                        out_dir.mkdir(parents=True, exist_ok=True)
                        zip_path = out_dir / f"BASIN-{w.id}.zip"
                        zip_path.write_bytes(payload)
                        brief_text = generate_brief(w, w.exportable())
                        brief_path = out_dir / f"Hydrologist_Handoff_Brief_{w.id}.md"
                        brief_path.write_text(brief_text, encoding="utf-8")
                        render_outcome = generate_pdf_report_with_status(w, w.exportable(), include_notes=share, config=experiment_config)
                        pdf_bytes = render_outcome.pdf_bytes
                        pdf_path = out_dir / f"BASIN-Executive-Brief-{w.id}.pdf"
                        pdf_path.write_bytes(pdf_bytes)

                        # Build Excel deliverable (.xlsx)
                        import io
                        excel_buffer = io.BytesIO()
                        with pd.ExcelWriter(excel_buffer, engine="openpyxl") as writer:
                            shortlist_df = pd.DataFrame([summary_record(sc) for sc in w.exportable()])
                            shortlist_df.to_excel(writer, sheet_name="Shortlist_Summary", index=False)
                            rainfall_df = pd.concat([rainfall_rows(sc) for sc in w.exportable()])
                            rainfall_df.to_excel(writer, sheet_name="Daily_Rainfall", index=False)
                            pd.DataFrame([
                                {"Property": "Run ID", "Value": w.id},
                                {"Property": "Created At", "Value": w.created_at},
                                {"Property": "Snapshot SHA-256", "Value": w.source.manifest.get("sha256", "")},
                            ]).to_excel(writer, sheet_name="Run_Metadata", index=False)
                        xlsx_bytes = excel_buffer.getvalue()
                        xlsx_path = out_dir / f"BASIN-Shortlist-{w.id}.xlsx"
                        xlsx_path.write_bytes(xlsx_bytes)

                        st.session_state.packet = {
                            "data": payload,
                            "pdf_bytes": pdf_bytes,
                            "pdf_renderer": render_outcome.renderer,
                            "pdf_degraded": render_outcome.degraded,
                            "pdf_render_detail": render_outcome.detail,
                            "brief_text": brief_text,
                            "xlsx_bytes": xlsx_bytes,
                            "saved_pdf": str(pdf_path.name),
                            "saved_zip": str(zip_path.name),
                            "saved_brief": str(brief_path.name),
                            "saved_xlsx": str(xlsx_path.name),
                            "fingerprint": json.dumps(w.record(share, include_custom=share_custom), sort_keys=True),
                            "share": share,
                            "custom": share_custom,
                            "config": experiment_config.fingerprint(),
                            "token": report_token(w.exportable()),
                            "report": report
                        }
                        meta_path = out_dir / f"BASIN-Meta-{w.id}.json"
                        meta_path.write_text(json.dumps({
                            "fingerprint": json.dumps(w.record(share, include_custom=share_custom), sort_keys=True),
                            "share": share,
                            "custom": share_custom,
                            "config": experiment_config.fingerprint(),
                            "run_id": w.id,
                            "created_at": w.created_at,
                        }, indent=2), encoding="utf-8")
                        st.success(f"✅ Verified deliverables generated and saved to disk: `output/{pdf_path.name}`, `output/{zip_path.name}`, and `output/{xlsx_path.name}`")
                    except (ValueError, AssertionError, OSError) as error:
                        st.error(f"Verification failed: {error}")

            # 2. GENERATED DELIVERABLES STAGE (MAIN PDF, EXCEL & ZIP DOWNLOAD CARDS)
            packet = st.session_state.get("packet")
            try:
                current_fingerprint = json.dumps(w.record(share, include_custom=share_custom), sort_keys=True)
            except ValueError:
                current_fingerprint = None

            packet_fresh = bool(
                packet
                and (not w.has_custom_data or share_custom)
                and packet.get("custom", False) == share_custom
                and packet.get("share") == share
                and packet.get("config") == experiment_config.fingerprint()
                and current_fingerprint is not None
                and packet.get("fingerprint") == current_fingerprint
            )
            if packet and not packet_fresh:
                st.session_state.pop("packet", None)
                packet = None
                st.info("Inputs, experiment settings or consent changed since the last export. Rebuild the verified export to download it again.")

            disk_zip = ROOT / "output" / f"BASIN-{w.id}.zip"
            disk_pdf = ROOT / "output" / f"BASIN-Executive-Brief-{w.id}.pdf"
            disk_xlsx = ROOT / "output" / f"BASIN-Shortlist-{w.id}.xlsx"
            disk_meta = ROOT / "output" / f"BASIN-Meta-{w.id}.json"

            disk_fresh = False
            if disk_meta.exists():
                try:
                    dm = json.loads(disk_meta.read_text(encoding="utf-8"))
                    disk_fresh = (
                        dm.get("fingerprint") == current_fingerprint
                        and dm.get("share") == share
                        and dm.get("custom") == share_custom
                        and dm.get("config") == experiment_config.fingerprint()
                    )
                except Exception:
                    disk_fresh = False

            if not packet_fresh and disk_zip.exists() and disk_pdf.exists():
                if disk_fresh:
                    st.info(f"📦 **Existing Verified Deliverables on Disk** for run `{w.id}`. (Matches current settings and consent).")
                    c_d1, c_d2, c_d3, c_d4 = st.columns([1, 1, 1, 1])
                    c_d1.download_button("Download Saved PDF", disk_pdf.read_bytes(), disk_pdf.name, "application/pdf", key=f"dl_disk_pdf_{w.id}", width="stretch")
                    c_d2.download_button("Download Saved ZIP", disk_zip.read_bytes(), disk_zip.name, "application/zip", key=f"dl_disk_zip_{w.id}", width="stretch")
                    if disk_xlsx.exists():
                        c_d3.download_button("Download Saved Excel", disk_xlsx.read_bytes(), disk_xlsx.name, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", key=f"dl_disk_xlsx_{w.id}", width="stretch")
                    if c_d4.button("Open Output Folder", key=f"btn_open_disk_out_{w.id}", width="stretch"):
                        import subprocess, sys
                        out_folder = ROOT / "output"
                        if sys.platform == "win32":
                            subprocess.Popen(["explorer", str(out_folder.resolve())])
                        elif sys.platform == "darwin":
                            subprocess.Popen(["open", str(out_folder.resolve())])
                        else:
                            subprocess.Popen(["xdg-open", str(out_folder.resolve())])
                else:
                    st.warning(
                        f"⚠️ **Previous Local Draft Found on Disk** (`output/BASIN-{w.id}.*`). "
                        "Settings, review decisions, or privacy consent have changed since this artifact was created. "
                        "Rebuild the verified export above to update the packet."
                    )
                    if st.button("📁 Open Output Folder (Inspect Historical Drafts)", key=f"btn_open_disk_out_{w.id}"):
                        import subprocess, sys
                        out_folder = ROOT / "output"
                        if sys.platform == "win32":
                            subprocess.Popen(["explorer", str(out_folder.resolve())])
                        elif sys.platform == "darwin":
                            subprocess.Popen(["open", str(out_folder.resolve())])
                        else:
                            subprocess.Popen(["xdg-open", str(out_folder.resolve())])

            if packet_fresh:
                st.success(
                    "✅ **Verified Export Package Ready** — SHA-256 integrity verified for the replay ZIP bundle. "
                    "The companion Executive Brief (PDF) and Shortlist Workbook (Excel) provide decision-ready deliverables for water board and council presentation."
                )

                pdf_data = packet.get("pdf_bytes")
                if pdf_data:
                    st.download_button(
                        "Download Executive Brief (PDF)",
                        pdf_data,
                        f"BASIN-Executive-Brief-{w.id}.pdf",
                        "application/pdf",
                        key=f"dl_pdf_main_{w.id}",
                        type="primary",
                        width="stretch"
                    )
                    if packet.get("pdf_degraded"):
                        st.warning(f"⚠️ **PDF renderer fallback:** {packet.get('pdf_render_detail', '')}")
                    else:
                        st.caption(f"PDF renderer: {packet.get('pdf_render_detail', 'unknown')}")

                st.markdown("**Companion Deliverables & Replay Package:**")
                col_dl1, col_dl2 = st.columns(2)
                with col_dl1:
                    st.download_button("Download Replay ZIP", packet["data"], f"BASIN-{w.id}.zip", "application/zip", key=f"dl_zip_{w.id}", width="stretch")
                with col_dl2:
                    brief_bytes = packet.get("brief_text", "").encode("utf-8") if packet.get("brief_text") else b""
                    st.download_button("Download Brief (.md)", brief_bytes, f"Hydrologist_Handoff_Brief_{w.id}.md", "text/markdown", key=f"dl_brief_export_{w.id}", width="stretch")
                col_dl3, col_dl4 = st.columns(2)
                with col_dl3:
                    xlsx_data = packet.get("xlsx_bytes")
                    if xlsx_data:
                        st.download_button("Download Shortlist (.xlsx)", xlsx_data, f"BASIN-Shortlist-{w.id}.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", key=f"dl_xlsx_{w.id}", width="stretch")
                with col_dl4:
                    if st.button("Open Output Folder", key=f"btn_open_out_folder_{w.id}", width="stretch"):
                        import subprocess, sys
                        out_folder = ROOT / "output"
                        if sys.platform == "win32":
                            subprocess.Popen(["explorer", str(out_folder.resolve())])
                        elif sys.platform == "darwin":
                            subprocess.Popen(["open", str(out_folder.resolve())])
                        else:
                            subprocess.Popen(["xdg-open", str(out_folder.resolve())])
                st.caption(f"📁 Local copies on disk: `output/{packet.get('saved_pdf', f'BASIN-Executive-Brief-{w.id}.pdf')}`, `output/{packet.get('saved_zip', f'BASIN-{w.id}.zip')}` and `output/{packet.get('saved_brief', f'Hydrologist_Handoff_Brief_{w.id}.md')}`")
                st.json(packet["report"])
                st.caption(f"{packet['report']['scenarios_replayed']} revisions verified · daily_rainfall.csv / shortlist.csv / audit.json / input snapshot / checksums")

            st.markdown("#### Experiment Configuration")
            if not experiment_config.selected:
                st.info("No experiment has been configured in Review. Reports use BASIN's documented defaults, shown below. These are not a record of an earlier run.")
            else:
                st.caption("Selected in Review. Every simulated figure in the preview and the exported PDF uses exactly these settings.")
            st.dataframe(
                pd.DataFrame(experiment_config.describe_rows(), columns=["Setting", "Value"]),
                hide_index=True,
                width="stretch",
            )

        with col_export_view:
            st.markdown("#### 2. Deliverable Workspace & Documentation")
            accepted_preview = [s for s in chosen if s.status == "accepted" and s.approved_revision == s.revision]
            if not accepted_preview:
                st.session_state.pop("preview_pdf", None)

            tab_rep_prev, tab_shortlist, tab_evidence, tab_footprint = st.tabs([
                "📄 Executive Report Preview",
                "📊 Shortlist Details",
                "📁 Evidence & Provenance",
                "🌱 Environmental Footprint"
            ])

            with tab_rep_prev:
                if accepted_preview:
                    st.caption("Draft preview of currently accepted revisions. Building the packet still requires every shortlisted revision to be reviewed.")
                    brief_preview_text = generate_brief(w, accepted_preview)
                    col_prev_a, col_prev_b, col_prev_c = st.columns([1.5, 1, 1])
                    with col_prev_b:
                        preview_token = report_token(accepted_preview)
                        preview_state = st.session_state.get("preview_pdf")
                        if preview_state and preview_state.get("token") != preview_token:
                            st.session_state.pop("preview_pdf", None)
                            preview_state = None
                        if preview_state is None:
                            if st.button("📕 Prep PDF Preview", key=f"btn_prep_pdf_prev_{w.id}", width="stretch"):
                                preview_outcome = generate_pdf_report_with_status(w, accepted_preview, include_notes=share, config=experiment_config)
                                st.session_state["preview_pdf"] = {
                                    "token": preview_token,
                                    "bytes": preview_outcome.pdf_bytes,
                                    "degraded": preview_outcome.degraded,
                                    "detail": preview_outcome.detail,
                                }
                                st.rerun()
                        else:
                            st.download_button(
                                "📕 Download PDF Preview",
                                preview_state["bytes"],
                                f"BASIN-Executive-Brief-Preview-{w.id}.pdf",
                                "application/pdf",
                                key=f"dl_pdf_preview_{w.id}",
                                width="stretch"
                            )
                            if preview_state.get("degraded"):
                                st.warning(f"⚠️ {preview_state.get('detail', '')}")
                            else:
                                st.caption(f"PDF renderer: {preview_state.get('detail', 'unknown')}")
                    with col_prev_c:
                        st.download_button(
                            "📄 Download Brief (.md)",
                            brief_preview_text.encode("utf-8"),
                            f"Hydrologist_Handoff_Brief_{w.id}.md",
                            "text/markdown",
                            key=f"dl_brief_preview_{w.id}",
                            width="stretch",
                        )
                    prev_sub1, prev_sub2, prev_sub3 = st.tabs([
                        "📈 Visual Report Figures",
                        "📄 Executive Briefing (.md)",
                        "🌐 Full HTML Report Preview",
                    ])
                    with prev_sub1:
                        try:
                            lead_sc = accepted_preview[0]
                            sys_cfg = experiment_config.system_config or REGION_N_PRESET
                            bands = tuple(sys_cfg.stage_bands_pct) if hasattr(sys_cfg, "stage_bands_pct") else (0.40, 0.30, 0.20, 0.15)
                            sim_lead = simulate_reservoir_drawdown(
                                lead_sc.series,
                                initial_pct=experiment_config.initial_pct,
                                conservation_pct=0.0,
                                pipeline_active=experiment_config.pipeline_active,
                                pipeline_reliability_pct=experiment_config.pipeline_reliability_pct,
                                stepped_policy=experiment_config.stepped_policy,
                                config=sys_cfg,
                            )
                            spec_lead = simulate_stress_spectrum(
                                lead_sc.series,
                                tiers=experiment_config.tiers,
                                initial_pct=experiment_config.initial_pct,
                                conservation_pct=experiment_config.conservation_pct,
                                pipeline_active=experiment_config.pipeline_active,
                                pipeline_reliability_pct=experiment_config.pipeline_reliability_pct,
                                stepped_policy=experiment_config.stepped_policy,
                                config=sys_cfg,
                            )
                            bands_pct = tuple(b * 100.0 if b <= 1.0 else b for b in bands)

                            st.markdown("**Figure 1: Projected Reservoir Storage Trajectory & Threshold Crossings (Uncalibrated Toy Planning Model — No Regulatory Restriction Date)**")
                            st.plotly_chart(storage_trajectory_figure(sim_lead, bands), width="stretch", config={"displayModeBar": False})

                            st.markdown("**Figure 2: Milestone Gantt Timeline — Response Band Crossings Across Retention Tiers**")
                            st.plotly_chart(stage_trigger_milestone_figure(spec_lead, bands_pct), width="stretch", config={"displayModeBar": False})

                            st.markdown("**Figure 3: Candidate Deficit & Shortlist Distribution Across Durations (Pareto Frontier)**")
                            st.plotly_chart(pareto_frontier_figure(table(w), list(w.selected)), width="stretch", config={"displayModeBar": False})
                        except Exception as err:
                            st.info(f"Visual charts preview unavailable: {err}")

                    with prev_sub2:
                        with st.container(height=520):
                            st.markdown(brief_preview_text)

                    with prev_sub3:
                        if st.button("🌐 Compile & View Full HTML Report", key=f"btn_render_html_prev_{w.id}"):
                            st.session_state[f"show_html_prev_{w.id}"] = True
                        if st.session_state.get(f"show_html_prev_{w.id}"):
                            try:
                                html_report = render_html_report(w, accepted_preview, include_notes=share, config=experiment_config)
                                import streamlit.components.v1 as components
                                components.html(html_report, height=620, scrolling=True)
                            except Exception as err:
                                st.info(f"HTML report preview unavailable: {err}")
                        else:
                            st.caption("Click above to compile and inspect the complete standalone executive brief with all tables and disclosures.")
                else:
                    st.info("No accepted scenarios yet. In Review, inspect a scenario and choose Accept to see its report preview here.")
                    st.button("Go to Review", on_click=switch_page, args=("Review",))

            with tab_shortlist:
                st.markdown("**Shortlist Candidate Summary**")
                selected_table = table(w)
                selected_table = selected_table[selected_table["Selected for review"]].drop(columns="Selected for review")
                st.dataframe(selected_table, hide_index=True, width="stretch", height=450)

            with tab_evidence:
                st.markdown("**Evidence Included in Packet**")
                unresolved = [c for c in w.conflicts if c["status"] == "unresolved"]
                if unresolved:
                    st.warning(f"{len(unresolved)} unresolved evidence disagreement(s) will be included for the recipient.")
                    st.dataframe(pd.DataFrame(unresolved).drop(columns="private_note", errors="ignore"), hide_index=True)
                st.dataframe(pd.DataFrame(w.evidence).drop(columns="private_note", errors="ignore"), hide_index=True, width="stretch", height=400)

            with tab_footprint:
                fp = w.footprint
                st.markdown("**Local On-Device Resource Accounting**")
                c_fp1, c_fp2, c_fp3, c_fp4 = st.columns(4)
                c_fp1.metric("Pipeline Elapsed", f"{fp['wall_seconds']:.2f} s")
                c_fp2.metric("CPU Execution", f"{fp['cpu_seconds']:.2f} s")
                c_fp3.metric("Resident Memory", f"{fp['process_rss_mib_at_end']:.1f} MiB")
                er = fp.get("energy_wh_range", [0, 0])
                c_fp4.metric("Est. Pipeline Energy", f"{er[0]:.4f}–{er[1]:.4f} Wh")

                ai_sec = float(st.session_state.get("assistant_inference_seconds", 0.0))
                ai_wh_min = (ai_sec * 15.0) / 3600.0
                ai_wh_max = (ai_sec * 35.0) / 3600.0

                st.markdown("**AI & Assistant Subsystem Energy**")
                a_col1, a_col2, a_col3 = st.columns(3)
                a_col1.metric("Assistant Compute Time", f"{ai_sec:.2f} s")
                a_col2.metric("Active AI Power", "15–35 W" if ai_sec > 0 else "0 W (Direct Tools)")
                a_col3.metric("Est. AI Energy", f"{ai_wh_min:.4f}–{ai_wh_max:.4f} Wh" if ai_sec > 0 else "0.0000 Wh")

                st.caption(
                    "Runs 100% on-device with zero cloud inference calls and zero network transmission during analysis. "
                    "Pipeline energy is an illustrative laptop estimate (15–65 W × elapsed seconds); assistant energy accounts for active on-device CPU/GPU inference. "
                    "Full lifecycle water and embodied hardware carbon costs are unquantified."
                )
                st.json(w.footprint)

        render_bottom_nav(
            prev_page="Review",
            next_page=None,
            next_label=""
        )

st.caption("Rainfall evidence workbench · 100% on-device execution (0 cloud calls) · Core calculation engine: <150 MiB RAM · Optional local Qwen LLM requires 2.5 GB RAM")

with st.container(key="basin_assistant_slot"):
    assistant_panel(w, source=source, names=names)

with st.container(key="basin_notes_slot"):
    personal_notes_panel(w)
