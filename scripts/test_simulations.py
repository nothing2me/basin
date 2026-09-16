import sys
from pathlib import Path
import pandas as pd
import numpy as np

ROOT = Path.cwd()
sys.path.insert(0, str(ROOT))

from basin_core.data import CachedSource
from basin_core.engine import ScenarioParams
from basin_core.workspace import Workspace
from basin_core.analysis_context import AnalysisContext
from basin_core.simulation import SimulationSettings, calculate
from basin_core.water_system import REGION_N_PRESET

source = CachedSource()
params = ScenarioParams(
    stations=tuple(source.daily.columns),
    durations=(90, 180, 270),
    months=(1, 4, 7, 10),
    retention_min=0.35,
    retention_max=0.85,
    extent="All stations",
    candidates=300,
    seed=22
)

context = AnalysisContext(
    scope="specific_provider",
    organization_type="regional_planning",
    organization_name="City of Corpus Christi & Nueces River Authority Joint Water Resources Planning Committee",
    counties=("Nueces", "San Patricio", "Live Oak", "McMullen"),
    community="Corpus Christi / Lower Nueces Basin",
    supply_relationship="regional_wholesale",
    decision_use="drought_plan"
)

ws = Workspace(source, params, size=6, analysis_context=context)
weights = {"severity": 35, "concurrence": 30, "duration": 20, "season": 15}
ws.rerank(weights)
ws.rebuild_shortlist()

settings = SimulationSettings.from_percent(
    initial_storage_percent=38.0,
    conservation_percent=15.0,
    baseline_kind="scenario_revision",
    pipeline_active=True,
    retention_percentages=(100, 80, 60, 40)
)

print(f"Total system capacity: {ws.water_system_selection.config.total_capacity_acft:,.1f} ac-ft")
initial_acft = ws.water_system_selection.config.total_capacity_acft * 0.38
stage2_acft = ws.water_system_selection.config.total_capacity_acft * 0.30
stage3_acft = ws.water_system_selection.config.total_capacity_acft * 0.20
print(f"Entering storage (38%): {initial_acft:,.1f} ac-ft")
print(f"Stage 2 trigger (30%): {stage2_acft:,.1f} ac-ft")
print(f"Stage 3 trigger (20%): {stage3_acft:,.1f} ac-ft")
print("="*80)

for sid in ws.selected:
    s = ws.get(sid)
    f, p = s.features, s.provenance
    run = ws.run_simulation(sid, settings)
    res = run["results"]
    print(f"\nScenario {sid} (Cluster {s.cluster}: {s.cluster_name})")
    print(f"  Window: {p['source_start']} to {p['source_end']} ({f['duration_days']} days)")
    print(f"  Deficit: {f['deficit_mm']:.1f} mm ({f['deficit_mm']/25.4:.2f} in) | Concurrence: {f['concurrence']:.1%}")
    print("  Stress Spectrum Summary Table (15% Emergency Conservation):")
    for row in res["summary_table"]:
        print(f"    Tier {row['retention_pct']:.0f}%: Min={row['min_pct']:.2f}% ({row['min_acft']:,.0f} ac-ft), Final={row['final_pct']:.2f}% ({row['final_acft']:,.0f} ac-ft), Day Stage 3 (20%)={row['day_stage3_20']}")
    print("  Conservation Comparison (0% vs 15% curtailment):")
    for comp in res["conservation_comparison"]:
        print(f"    Tier {comp['retention_percent']:.0f}%: No Cons Day 20={comp['no_conservation_day_20']} | 15% Cons Day 20={comp['chosen_conservation_day_20']} | Delay={comp['delay_days']} days")
        print(f"      Mean Evap={comp['mean_evaporation_acft_per_day']:.1f} ac-ft/day | Mean Demand={comp['mean_served_demand_acft_per_day']:.1f} ac-ft/day | Ratio (Evap/Demand)={comp['mean_evaporation_acft_per_day']/comp['mean_served_demand_acft_per_day']:.2f}x")
