from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import replace
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
                                use_eac_scaling: bool = False,
                                stepped_policy: bool = False,
                                policy_schedule: dict[int, float] | None = None,
                                pipeline_reliability_pct: float | None = None) -> pd.DataFrame:
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
    if type(stepped_policy) is not bool:
        raise ValueError("stepped_policy must be true or false")
    if policy_schedule is not None:
        if not isinstance(policy_schedule, dict):
            raise ValueError("policy_schedule must be a dictionary")
        for k, v in policy_schedule.items():
            if isinstance(k, bool) or not isinstance(k, int) or k < 0:
                raise ValueError("policy_schedule keys must be non-negative integers")
            if isinstance(v, bool) or not isinstance(v, (int, float)) or not np.isfinite(v) or not 0 <= v <= 1:
                raise ValueError("policy_schedule values must be fractions from 0 to 1")
    if pipeline_reliability_pct is not None:
        if isinstance(pipeline_reliability_pct, bool) or not isinstance(pipeline_reliability_pct, (int, float)) or not np.isfinite(pipeline_reliability_pct) or not 0 <= pipeline_reliability_pct <= 1:
            raise ValueError("Pipeline reliability must be a fraction from 0 to 1")

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
    full_surface_area_acres = sum(s.capacity_acft / 12.8 for s in cfg.sources) if cfg.sources else 0.0

    for step, (date, rain) in enumerate(series.mean(axis=1).items()):
        beginning = float(storage.sum())
        inflow = base_inflow + float(rain) * inflow_sens

        # TCEQ Emergency Inflow Order pass-through accounting
        estuary_pass_through = 0.0
        if getattr(cfg, "estuary_order_active", False):
            thresh = getattr(cfg, "estuary_threshold_pct", 0.50)
            if total_cap > 0 and (beginning / total_cap) > thresh:
                estuary_pass_through = min(
                    inflow * getattr(cfg, "estuary_pass_through_fraction", 0.0),
                    getattr(cfg, "estuary_pass_through_cap_acft_day", 0.0),
                )
                inflow -= estuary_pass_through

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
            est_surface_area = full_surface_area_acres * eac_scale
        else:
            eac_scale = 1.0
            potential_evap = day_potential_evap
            est_surface_area = full_surface_area_acres

        # Conditional / Tiered Pipeline Import Reliability (Item 5)
        if pipeline_reliability_pct is not None:
            rel = float(pipeline_reliability_pct)
            if cfg.demand_no_pipeline_acft_day is not None:
                pipeline_yield = max(0.0, cfg.demand_no_pipeline_acft_day - cfg.demand_acft_day)
                dem = cfg.demand_no_pipeline_acft_day - (pipeline_yield * rel)
            else:
                dem = cfg.demand_acft_day
        elif pipeline_active or cfg.demand_no_pipeline_acft_day is None:
            dem = cfg.demand_acft_day
        else:
            dem = cfg.demand_no_pipeline_acft_day

        # Dynamic Stepped Policy Schedule (Item 1)
        stepped_active = stepped_policy or getattr(cfg, "stepped_policy_active", False)
        if stepped_active:
            current_fraction = beginning / total_cap if total_cap > 0 else 0.0
            sched = policy_schedule if policy_schedule is not None else getattr(cfg, "policy_schedule", None) or {0: 0.0, 1: 0.05, 2: 0.15, 3: 0.30, 4: 0.50}
            if len(cfg.stage_bands_pct) >= 4:
                b40, b30, b20, b15 = cfg.stage_bands_pct[:4]
                curr_stage = 4 if current_fraction <= b15 else 3 if current_fraction <= b20 else 2 if current_fraction <= b30 else 1 if current_fraction <= b40 else 0
            else:
                curr_stage = 0
                for b_idx, b_thresh in enumerate(sorted(cfg.stage_bands_pct, reverse=True)):
                    if current_fraction <= b_thresh:
                        curr_stage = b_idx + 1
            effective_cons_pct = float(sched.get(curr_stage, conservation_pct))
        else:
            effective_cons_pct = conservation_pct

        # Sector-Disaggregated Demand (Item 3)
        dom_pct = getattr(cfg, "demand_domestic_pct", 40.0)
        ind_pct = getattr(cfg, "demand_industrial_pct", 50.0)
        out_pct = getattr(cfg, "demand_outdoor_pct", 10.0)
        who_pct = getattr(cfg, "demand_wholesale_pct", 0.0)

        dom_base = dem * (dom_pct / 100.0)
        ind_base = dem * (ind_pct / 100.0)
        out_base = dem * (out_pct / 100.0)
        who_base = dem * (who_pct / 100.0)

        # Dynamic hierarchical stage curtailment
        if getattr(cfg, "stage_curtailment_active", False):
            current_fraction = beginning / total_cap if total_cap > 0 else 0.0
            band_1, band_2, band_3, band_4 = cfg.stage_bands_pct[:4]
            if current_fraction <= band_4:
                dom_req = dom_base * 0.80
                ind_req = ind_base * 0.70
                out_req = 0.0
                who_req = who_base * 0.75
            elif current_fraction <= band_3:
                dom_req = dom_base * 0.90
                ind_req = ind_base
                out_req = 0.0
                who_req = who_base * 0.85
            elif current_fraction <= band_2:
                dom_req = dom_base
                ind_req = ind_base
                out_req = out_base * 0.50
                who_req = who_base * 0.95
            elif current_fraction <= band_1:
                dom_req = dom_base
                ind_req = ind_base
                out_req = out_base * 0.85
                who_req = who_base
            else:
                dom_req = dom_base
                ind_req = ind_base
                out_req = out_base
                who_req = who_base
            requested_demand = (dom_req + ind_req + out_req + who_req) * (1 - effective_cons_pct)
        else:
            requested_demand = dem * (1 - effective_cons_pct)
            dom_req = requested_demand * (dom_pct / 100.0)
            ind_req = requested_demand * (ind_pct / 100.0)
            out_req = requested_demand * (out_pct / 100.0)
            who_req = requested_demand * (who_pct / 100.0)

        storage += inflow * caps / caps.sum()
        actual_evap = min(potential_evap, float(storage.sum()))
        if storage.sum() > 0:
            storage -= actual_evap * storage / storage.sum()

        # Dead Storage & Physical Withdrawal Cap
        dead_storage = float(getattr(cfg, "dead_storage_acft", 0.0))
        available_above_dead = max(0.0, float(storage.sum()) - dead_storage)
        deliverable_demand = min(available_above_dead, requested_demand)

        if n_sources == 2:
            fraction = cfg.allocation_primary_fraction if storage[0] > caps[0] * cfg.allocation_threshold_pct else cfg.allocation_secondary_fraction
            withdrawals = np.minimum(storage, deliverable_demand * np.array([fraction, 1 - fraction]))
            storage -= withdrawals
            served = float(withdrawals.sum())
            for tank in (0, 1):
                extra = min(float(storage[tank]), max(0.0, deliverable_demand - served))
                storage[tank] -= extra
                served += extra
        elif n_sources == 1:
            served = min(float(storage[0]), deliverable_demand)
            storage[0] -= served
        else:
            proportions = storage / storage.sum() if storage.sum() > 0 else caps / caps.sum()
            withdrawals = np.minimum(storage, deliverable_demand * proportions)
            storage -= withdrawals
            served = float(withdrawals.sum())
            for tank in range(n_sources):
                extra = min(float(storage[tank]), max(0.0, deliverable_demand - served))
                storage[tank] -= extra
                served += extra

        # Sector delivery breakdown
        dom_target = dom_req * (1 - effective_cons_pct) if getattr(cfg, "stage_curtailment_active", False) else dom_req
        ind_target = ind_req * (1 - effective_cons_pct) if getattr(cfg, "stage_curtailment_active", False) else ind_req
        who_target = who_req * (1 - effective_cons_pct) if getattr(cfg, "stage_curtailment_active", False) else who_req
        out_target = out_req * (1 - effective_cons_pct) if getattr(cfg, "stage_curtailment_active", False) else out_req

        delivered_dom = min(dom_target, served)
        rem_served = served - delivered_dom
        delivered_ind = min(ind_target, rem_served)
        rem_served -= delivered_ind
        delivered_who = min(who_target, rem_served)
        rem_served -= delivered_who
        delivered_out = min(out_target, rem_served)

        is_day_zero = bool(available_above_dead <= 1e-6 and requested_demand > 0.0)

        spill = float(np.maximum(storage - caps, 0).sum())
        storage = np.clip(storage, 0, caps)
        combined = float(storage.sum())
        pct = combined / caps.sum() * 100

        # Bands are inclusive, like threshold_crossing_day: storage exactly at 20% is in the
        # 20% band. Only exact equality is affected; storage arithmetic is unchanged.
        band = 0
        if len(cfg.stage_bands_pct) >= 4:
            b40, b30, b20, b15 = cfg.stage_bands_pct[:4]
            band = 4 if pct <= b15 * 100 else 3 if pct <= b20 * 100 else 2 if pct <= b30 * 100 else 1 if pct <= b40 * 100 else 0
        else:
            for b_idx, b_thresh in enumerate(sorted(cfg.stage_bands_pct, reverse=True)):
                if pct <= b_thresh * 100:
                    band = b_idx + 1

        bal_err = combined - (beginning + inflow - actual_evap - served - spill)
        if abs(bal_err) >= 1e-6:
            raise ArithmeticError(f"Mass balance error on day {step + 1}: {bal_err}")

        rec = {
            "day": step + 1, "date": str(date.date()),
            "combined_acft": combined, "combined_pct": pct, "beginning_acft": beginning,
            "stage": f"Illustrative band {band}", "stage_num": band, "prcp_mm": float(rain),
            "inflow_acft": inflow, "evap_acft": actual_evap, "potential_evap_acft": potential_evap,
            "unmet_evap_acft": potential_evap - actual_evap,
            "demand_acft": requested_demand, "served_demand_acft": served,
            "unmet_demand_acft": max(0.0, requested_demand - served), "spill_acft": spill,
            "net_loss_acft": requested_demand + potential_evap - inflow,
            "balance_error_acft": bal_err,
            "is_day_zero": is_day_zero,
            "active_storage_acft": max(0.0, combined - dead_storage),
            "dead_storage_acft": dead_storage,
            "served_domestic_acft": delivered_dom,
            "served_industrial_acft": delivered_ind,
            "served_wholesale_acft": delivered_who,
            "served_outdoor_acft": delivered_out,
            "curtailed_domestic_acft": max(0.0, dom_base - delivered_dom) if getattr(cfg, "stage_curtailment_active", False) else 0.0,
            "curtailed_industrial_acft": max(0.0, ind_base - delivered_ind) if getattr(cfg, "stage_curtailment_active", False) else 0.0,
            "curtailed_wholesale_acft": max(0.0, who_base - delivered_who) if getattr(cfg, "stage_curtailment_active", False) else 0.0,
            "curtailed_outdoor_acft": max(0.0, out_base - delivered_out) if getattr(cfg, "stage_curtailment_active", False) else 0.0,
            "estuary_pass_through_acft": estuary_pass_through,
            "effective_conservation_pct": effective_cons_pct,
            "stepped_policy_active": stepped_active,
            "eac_scale": round(float(eac_scale), 4),
            "surface_area_acres": round(float(est_surface_area), 1),
            "pipeline_reliability_pct": float(pipeline_reliability_pct) if pipeline_reliability_pct is not None else (1.0 if pipeline_active else 0.0),
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


def threshold_day_label(day: int | None) -> str:
    """Compact crossing label shared by tables. Day 0 is a crossing, not a missing value."""
    if day is None:
        return "Not reached in window"
    return "Day 0 (at/below at start)" if day == 0 else f"Day {day}"


def rainfall_tier_label(multiplier: float) -> str:
    """Name a tier relative to the rainfall it multiplies.

    The input may already be a constructed or edited scenario, so a 100% tier is never
    called historical or a baseline here; each presentation states what the input is.
    """
    pct = round(float(multiplier) * 100, 1)
    text = f"{pct:g}% of input rainfall"
    if pct < 100:
        return f"{text} ({round(100 - pct, 1):g}% reduction)"
    if pct > 100:
        return f"{text} ({round(pct - 100, 1):g}% increase)"
    return text


def simulate_stress_spectrum(series: pd.DataFrame,
                             tiers: tuple[float, ...] = (1.0, 0.8, 0.6, 0.4),
                             initial_pct: float = 0.48,
                             conservation_pct: float = 0.0,
                             pipeline_active: bool = True,
                             config: WaterSystemConfig | None = None,
                             stepped_policy: bool = False,
                             policy_schedule: dict[int, float] | None = None,
                             pipeline_reliability_pct: float | None = None,
                             use_smooth_evap: bool = False,
                             use_eac_scaling: bool = False) -> dict:
    """Simulate reservoir storage drawdown across multiple rainfall stress tiers simultaneously.

    tiers: tuple of rainfall retention multipliers (e.g. 1.0 = 100%, 0.8 = 80%, 0.6 = 60%, 0.4 = 40%).
    Returns a dict containing simulation results for each tier, combined trajectory dataframes,
    and a summary table of threshold breach countdowns.
    """
    cfg = config if config is not None else REGION_N_PRESET
    tier_results = {}
    summary_rows = []

    for mult in tiers:
        m = float(mult)
        scaled_series = series * m
        sim_df = simulate_reservoir_drawdown(
            scaled_series,
            initial_pct=initial_pct,
            conservation_pct=conservation_pct,
            pipeline_active=pipeline_active,
            config=cfg,
            use_smooth_evap=use_smooth_evap,
            use_eac_scaling=use_eac_scaling,
            stepped_policy=stepped_policy,
            policy_schedule=policy_schedule,
            pipeline_reliability_pct=pipeline_reliability_pct,
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
        dead_thresh = (getattr(cfg, "dead_storage_acft", 0.0) / cfg.total_capacity_acft * 100) if cfg.total_capacity_acft > 0 else 0.0
        day_dead = threshold_crossing_day(sim_df, initial_pct, dead_thresh) if dead_thresh > 0 else None
        day_zero = next((int(r["day"]) for _, r in sim_df.iterrows() if r.get("is_day_zero")), None)
        survived = bool(initial_pct * 100 > critical_thresh and unrounded_min > critical_thresh)

        # 180-Day Statutory Emergency Horizon (TAC Title 30 §290.41(b)(1))
        # Evaluates whether total active storage reaches zero / dead storage within 180 days
        depletion_day = day_zero if day_zero is not None else day_dead
        tac_180_day_breached = bool(depletion_day is not None and depletion_day <= 180)
        tac_180_warning_day = max(0, depletion_day - 180) if depletion_day is not None else None

        row = {
            "tier_multiplier": m,
            "tier_label": rainfall_tier_label(m),
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
            "day_dead_storage": day_dead,
            "day_zero": day_zero,
            "survived_critical_20pct": survived,
            "status": (f"Above {critical_thresh:g}% throughout window" if survived
                       else f"At or below {critical_thresh:g}% in window"),
            "tac_180_day_breached": tac_180_day_breached,
            "tac_180_warning_day": tac_180_warning_day,
            "tac_180_status": ("EMERGENCY (< 180d)" if tac_180_day_breached else (f"Depletion Day {depletion_day}" if depletion_day is not None else "Adequate (>180d)")),
            "total_served_domestic_acft": float(sim_df["served_domestic_acft"].sum()) if "served_domestic_acft" in sim_df else 0.0,
            "total_served_industrial_acft": float(sim_df["served_industrial_acft"].sum()) if "served_industrial_acft" in sim_df else 0.0,
            "total_served_wholesale_acft": float(sim_df["served_wholesale_acft"].sum()) if "served_wholesale_acft" in sim_df else 0.0,
            "total_served_outdoor_acft": float(sim_df["served_outdoor_acft"].sum()) if "served_outdoor_acft" in sim_df else 0.0,
            "mean_surface_area_acres": float(sim_df["surface_area_acres"].mean()) if "surface_area_acres" in sim_df else 0.0,
            "mean_eac_scale": float(sim_df["eac_scale"].mean()) if "eac_scale" in sim_df else 1.0,
            "stepped_policy_active": bool(stepped_policy or getattr(cfg, "stepped_policy_active", False)),
            "pipeline_reliability_pct": float(pipeline_reliability_pct) if pipeline_reliability_pct is not None else (1.0 if pipeline_active else 0.0),
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
        "stepped_policy": bool(stepped_policy or getattr(cfg, "stepped_policy_active", False)),
        "pipeline_reliability_pct": pipeline_reliability_pct,
    }


def build_shortlist_scorecard(
    workspace: Any,
    simulation_results_by_scenario: dict[str, pd.DataFrame] | None = None,
    config: WaterSystemConfig | None = None,
    initial_pct: float = 0.48,
    conservation_pct: float = 0.0,
    pipeline_active: bool = True,
    unit: str = "us",
) -> pd.DataFrame:
    """Generate a comprehensive multi-criteria comparison matrix across all shortlisted scenarios."""
    if not workspace or not getattr(workspace, "selected", None):
        return pd.DataFrame()

    cfg = config if config is not None else getattr(workspace, "water_system_config", None) or REGION_N_PRESET
    is_us = unit.lower() in ("us", "in", "ac-ft")
    scale = 1.0 / 25.4 if is_us else 1.0
    u_label = "in" if is_us else "mm"

    rows = []
    sims = simulation_results_by_scenario or {}

    for s_id in workspace.selected:
        s = workspace.get(s_id)
        f = s.features

        if s_id in sims:
            sim_df = sims[s_id]
        else:
            try:
                sim_df = simulate_reservoir_drawdown(
                    s.series,
                    initial_pct=initial_pct,
                    conservation_pct=conservation_pct,
                    pipeline_active=pipeline_active,
                    config=cfg,
                )
            except Exception:
                sim_df = None

        deficit_val = f["deficit_mm"] * scale
        duration_days = f["duration_days"]
        rate_val = (deficit_val / (duration_days / 30.4375)) if duration_days > 0 else 0.0

        day_st2 = "None"
        day_st3 = "None"
        end_storage = "N/A"
        min_storage = "N/A"

        if sim_df is not None and not sim_df.empty:
            b2_day = threshold_crossing_day(sim_df, initial_pct, cfg.stage_bands_pct[1] * 100 if len(cfg.stage_bands_pct) >= 2 else 30.0)
            b3_day = threshold_crossing_day(sim_df, initial_pct, cfg.stage_bands_pct[2] * 100 if len(cfg.stage_bands_pct) >= 3 else 20.0)
            day_st2 = f"Day {b2_day}" if b2_day is not None else "None"
            day_st3 = f"Day {b3_day}" if b3_day is not None else "None"
            end_pct = float(sim_df.iloc[-1]["combined_pct"])
            min_pct = float(sim_df["combined_pct"].min())
            end_storage = f"{end_pct:.1f}%"
            min_storage = f"{min_pct:.1f}%"

        start_date = s.provenance.get("source_start", "N/A")
        end_date = s.provenance.get("source_end", "N/A")
        hist_window = f"{start_date} to {end_date}"

        status_text = {
            "accepted": "Included",
            "rejected": "Excluded",
            "unreviewed": "Needs review",
        }.get(s.status, s.status)

        rows.append({
            "Scenario ID": s.id,
            "Historical Window": hist_window,
            "Duration (days)": duration_days,
            f"Total Deficit ({u_label})": round(deficit_val, 2 if is_us else 1),
            f"Deficit Rate ({u_label}/mo)": round(rate_val, 2 if is_us else 1),
            "Station Concurrence": f"{f['concurrence'] * 100:.0f}%",
            "Historical Rarity": f"{f['historical_percentile'] * 100:.0f}%",
            "Stage 2 (30%) Breach": day_st2,
            "Stage 3 (20%) Breach": day_st3,
            "Min Storage": min_storage,
            "End Storage": end_storage,
            "Ranking Score": round(float(s.score), 2),
            "Status": status_text,
        })

    return pd.DataFrame(rows)


def compare_demand_curtailment_policies(
    series: pd.DataFrame,
    initial_pct: float = 0.48,
    conservation_pct: float = 0.0,
    pipeline_active: bool = True,
    config: WaterSystemConfig | None = None,
    stepped_policy: bool = False,
    policy_schedule: dict[int, float] | None = None,
    pipeline_reliability_pct: float | None = None,
) -> dict[str, object]:
    """Compare configured sector curtailment against no sector-specific curtailment.

    Holding rainfall, starting storage, pipeline availability, aggregate demand reduction,
    capacities, inflow assumptions, evaporation assumptions, and stage thresholds constant,
    this runs two simulations differing only in whether sector-specific stage curtailment is active.

    Returns structured results, threshold crossings, and deltas without hardcoding dates,
    savings, or policy benefits.
    """
    cfg = config if config is not None else REGION_N_PRESET
    cfg.validate()

    if cfg.stage_curtailment_active:
        cfg_configured = cfg
        cfg_flat = replace(cfg, stage_curtailment_active=False)
    elif len(cfg.stage_bands_pct) >= 4:
        cfg_configured = replace(cfg, stage_curtailment_active=True)
        cfg_flat = cfg
    else:
        cfg_configured = cfg
        cfg_flat = cfg

    sim_kwargs = {
        "series": series,
        "initial_pct": initial_pct,
        "conservation_pct": conservation_pct,
        "pipeline_active": pipeline_active,
        "stepped_policy": stepped_policy,
        "policy_schedule": policy_schedule,
        "pipeline_reliability_pct": pipeline_reliability_pct,
    }

    df_configured = simulate_reservoir_drawdown(**sim_kwargs, config=cfg_configured)
    df_flat = simulate_reservoir_drawdown(**sim_kwargs, config=cfg_flat)

    # 1. Configured critical band crossing
    bands = cfg.stage_bands_pct
    band_crit_pct = (bands[2] if len(bands) >= 3 else 0.20) * 100
    day_crit_configured = threshold_crossing_day(df_configured, initial_pct, band_crit_pct)
    day_crit_flat = threshold_crossing_day(df_flat, initial_pct, band_crit_pct)
    day_crit_delta = (day_crit_configured - day_crit_flat) if (day_crit_configured is not None and day_crit_flat is not None) else None

    # 2. Day active-storage limit reached (is_day_zero)
    day_active_configured = int(df_configured.loc[df_configured["is_day_zero"], "day"].iloc[0]) if df_configured["is_day_zero"].any() else None
    day_active_flat = int(df_flat.loc[df_flat["is_day_zero"], "day"].iloc[0]) if df_flat["is_day_zero"].any() else None
    day_active_delta = (day_active_configured - day_active_flat) if (day_active_configured is not None and day_active_flat is not None) else None

    # 3. Total unmet modeled demand
    unmet_configured = float(df_configured["unmet_demand_acft"].sum())
    unmet_flat = float(df_flat["unmet_demand_acft"].sum())
    unmet_delta = unmet_configured - unmet_flat

    # 4. Domestic and industrial curtailed volume
    curt_dom_configured = float(df_configured["curtailed_domestic_acft"].sum())
    curt_ind_configured = float(df_configured["curtailed_industrial_acft"].sum())
    curt_dom_flat = float(df_flat["curtailed_domestic_acft"].sum())
    curt_ind_flat = float(df_flat["curtailed_industrial_acft"].sum())
    curt_dom_delta = curt_dom_configured - curt_dom_flat
    curt_ind_delta = curt_ind_configured - curt_ind_flat

    boundary_statement = (
        "This comparison is an illustrative numerical experiment using configured shares "
        "and is not an adopted allocation or forecast."
    )

    return {
        "configured_label": "Configured sector schedule",
        "flat_label": "No sector-specific curtailment",
        "configured_config": cfg_configured,
        "flat_config": cfg_flat,
        "df_configured": df_configured,
        "df_flat": df_flat,
        "crit_band_pct": band_crit_pct,
        "crit_day_configured": day_crit_configured,
        "crit_day_flat": day_crit_flat,
        "crit_day_delta": day_crit_delta,
        "active_limit_day_configured": day_active_configured,
        "active_limit_day_flat": day_active_flat,
        "active_limit_day_delta": day_active_delta,
        "unmet_demand_configured_acft": unmet_configured,
        "unmet_demand_flat_acft": unmet_flat,
        "unmet_demand_delta_acft": unmet_delta,
        "curtailed_domestic_configured_acft": curt_dom_configured,
        "curtailed_domestic_flat_acft": curt_dom_flat,
        "curtailed_domestic_delta_acft": curt_dom_delta,
        "curtailed_industrial_configured_acft": curt_ind_configured,
        "curtailed_industrial_flat_acft": curt_ind_flat,
        "curtailed_industrial_delta_acft": curt_ind_delta,
        "boundary_statement": boundary_statement,
    }



