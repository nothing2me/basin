from __future__ import annotations

from abc import ABC, abstractmethod
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score, pairwise_distances
from threadpoolctl import threadpool_limits

from basin_core.engine import Scenario

DEFAULT_WEIGHTS = {"severity": 40, "duration": 25, "concurrence": 25, "season": 10}

COMMUNITY_PRESETS = {
    "Rural Water District (Nueces County WCID #3)": {"severity": 30, "duration": 10, "concurrence": 10, "season": 50},
    "River Basin Authority (Nueces Basin)": {"severity": 15, "duration": 35, "concurrence": 40, "season": 10},
    "County Emergency Management": {"severity": 50, "duration": 30, "concurrence": 10, "season": 10},
}


def label_profile(c: np.ndarray) -> str:
    perc, dur, conc, summer, dry = c[0], c[1] * 365, c[2], c[3], c[4] * 365
    parts = []
    if conc >= 0.45:
        parts.append("Multi-Basin Concurrent")
    elif summer >= 0.50:
        parts.append("Peak Summer")
    elif dur >= 210:
        parts.append("Prolonged Multi-Season")
    elif summer <= 0.15:
        parts.append("Winter-Spring")
    elif dry >= 45:
        parts.append("Extended Dry Spell")
    else:
        parts.append("Moderate Regional")

    if perc >= 0.85:
        parts.append("Severe Deficit")
    elif perc >= 0.60:
        parts.append("Elevated Deficit")
    else:
        parts.append("Deficit")
    return " ".join(parts)


def vector(s: Scenario) -> list[float]:
    f = s.features
    return [f["historical_percentile"], f["duration_days"] / 365,
            f["concurrence"], f["high_priority_season_fraction"], f["max_dry_days"] / 365,
            *[min(v / max(f["expected_mm"], 1), 1) for v in f["station_deficits_mm"].values()]]


class RankingStrategy(ABC):
    @abstractmethod
    def apply(self, scenarios, weights): ...


class WeightedSumRanking(RankingStrategy):
    def apply(self, scenarios: list[Scenario], weights: dict):
        if set(weights) != set(DEFAULT_WEIGHTS) or any(not np.isfinite(v) or v < 0 for v in weights.values()) or sum(weights.values()) <= 0:
            raise ValueError("Ranking priorities must be nonnegative with at least one positive value")
        total = sum(weights.values())
        for s in scenarios:
            f = s.features
            raw = {"severity": f["historical_percentile"], "duration": f["duration_days"] / 365,
                   "concurrence": f["concurrence"], "season": f["high_priority_season_fraction"]}
            s.components = {k: 100 * weights[k] / total * raw[k] for k in weights}
            s.score = sum(s.components.values())


class ScenarioClusterer:
    def fit(self, scenarios: list[Scenario], count=6) -> dict:
        if not scenarios:
            raise ValueError("No scenarios to group")
        x = np.asarray([vector(s) for s in scenarios])
        count = min(count, len(np.unique(x, axis=0)), len(x))
        with threadpool_limits(limits=1):
            model = KMeans(n_clusters=count, random_state=22, n_init=10).fit(x)
        # Canonicalize labels by centroid to keep group numbering deterministic.
        ordered = sorted(range(count), key=lambda i: tuple(model.cluster_centers_[i]))
        mapping = {old: new + 1 for new, old in enumerate(ordered)}
        labels = [mapping[int(label)] for label in model.labels_]

        # Compute semantic profile names for each canonicalized cluster
        group_profiles = {}
        for new_label, old_idx in enumerate(ordered, start=1):
            group_profiles[new_label] = label_profile(model.cluster_centers_[old_idx])

        for scenario, label in zip(scenarios, labels):
            scenario.cluster = label
            scenario.cluster_name = group_profiles.get(label, f"Group {label}")
        silhouette = float(silhouette_score(x, labels, sample_size=min(500, len(x)), random_state=22)) if 1 < count < len(x) else None
        return {"method": "KMeans", "seed": 22, "n_init": 10, "groups": count,
                "group_profiles": group_profiles,
                "feature_scaling": "fixed domain scales, see methodology.md", "silhouette": silhouette}


def shortlist(scenarios: list[Scenario], count: int) -> list[str]:
    if not 1 <= count <= len(scenarios):
        raise ValueError("Shortlist size is out of bounds")
    ranked = sorted(scenarios, key=lambda s: (-s.score, s.id))
    leaders = []
    groups = set()
    for s in ranked:
        if s.cluster not in groups:
            leaders.append(s)
            groups.add(s.cluster)
    chosen = leaders[:count]
    for s in ranked:
        if len(chosen) >= count:
            break
        if s not in chosen:
            chosen.append(s)
    return [s.id for s in chosen]


def comparison(scenarios: list[Scenario], selected: list[str], seed: int) -> list[dict]:
    rng = np.random.default_rng(seed)
    by_id = {s.id: s for s in scenarios}
    n = len(selected)
    choices = {"BASIN diverse shortlist": [by_id[i] for i in selected],
               "Score only": sorted(scenarios, key=lambda s: (-s.score, s.id))[:n],
               "Seeded random": [scenarios[int(i)] for i in rng.choice(len(scenarios), n, replace=False)]}
    result = []
    for name, items in choices.items():
        dist = pairwise_distances([vector(s) for s in items])
        separation = float(dist[np.triu_indices(n, 1)].mean()) if n > 1 else 0.0
        result.append({"Method": name, "Groups covered": len({s.cluster for s in items}),
                       "Mean feature distance": round(separation, 3),
                       "Mean priority score": round(float(np.mean([s.score for s in items])), 1)})
    return result


def simulate_reservoir_drawdown(
    series: pd.DataFrame,
    initial_pct: float = 0.48
) -> pd.DataFrame:
    """
    Physical mass-balance reservoir storage simulation across the Region N system
    (Lake Corpus Christi and Choke Canyon Reservoir), calibrated to Texas Water
    Development Board (TWDB) historical conservation pool capacities and Drought
    Contingency Plan (DCP) operational triggers.

    Conservation capacities:
      Lake Corpus Christi (LCC): 257,300 ac-ft
      Choke Canyon Reservoir (CCR): 662,600 ac-ft
      Combined Conservation Pool: 919,900 ac-ft

    Drought Contingency Plan (DCP) combined storage triggers:
      Stage 1 (Mild Drought): Combined < 40% (367,960 ac-ft)
      Stage 2 (Moderate Drought): Combined < 30% (275,970 ac-ft)
      Stage 3 (Critical / Mandatory Cuts): Combined < 20% (183,980 ac-ft)
      Stage 4 (Emergency): Combined < 15% (137,985 ac-ft)
    """
    cap_lcc = 257300.0
    cap_ccr = 662600.0
    cap_total = cap_lcc + cap_ccr

    storage_lcc = cap_lcc * initial_pct
    storage_ccr = cap_ccr * initial_pct

    records = []
    mean_daily_prcp = series.mean(axis=1)

    for step, (date, prcp_mm) in enumerate(mean_daily_prcp.items()):
        month = getattr(date, "month", 7)
        # Seasonal pan evaporation (ac-ft/day) based on TWDB historical net evaporation rates
        evap_daily = 750.0 if month in [6, 7, 8, 9] else 380.0

        # Base regional municipal and industrial demand (~180 MGD minus ~60 MGD Mary Rhodes pipeline)
        demand_daily = 370.0

        # Catchment inflow response during drought (calibrated runoff response + baseflow)
        inflow = 30.0 + (float(prcp_mm) * 45.0)

        net_loss = demand_daily + evap_daily - inflow

        # Lower Nueces priority rule: draw LCC first until 20%, then CCR supplements
        if storage_lcc > cap_lcc * 0.20:
            loss_lcc = min(max(net_loss * 0.65, 0.0), storage_lcc)
            loss_ccr = max(net_loss - loss_lcc, 0.0)
        else:
            loss_lcc = min(max(net_loss * 0.15, 0.0), storage_lcc)
            loss_ccr = max(net_loss - loss_lcc, 0.0)

        storage_lcc = max(0.0, min(cap_lcc, storage_lcc - loss_lcc))
        storage_ccr = max(0.0, min(cap_ccr, storage_ccr - loss_ccr))
        comb = storage_lcc + storage_ccr
        comb_pct = comb / cap_total

        if comb_pct < 0.15:
            stage = "Stage 4 (Emergency)"
            stage_num = 4
        elif comb_pct < 0.20:
            stage = "Stage 3 (Critical)"
            stage_num = 3
        elif comb_pct < 0.30:
            stage = "Stage 2 (Moderate)"
            stage_num = 2
        elif comb_pct < 0.40:
            stage = "Stage 1 (Mild)"
            stage_num = 1
        else:
            stage = "Normal"
            stage_num = 0

        records.append({
            "day": step + 1,
            "date": str(date)[:10],
            "lcc_acft": round(storage_lcc, 1),
            "lcc_pct": round(storage_lcc / cap_lcc * 100, 1),
            "ccr_acft": round(storage_ccr, 1),
            "ccr_pct": round(storage_ccr / cap_ccr * 100, 1),
            "combined_acft": round(comb, 1),
            "combined_pct": round(comb_pct * 100, 1),
            "stage": stage,
            "stage_num": stage_num,
            "prcp_mm": round(float(prcp_mm), 2),
            "evap_acft": round(evap_daily, 1),
            "demand_acft": round(demand_daily, 1),
            "net_loss_acft": round(net_loss, 1)
        })

    return pd.DataFrame(records)

