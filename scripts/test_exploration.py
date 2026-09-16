import json
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
from basin_core.water_system import REGION_N_PRESET

source = CachedSource()
stations = tuple(source.daily.columns)
print("Stations in dataset:", stations)

params = ScenarioParams(
    stations=stations,
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

# Check weights
weights = {"severity": 35, "concurrence": 30, "duration": 20, "season": 15}
ws.rerank(weights)
ws.rebuild_shortlist()

print(f"\nWorkspace ID: {ws.id}")
print(f"Total candidates generated: {len(ws.scenarios)}")
print("Shortlisted scenarios after applying regional planning weights:")
for sid in ws.selected:
    s = ws.get(sid)
    f = s.features
    p = s.provenance
    print(f"ID: {s.id} | Cluster: {s.cluster} ({s.cluster_name}) | Score: {s.score:.2f}")
    print(f"  Window: {p['source_start']} to {p['source_end']} ({f['duration_days']} days)")
    print(f"  Deficit: {f['deficit_mm']:.1f} mm ({f['deficit_mm']/25.4:.2f} in) | Historical %ile: {f['historical_percentile']:.1%}")
    print(f"  Concurrence: {f['concurrence']:.1%} | High-pri season fraction: {f['high_priority_season_fraction']:.1%}")
    print(f"  Max dry days: {f['max_dry_days']} | Retention by station: {p['retention_by_station']}")
