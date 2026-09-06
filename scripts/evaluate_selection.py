"""Predefined diagnostic comparison; not a claim of scientific validity or user benefit."""
from pathlib import Path
import json
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from basin_core.analysis import comparison
from basin_core.data import CachedSource, ROOT
from basin_core.engine import ScenarioParams
from basin_core.workspace import Workspace


def evaluate():
    source = CachedSource()
    all_stations = tuple(source.daily.columns)
    results = []
    for seed in (7, 22, 91):
        for profile, stations, durations, extent in (
                ("multiple durations", all_stations, (90, 180, 270), "All stations"),
                ("mixed station perturbation", all_stations, (30, 90, 365), "Mixed"),
                ("single station", all_stations[:1], (90, 180, 270), "All stations")):
            w = Workspace(source, ScenarioParams(stations, durations=durations, extent=extent, seed=seed))
            results.append({"seed": seed, "profile": profile, "candidate_count": len(w.scenarios),
                            "silhouette": w.clustering["silhouette"], "comparison": comparison(w.scenarios, w.selected, seed)})
    target = ROOT / "output/selection-evaluation.json"
    target.parent.mkdir(exist_ok=True)
    target.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    evaluate()
