"""Comprehensive end-to-end testing script for Mateo Garza farm workflow in BASIN.
"""
import sys
from pathlib import Path
import datetime
import io
import json
import zipfile

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import numpy as np
import pandas as pd
from streamlit.testing.v1 import AppTest

from basin_core.data import CachedSource
from basin_core.engine import ScenarioParams
from basin_core.workspace import Workspace
from basin_core.uploads import preview_rainfall
from basin_core.rainfall_comparison import compare_rainfall
from basin_core.agronomics import calculate_crop_water_deficit, calculate_kbdi, CROP_COEFFICIENTS
from basin_core.analysis import simulate_reservoir_drawdown, threshold_crossing_day, REGION_N_PRESET
from basin_core.summary import scenario_summary
from basin_core.exporter import export_bundle, verify_bundle
from basin_core.pdf_report import generate_pdf_report_with_status, ExperimentConfig
from basin_core.assistant import semantic_query_route

print("=" * 80)
print("MATEO GARZA - FARM-GATE END-TO-END BASIN PLATFORM AUDIT")
print("San Patricio / Nueces County, TX · Lower Nueces River Basin")
print("=" * 80)

# ---------------------------------------------------------------------------
# STEP 1: ON-FARM DATA INGESTION & COMPARISON
# ---------------------------------------------------------------------------
print("\n>>> STEP 1: Ingesting & Validating On-Farm Rainfall Data...")
csv_path = ROOT / "data" / "garza_farm_rainfall.csv"
if not csv_path.exists():
    raise FileNotFoundError(f"Missing {csv_path}")

raw_bytes = csv_path.read_bytes()
preview = preview_rainfall(raw_bytes, "Garza Farm Rain Gauge", "San Patricio County, TX", "inches")

print(f"File: {csv_path.name}")
print(f"Original SHA-256: {preview.original_sha256}")
print(f"Expected Days: {preview.expected_days} (2021-01-01 to 2024-12-31)")
print(f"Valid Days: {preview.valid_days}")
print(f"Missing Days: {preview.missing_days}")
print(f"Completeness: {preview.valid_days / preview.expected_days * 100:.2f}%")

df_farm = pd.read_csv(csv_path)
df_farm["date"] = pd.to_datetime(df_farm["date"])
df_farm["year"] = df_farm["date"].dt.year
annual_totals = df_farm.groupby("year")["precipitation"].sum()
print("\nAnnual Rainfall at Garza Farm (inches):")
for y, tot in annual_totals.items():
    print(f"  - {y}: {tot:.2f} in ({tot * 25.4:.1f} mm)")

# Compare with regional NOAA station: Corpus Christi Airport (USW00012924)
source = CachedSource()
cc_series = source.select(["USW00012924"])["USW00012924"]
cc_ref = {d.date(): None if pd.isna(v) else float(v) for d, v in cc_series.items()}

comp_result = compare_rainfall(preview, cc_ref, relationship="regional_proxy", daily_basis_confirmed=True)
print("\nNOAA Comparison (Garza Farm vs. Corpus Christi Airport USW00012924):")
print(f"  - Paired Valid Days: {comp_result.paired_days} / {len(comp_result.rows)}")
print(f"  - Farm Total (paired): {comp_result.upload_total_mm:.1f} mm ({comp_result.upload_total_mm / 25.4:.2f} in)")
print(f"  - NOAA Corpus Christi Total (paired): {comp_result.reference_total_mm:.1f} mm ({comp_result.reference_total_mm / 25.4:.2f} in)")
print(f"  - Difference (Farm - NOAA): {comp_result.difference_mm:+.1f} mm ({comp_result.difference_mm / 25.4:+.2f} in)")
print(f"  - Relative Difference: {comp_result.relative_difference_pct:+.2f}%")

# ---------------------------------------------------------------------------
# STEP 2: AGRICULTURAL PRIORITIZATION & SCENARIO SHORTLISTING
# ---------------------------------------------------------------------------
print("\n>>> STEP 2: Prioritizing Drought Criteria with Agricultural Weights...")
names = {s["id"]: s["name"].title().replace(" Intl Ap", "").replace(" Rgnl Ap", "") for s in source.manifest["stations"]}

# Generate multi-station scenarios covering Coastal Bend and upstream Nueces catchment
params = ScenarioParams(tuple(names.keys()), (90, 180, 270), (1, 4, 7, 10), 0.35, 0.85, "All stations", 300, 22)
workspace = Workspace(source, params, 6)

# Agricultural weights:
# Deficit severity (40): peak flowering/grain-fill moisture deficit
# Duration (30): prolonged multi-month drought
# Concurrence (25): upstream Nueces River tributaries starved of rainfall
# Summer timing (15): peak heat/evaporation window
ag_weights = {"severity": 40, "duration": 30, "concurrence": 25, "season": 15}
workspace.rerank(ag_weights)
workspace.rebuild_shortlist()

print(f"Generated {len(workspace.scenarios)} candidate scenarios. Agricultural Shortlist ({len(workspace.selected)} candidates):")
shortlisted = [workspace.get(sid) for sid in workspace.selected]
for rank, s in enumerate(shortlisted, start=1):
    f = s.features
    print(f"  #{rank}: {s.id} | Score: {s.score:.3f} | Duration: {f['duration_days']}d | Deficit: {f['deficit_mm']/25.4:.2f} in ({f['deficit_mm']:.1f} mm) | Percentile: {f['historical_percentile']*100:.0f}% | Concurrence: {f['concurrence']*100:.0f}% | Source: {s.provenance['source_start']} to {s.provenance['source_end']}")

# Attach custom farm gauge as supporting evidence
workspace.save_custom_upload(
    raw_bytes,
    reviewed=True,
    station="Garza Farm Rain Gauge",
    location="San Patricio County, TX (28.0° N, -97.6° W)",
    unit="inches",
    provider="Mateo Garza / Farm Electronic Gauge (Davis Vantage Pro2)",
    observation_basis="Midnight-to-midnight local central standard time; continuous tipping bucket (0.01 in resolution)",
    reference_station="USW00012924",
    relationship="regional_proxy",
    daily_confirmed=True,
    rationale="On-farm rainfall gauge representing San Patricio / Nueces County crop fields to evaluate local precipitation deficit vs regional reservoir catchment.",
    scenario_ids=workspace.selected,
)

# ---------------------------------------------------------------------------
# STEP 3: SCENARIO REVIEW & OPERATIONAL INTERPRETATION
# ---------------------------------------------------------------------------
print("\n>>> STEP 3: Inspecting Top Shortlisted Scenario & Reviewing Notes...")
top_s = shortlisted[0]
top_f = top_s.features
print(f"Top Candidate: {top_s.id}")
print(f"- Window: {top_s.provenance['source_start']} to {top_s.provenance['source_end']} ({top_f['duration_days']} days)")
print(f"- Mean Rainfall Shortfall: {top_f['deficit_mm']/25.4:.2f} in ({top_f['deficit_mm']:.1f} mm)")
print(f"- Historical Percentile: ≥ {top_f['historical_percentile']*100:.0f}% of benchmark windows")
print(f"- Station Concurrence: {top_f['concurrence']*100:.0f}%")
print(f"- Longest Consecutive Dry Run: {top_f.get('max_dry_days', 'N/A')} days (< 1 mm/day)")

summary_narrative = scenario_summary(top_f, names, unit_system="us")
print("\nAutomated Rainfall Screening Narrative:")
print(summary_narrative)

# Approve all shortlisted scenarios with authentic farmer/operator review notes
farmer_review_note = (
    "Mateo Garza review: 180-day severe deficit sequence aligns with San Patricio grain sorghum boot-to-fill stage "
    "and upland cotton peak boll development. High station concurrence confirms upstream Nueces tributaries "
    "(San Antonio, Frio, Atascosa) were simultaneously starved of runoff into Choke Canyon. Approved for regional resilience analysis."
)

for s in shortlisted:
    s.review(True, farmer_review_note)

accepted_scenarios = workspace.exportable()
print(f"\nAll {len(workspace.selected)} shortlisted scenarios reviewed and accepted. Ready for export: {bool(accepted_scenarios)} ({len(accepted_scenarios)} scenarios)")

# ---------------------------------------------------------------------------
# STEP 4: RESERVOIR STORAGE STRESS SIMULATION & DELIVERABLES
# ---------------------------------------------------------------------------
print("\n>>> STEP 4: Running Reservoir Storage Stress Simulation (38% Initial Storage)...")
# System configuration
sys_cfg = REGION_N_PRESET
total_cap = sys_cfg.total_capacity_acft  # 919,900 ac-ft
initial_pct = 0.38
initial_acft = total_cap * initial_pct  # 349,562 ac-ft

stage2_pct = 0.30
stage2_acft = total_cap * stage2_pct    # 275,970 ac-ft

stage3_pct = 0.20
stage3_acft = total_cap * stage3_pct    # 183,980 ac-ft

print(f"Water System: {sys_cfg.name} (Combined Choke Canyon + Lake Corpus Christi)")
print(f"Total Capacity: {total_cap:,.0f} ac-ft")
print(f"Initial Starting Storage: {initial_pct*100:.1f}% ({initial_acft:,.0f} ac-ft)")
print(f"Stage 2 Mandatory Curtailment Threshold: {stage2_pct*100:.1f}% ({stage2_acft:,.0f} ac-ft)")
print(f"Stage 3 Critical Reserve Threshold: {stage3_pct*100:.1f}% ({stage3_acft:,.0f} ac-ft)")

# Simulation A: 0% Curtailment (Baseline Demand)
sim_0 = simulate_reservoir_drawdown(
    top_s.series,
    initial_pct=initial_pct,
    conservation_pct=0.0,
    pipeline_active=True,
    config=sys_cfg,
)

# Simulation B: 15% Curtailment (Mandatory Drought Curtailment)
sim_15 = simulate_reservoir_drawdown(
    top_s.series,
    initial_pct=initial_pct,
    conservation_pct=0.15,
    pipeline_active=True,
    config=sys_cfg,
)

# Crossings
cross_s2_0 = threshold_crossing_day(sim_0, initial_pct, stage2_pct * 100)
cross_s3_0 = threshold_crossing_day(sim_0, initial_pct, stage3_pct * 100)

cross_s2_15 = threshold_crossing_day(sim_15, initial_pct, stage2_pct * 100)
cross_s3_15 = threshold_crossing_day(sim_15, initial_pct, stage3_pct * 100)

min_0_pct = sim_0["combined_pct"].min()
min_0_acft = sim_0["combined_acft"].min()
final_0_pct = sim_0["combined_pct"].iloc[-1]
final_0_acft = sim_0["combined_acft"].iloc[-1]

min_15_pct = sim_15["combined_pct"].min()
min_15_acft = sim_15["combined_acft"].min()
final_15_pct = sim_15["combined_pct"].iloc[-1]
final_15_acft = sim_15["combined_acft"].iloc[-1]

print("\n--- Simulation Results Comparison ---")
print(f"0% Curtailment (Business-as-usual demand):")
print(f"  - Days to Stage 2 (30%): Day {cross_s2_0} ({'Breached' if cross_s2_0 else 'Not breached'})")
print(f"  - Days to Stage 3 (20%): Day {cross_s3_0} ({'Breached' if cross_s3_0 else 'Not breached'})")
print(f"  - Minimum Storage Reached: {min_0_pct:.1f}% ({min_0_acft:,.0f} ac-ft)")
print(f"  - Final Ending Storage: {final_0_pct:.1f}% ({final_0_acft:,.0f} ac-ft)")

print(f"\n15% Curtailment (Mandatory Conservation):")
print(f"  - Days to Stage 2 (30%): Day {cross_s2_15} ({'Breached' if cross_s2_15 else 'Not breached'})")
print(f"  - Days to Stage 3 (20%): Day {cross_s3_15} ({'Breached' if cross_s3_15 else 'Not breached'})")
print(f"  - Minimum Storage Reached: {min_15_pct:.1f}% ({min_15_acft:,.0f} ac-ft)")
print(f"  - Final Ending Storage: {final_15_pct:.1f}% ({final_15_acft:,.0f} ac-ft)")

if cross_s2_0 and cross_s2_15:
    days_gained_s2 = cross_s2_15 - cross_s2_0
    print(f"\nTimeline Extension to Stage 2: +{days_gained_s2} days gained from 15% curtailment")
elif cross_s2_0 and not cross_s2_15:
    print(f"\nStage 2 completely averted over the {top_f['duration_days']}-day scenario window!")

if cross_s3_0 and cross_s3_15:
    days_gained_s3 = cross_s3_15 - cross_s3_0
    print(f"Timeline Extension to Stage 3: +{days_gained_s3} days gained from 15% curtailment")
elif cross_s3_0 and not cross_s3_15:
    print(f"Stage 3 Critical Reserve completely avoided under 15% curtailment!")

# Export deliverables
out_dir = ROOT / "output"
out_dir.mkdir(parents=True, exist_ok=True)

# 1. Verified Export Packet (.zip)
print("\nGenerating Verified Data Bundle (.zip)...")
workspace.notes = "Mateo Garza farm & rural water audit - Lower Nueces Basin resilience analysis."
zip_bytes = export_bundle(workspace, include_custom=True)
zip_path = out_dir / "garza_farm_drought_resilience_bundle.zip"
zip_path.write_bytes(zip_bytes)
print(f"Saved ZIP bundle: {zip_path} ({len(zip_bytes) / 1024:.1f} KB)")

# Verify bundle
verify_res = verify_bundle(zip_bytes)
print(f"Verification Status: {'PASSED (Verified)' if verify_res['verified'] else 'FAILED'}")
print(f"- Bundle Schema: {verify_res.get('schema_version', 'N/A')}")
print(f"- Custom Comparisons Replayed: {verify_res.get('custom_comparisons_replayed', 0)}")

# 2. Executive Technical Brief PDF
print("\nGenerating Executive Technical Brief (PDF)...")
exp_cfg = ExperimentConfig(
    initial_pct=0.38,
    conservation_pct=0.15,
    pipeline_active=True,
    scenario_id=top_s.id,
    selected=True,
    system_config=sys_cfg,
)
pdf_outcome = generate_pdf_report_with_status(
    workspace,
    accepted=shortlisted,
    output_path=out_dir / "garza_farm_executive_brief.pdf",
    include_notes=True,
    config=exp_cfg,
)
print(f"Saved Executive Brief PDF: {out_dir / 'garza_farm_executive_brief.pdf'} ({len(pdf_outcome.pdf_bytes) / 1024:.1f} KB)")
print(f"Renderer used: {pdf_outcome.renderer} (degraded={pdf_outcome.degraded})")

# ---------------------------------------------------------------------------
# STEP 5: AI ASSISTANT & AGRONOMIC WATER DEFICIT EVALUATION
# ---------------------------------------------------------------------------
print("\n>>> STEP 5: AI Assistant Evaluation & Agronomic Calculations...")

# 1. Agronomic Calculations
cotton_res = calculate_crop_water_deficit(top_s.series, crop_name="Cotton (mid-season peak)")
sorghum_res = calculate_crop_water_deficit(top_s.series, crop_name="Grain Sorghum (flowering)")

print(f"\nCrop Evapotranspiration & Irrigation Deficit (Scenario {top_s.id}, {top_f['duration_days']} days):")
print(f"--- Upland Cotton (Kc = {cotton_res['kc']:.2f}) ---")
print(f"  - Total Scenario Rain: {cotton_res['total_rain_in']:.2f} in ({cotton_res['total_rain_mm']:.1f} mm)")
print(f"  - Crop ET Demand (ETc): {cotton_res['total_etc_in']:.2f} in")
print(f"  - Net Irrigation Deficit: {cotton_res['irrigation_gap_in']:.2f} acre-inches per acre")
print(f"  - Assessment: {cotton_res['takeaway']}")

print(f"\n--- Grain Sorghum (Kc = {sorghum_res['kc']:.2f}) ---")
print(f"  - Total Scenario Rain: {sorghum_res['total_rain_in']:.2f} in ({sorghum_res['total_rain_mm']:.1f} mm)")
print(f"  - Crop ET Demand (ETc): {sorghum_res['total_etc_in']:.2f} in")
print(f"  - Net Irrigation Deficit: {sorghum_res['irrigation_gap_in']:.2f} acre-inches per acre")
print(f"  - Assessment: {sorghum_res['takeaway']}")

# 2. Targeted Assistant Queries
queries = [
    ("Crop Deficit / Irrigation Gap", "What is the crop water deficit and irrigation demand for our crops?"),
    ("35% Combined Storage Trigger", "What happens at 35% combined storage in Choke Canyon and Lake Corpus Christi?"),
    ("Concurrence & Tributary Starvation", "Explain concurrence in plain english and why upstream tributary starvation matters for Corpus Christi water supply"),
    ("Reservoir Stress Test (38% with 15% conservation)", f"Test reservoir at 38% storage with 15% conservation for {top_s.id}"),
]

for label, q in queries:
    print(f"\n--- Query: {label} ---")
    print(f"Q: '{q}'")
    ans = semantic_query_route(workspace, q)
    # Print first 6 lines of response
    lines = [line for line in ans.split("\n") if line.strip()][:6]
    for l in lines:
        print(f"  {l}")

print("\n" + "=" * 80)
print("TEST EXECUTION COMPLETED SUCCESSFULLY")
print("=" * 80)
