from __future__ import annotations

from abc import ABC, abstractmethod
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score, pairwise_distances
from threadpoolctl import threadpool_limits

from basin_core.engine import Scenario
from basin_core.water_system import WaterSource, WaterSystemConfig, REGION_N_PRESET, SYSTEM_PRESETS

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


RESERVOIR_ASSUMPTIONS = REGION_N_PRESET.describe_assumptions()


PAN_EVAP_MONTH_WEIGHTS = (0.04, 0.05, 0.07, 0.09, 0.11, 0.14, 0.15, 0.14, 0.10, 0.06, 0.03, 0.02)


def simulate_reservoir_drawdown(series: pd.DataFrame, initial_pct: float = 0.48,
                                conservation_pct: float = 0.0, pipeline_active: bool = True,
                                config: WaterSystemConfig | None = None,
                                use_smooth_evap: bool = False,
                                use_eac_scaling: bool = False) -> pd.DataFrame:
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

    cfg = config if config is not None else REGION_N_PRESET
    cfg.validate()
    n_sources = len(cfg.sources)
    caps = np.array([s.capacity_acft for s in cfg.sources], dtype=float)
    total_cap = float(caps.sum())
    storage = caps * initial_pct
    records = []
    base_inflow = sum(s.inflow_base_acft for s in cfg.sources)
    inflow_sens = sum(s.inflow_sensitivity for s in cfg.sources)
    summer_evap = sum(s.evap_summer_acft for s in cfg.sources)
    winter_evap = sum(s.evap_winter_acft for s in cfg.sources)
    annual_mean_daily_evap = (4.0 * summer_evap + 8.0 * winter_evap) / 12.0

    for step, (date, rain) in enumerate(series.mean(axis=1).items()):
        beginning = float(storage.sum())
        inflow = base_inflow + float(rain) * inflow_sens

        smooth_active = use_smooth_evap or getattr(cfg, "use_smooth_evap", False)
        eac_active = use_eac_scaling or getattr(cfg, "use_eac_scaling", False)

        # Smooth 12-month pan evaporation curve (Item 3)
        if smooth_active:
            m_idx = date.month - 1
            month_factor = PAN_EVAP_MONTH_WEIGHTS[m_idx] * 12.0
            day_potential_evap = annual_mean_daily_evap * month_factor
        else:
            day_potential_evap = summer_evap if date.month in (6, 7, 8, 9) else winter_evap

        # Surface area EAC scaling (Item 2)
        if eac_active and total_cap > 0:
            current_fraction = max(0.0, min(1.0, beginning / total_cap))
            eac_scale = max(0.15, current_fraction ** 0.65)
            potential_evap = day_potential_evap * eac_scale
        else:
            potential_evap = day_potential_evap

        if pipeline_active or cfg.demand_no_pipeline_acft_day is None:
            dem = cfg.demand_acft_day
        else:
            dem = cfg.demand_no_pipeline_acft_day
        requested_demand = dem * (1 - conservation_pct)

        storage += inflow * caps / caps.sum()
        actual_evap = min(potential_evap, float(storage.sum()))
        if storage.sum() > 0:
            storage -= actual_evap * storage / storage.sum()

        if n_sources == 2:
            fraction = cfg.allocation_primary_fraction if storage[0] > caps[0] * cfg.allocation_threshold_pct else cfg.allocation_secondary_fraction
            withdrawals = np.minimum(storage, requested_demand * np.array([fraction, 1 - fraction]))
            storage -= withdrawals
            served = float(withdrawals.sum())
            for tank in (0, 1):
                extra = min(float(storage[tank]), max(0.0, requested_demand - served))
                storage[tank] -= extra
                served += extra
        elif n_sources == 1:
            served = min(float(storage[0]), requested_demand)
            storage[0] -= served
        else:
            proportions = storage / storage.sum() if storage.sum() > 0 else caps / caps.sum()
            withdrawals = np.minimum(storage, requested_demand * proportions)
            storage -= withdrawals
            served = float(withdrawals.sum())
            for tank in range(n_sources):
                extra = min(float(storage[tank]), max(0.0, requested_demand - served))
                storage[tank] -= extra
                served += extra

        spill = float(np.maximum(storage - caps, 0).sum())
        storage = np.clip(storage, 0, caps)
        combined = float(storage.sum())
        pct = combined / caps.sum() * 100

        band = 0
        if len(cfg.stage_bands_pct) >= 4:
            b40, b30, b20, b15 = cfg.stage_bands_pct[:4]
            band = 4 if pct < b15 * 100 else 3 if pct < b20 * 100 else 2 if pct < b30 * 100 else 1 if pct < b40 * 100 else 0
        else:
            for b_idx, b_thresh in enumerate(sorted(cfg.stage_bands_pct, reverse=True)):
                if pct < b_thresh * 100:
                    band = b_idx + 1

        rec = {
            "day": step + 1, "date": str(date.date()),
            "combined_acft": combined, "combined_pct": pct, "beginning_acft": beginning,
            "stage": f"Illustrative band {band}", "stage_num": band, "prcp_mm": float(rain),
            "inflow_acft": inflow, "evap_acft": actual_evap, "potential_evap_acft": potential_evap,
            "unmet_evap_acft": potential_evap - actual_evap,
            "demand_acft": requested_demand, "served_demand_acft": served,
            "unmet_demand_acft": max(0.0, requested_demand - served), "spill_acft": spill,
            "net_loss_acft": requested_demand + potential_evap - inflow,
            "balance_error_acft": combined - (beginning + inflow - actual_evap - served - spill),
        }
        for i, s in enumerate(cfg.sources):
            rec[f"source_{i}_name"] = s.name
            rec[f"source_{i}_acft"] = float(storage[i])
            rec[f"source_{i}_pct"] = float(storage[i] / caps[i] * 100)

        if n_sources >= 2:
            rec["lcc_acft"] = float(storage[0])
            rec["lcc_pct"] = float(storage[0] / caps[0] * 100)
            rec["ccr_acft"] = float(storage[1])
            rec["ccr_pct"] = float(storage[1] / caps[1] * 100)
        else:
            rec["lcc_acft"] = float(storage[0])
            rec["lcc_pct"] = float(storage[0] / caps[0] * 100)
            rec["ccr_acft"] = 0.0
            rec["ccr_pct"] = 0.0

        records.append(rec)
    return pd.DataFrame(records)


def threshold_crossing_day(simulation: pd.DataFrame, initial_fraction: float, threshold_percent: float) -> int | None:
    if initial_fraction * 100 <= threshold_percent:
        return 0
    crossed = simulation.loc[simulation["combined_pct"] <= threshold_percent, "day"]
    return int(crossed.iloc[0]) if len(crossed) else None


def threshold_text(day: int | None) -> str:
    return "Not reached within modeled period" if day is None else "Already at/below at start (day 0)" if day == 0 else f"Day {day} (end of day)"


def simulate_stress_spectrum(series: pd.DataFrame,
                             tiers: tuple[float, ...] = (1.0, 0.8, 0.6, 0.4),
                             initial_pct: float = 0.48,
                             conservation_pct: float = 0.0,
                             pipeline_active: bool = True,
                             config: WaterSystemConfig | None = None) -> dict:
    """Simulate reservoir storage drawdown across multiple rainfall stress tiers simultaneously.

    tiers: tuple of rainfall retention multipliers (e.g. 1.0 = 100%, 0.8 = 80%, 0.6 = 60%, 0.4 = 40%).
    Returns a dict containing simulation results for each tier, combined trajectory dataframes,
    and a summary table of threshold breach countdowns.
    """
    cfg = config if config is not None else REGION_N_PRESET
    tier_results = {}
    summary_rows = []

    tier_labels = {
        1.0: "Selected scenario (100%)",
        0.8: "20% additional rainfall reduction",
        0.6: "40% additional rainfall reduction",
        0.4: "60% additional rainfall reduction",
    }

    for mult in tiers:
        m = float(mult)
        scaled_series = series * m
        sim_df = simulate_reservoir_drawdown(
            scaled_series,
            initial_pct=initial_pct,
            conservation_pct=conservation_pct,
            pipeline_active=pipeline_active,
            config=cfg,
        )
        unrounded_min = float(sim_df["combined_pct"].min())
        min_pct = round(unrounded_min, 1)
        min_acft = round(float(sim_df["combined_acft"].min()), 0)
        final_pct = round(float(sim_df["combined_pct"].iloc[-1]), 1)
        final_acft = round(float(sim_df["combined_acft"].iloc[-1]), 0)

        critical_thresh = cfg.stage_bands_pct[2] * 100 if len(cfg.stage_bands_pct) >= 3 else 20.0
        day_b1 = threshold_crossing_day(sim_df, initial_pct, cfg.stage_bands_pct[0] * 100 if len(cfg.stage_bands_pct) >= 1 else 40.0)
        day_b2 = threshold_crossing_day(sim_df, initial_pct, cfg.stage_bands_pct[1] * 100 if len(cfg.stage_bands_pct) >= 2 else 30.0)
        day_b3 = threshold_crossing_day(sim_df, initial_pct, critical_thresh)
        day_b4 = threshold_crossing_day(sim_df, initial_pct, cfg.stage_bands_pct[3] * 100 if len(cfg.stage_bands_pct) >= 4 else 15.0)
        survived = bool(initial_pct * 100 > critical_thresh and unrounded_min > critical_thresh)

        label = tier_labels.get(round(m, 2), f"{int(round(m * 100))}% ({(int(round(m * 100)) - 100):+d}% Rain)")

        row = {
            "tier_multiplier": m,
            "tier_label": label,
            "retention_pct": round(m * 100, 1),
            "reduction_pct": round((1.0 - m) * 100, 1),
            "min_pct": min_pct,
            "min_acft": min_acft,
            "final_pct": final_pct,
            "final_acft": final_acft,
            "day_stage1_40": day_b1,
            "day_stage2_30": day_b2,
            "day_stage3_20": day_b3,
            "day_emergency_15": day_b4,
            "survived_critical_20pct": survived,
            "status": "✅ Survived" if survived else "❌ Breached (Stage 3)",
        }
        summary_rows.append(row)
        tier_results[m] = {
            "df": sim_df,
            "metrics": row,
        }

    return {
        "tier_results": tier_results,
        "summary_table": summary_rows,
        "duration_days": len(series),
        "initial_pct": round(initial_pct * 100, 1),
        "conservation_pct": round(conservation_pct * 100, 1),
        "pipeline_active": pipeline_active,
        "config": cfg,
    }

