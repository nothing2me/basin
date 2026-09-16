import sys
from pathlib import Path
import pandas as pd
import numpy as np

ROOT = Path.cwd()
sys.path.insert(0, str(ROOT))

from basin_core.data import CachedSource
from basin_core.engine import ScenarioParams
from basin_core.workspace import Workspace
from basin_core.simulation import SimulationSettings

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

ws = Workspace(source, params, size=6)
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

print("Stage 2 (30% combined capacity = 275,970 ac-ft) crossing days:")
for sid in ws.selected:
    s = ws.get(sid)
    run = ws.run_simulation(sid, settings)
    
    # Check trajectories for tier 1.0 (100% retained)
    traj_15 = run["results"]["trajectories"]["1.0"] # 15% conservation
    traj_0 = run["results"]["no_conservation_trajectories"]["1.0"] # 0% conservation
    
    day_stage2_0 = next((row["day"] for row in traj_0 if row["combined_pct"] <= 30.0), None)
    day_stage2_15 = next((row["day"] for row in traj_15 if row["combined_pct"] <= 30.0), None)
    
    day_stage3_0 = next((row["day"] for row in traj_0 if row["combined_pct"] <= 20.0), None)
    day_stage3_15 = next((row["day"] for row in traj_15 if row["combined_pct"] <= 20.0), None)

    print(f"\nScenario {sid} ({s.cluster_name}, {s.features['duration_days']}d, window: {s.provenance['source_start']} to {s.provenance['source_end']}):")
    print(f"  Stage 2 (30%): 0% Cons = Day {day_stage2_0} | 15% Cons = Day {day_stage2_15} | Difference = {(day_stage2_15 - day_stage2_0) if day_stage2_0 and day_stage2_15 else 'N/A'} days")
    print(f"  Stage 3 (20%): 0% Cons = Day {day_stage3_0} | 15% Cons = Day {day_stage3_15} | Difference = {(day_stage3_15 - day_stage3_0) if day_stage3_0 and day_stage3_15 else 'N/A'} days")
