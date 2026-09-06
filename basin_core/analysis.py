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
    "Illustrative rural provider": {"severity": 30, "duration": 10, "concurrence": 10, "season": 50},
    "Illustrative regional planner": {"severity": 15, "duration": 35, "concurrence": 40, "season": 10},
    "Illustrative emergency planner": {"severity": 50, "duration": 30, "concurrence": 10, "season": 10},
}


def label_profile(c: np.ndarray, station_count=3) -> str:
    perc, dur, conc, summer, dry = c[0], c[1] * 365, c[2], c[3], c[4] * 365
    parts = []
    if conc >= 0.45:
        parts.append("Concurrent Stations" if station_count > 1 else "Frequent Station Stress")
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
            group_profiles[new_label] = label_profile(model.cluster_centers_[old_idx], len(scenarios[0].series.columns))

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


RESERVOIR_ASSUMPTIONS = {
    "model_version": "illustrative-balance-2",
    "scope": "Uncalibrated two-pool experiment; no forecast or official restriction dates. Excluded from session evidence packets and replay verification.",
    "capacities_acft": {"Lake Corpus Christi": 257300.0, "Choke Canyon": 662600.0},
    "inflow": "30 + 45 × equal-station mean rainfall (mm/day), in ac-ft/day; illustrative coefficient, no catchment calibration",
    "evaporation": "Potential loss 750 ac-ft/day in June–September, 380 otherwise; illustrative fixed seasonal assumption",
    "demand": "Requested 370 ac-ft/day with pipeline availability, 554 otherwise; conservation reduces this request",
    "allocation": "Inflow proportional to capacities; evaporation proportional to available water; demand targets 65% from LCC above 20% storage, 15% otherwise, with remaining water covering any shortfall; remaining excess spills",
    "thresholds": "Illustrative combined-storage bands at 40%, 30%, 20%, 15%; not current official policy",
    "time_step": "Daily: add inflow, serve available evaporation and demand, spill excess. Rows report end-of-day storage.",
}


def simulate_reservoir_drawdown(series: pd.DataFrame, initial_pct: float = 0.48,
                                conservation_pct: float = 0.0, pipeline_active: bool = True) -> pd.DataFrame:
    """Illustrative daily water accounting, explicitly tracking unserved losses and spill."""
    if not isinstance(series, pd.DataFrame) or series.empty or not len(series.columns):
        raise ValueError("Provide a nonempty daily rainfall table")
    if not isinstance(series.index, pd.DatetimeIndex) or not series.index.equals(pd.date_range(series.index[0], periods=len(series))):
        raise ValueError("Reservoir experiment requires consecutive daily dates")
    values = series.to_numpy(dtype=float)
    if not np.isfinite(values).all() or (values < 0).any():
        raise ValueError("Reservoir rainfall must be finite, nonnegative and complete")
    for label, value in (("Initial storage", initial_pct), ("Conservation", conservation_pct)):
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not np.isfinite(value) or not 0 <= value <= 1:
            raise ValueError(label + " must be a fraction from 0 to 1")
    if type(pipeline_active) is not bool:
        raise ValueError("Pipeline availability must be true or false")
    caps = np.array([257300.0, 662600.0])
    storage = caps * initial_pct
    records = []
    for step, (date, rain) in enumerate(series.mean(axis=1).items()):
        beginning = float(storage.sum())
        inflow = 30.0 + float(rain) * 45.0
        potential_evap = 750.0 if date.month in (6, 7, 8, 9) else 380.0
        requested_demand = (370.0 if pipeline_active else 554.0) * (1 - conservation_pct)
        storage += inflow * caps / caps.sum()
        actual_evap = min(potential_evap, float(storage.sum()))
        if storage.sum() > 0:
            storage -= actual_evap * storage / storage.sum()
        fraction = .65 if storage[0] > caps[0] * .20 else .15
        withdrawals = np.minimum(storage, requested_demand * np.array([fraction, 1 - fraction]))
        storage -= withdrawals
        served = float(withdrawals.sum())
        for tank in (0, 1):
            extra = min(float(storage[tank]), max(0.0, requested_demand - served))
            storage[tank] -= extra
            served += extra
        spill = float(np.maximum(storage - caps, 0).sum())
        storage = np.clip(storage, 0, caps)
        combined = float(storage.sum())
        pct = combined / caps.sum() * 100
        band = 4 if pct < 15 else 3 if pct < 20 else 2 if pct < 30 else 1 if pct < 40 else 0
        records.append({"day": step + 1, "date": str(date.date()),
                        "lcc_acft": float(storage[0]), "lcc_pct": float(storage[0] / caps[0] * 100),
                        "ccr_acft": float(storage[1]), "ccr_pct": float(storage[1] / caps[1] * 100),
                        "combined_acft": combined, "combined_pct": pct, "beginning_acft": beginning,
                        "stage": f"Illustrative band {band}", "stage_num": band, "prcp_mm": float(rain),
                        "inflow_acft": inflow, "evap_acft": actual_evap, "potential_evap_acft": potential_evap,
                        "unmet_evap_acft": potential_evap - actual_evap,
                        "demand_acft": requested_demand, "served_demand_acft": served,
                        "unmet_demand_acft": max(0.0, requested_demand - served), "spill_acft": spill,
                        "net_loss_acft": requested_demand + potential_evap - inflow,
                        "balance_error_acft": combined - (beginning + inflow - actual_evap - served - spill)})
    return pd.DataFrame(records)
