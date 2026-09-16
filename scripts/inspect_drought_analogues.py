import sys
from pathlib import Path
ROOT = Path.cwd()
sys.path.insert(0, str(ROOT))

from basin_core.data import CachedSource
from basin_core.engine import ScenarioParams
from basin_core.workspace import Workspace

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

print("Top 15 ranked scenarios:")
ranked = sorted(ws.scenarios, key=lambda s: -s.score)
for i, s in enumerate(ranked[:15], 1):
    p = s.provenance
    f = s.features
    selected_marker = "[SELECTED]" if s.id in ws.selected else ""
    print(f"{i:2d}. {s.id} {selected_marker} | Score: {s.score:.2f} | Cluster {s.cluster} ({s.cluster_name})")
    print(f"    Window: {p['source_start']} to {p['source_end']} ({f['duration_days']}d) | Yr: {p['source_start'][:4]}")
    print(f"    Deficit: {f['deficit_mm']:.1f}mm ({f['deficit_mm']/25.4:.2f}in) | Concurrence: {f['concurrence']:.1%} | Summer Frac: {f['high_priority_season_fraction']:.1%}")

# Also check for 2011, 2012, 2009, 2022 scenarios
print("\nNotable historical drought year candidates:")
for yr in [2011, 2009, 2022, 2024, 1996]:
    matches = [s for s in ws.scenarios if s.provenance['source_start'].startswith(str(yr))]
    print(f"\n--- Year {yr} ({len(matches)} candidates) ---")
    for s in sorted(matches, key=lambda x: -x.score)[:3]:
        p = s.provenance
        f = s.features
        selected_marker = "[SELECTED]" if s.id in ws.selected else ""
        print(f"  {s.id} {selected_marker} | Score: {s.score:.2f} | Cluster {s.cluster} | {p['source_start']} to {p['source_end']} ({f['duration_days']}d) | Deficit: {f['deficit_mm']:.1f}mm ({f['deficit_mm']/25.4:.2f}in) | Conc: {f['concurrence']:.1%}")
