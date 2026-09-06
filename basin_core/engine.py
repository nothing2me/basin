from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import hashlib
import json

import numpy as np
import pandas as pd

from basin_core.data import CachedSource


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True)
class ScenarioParams:
    stations: tuple[str, ...]
    durations: tuple[int, ...] = (90, 180, 270)
    months: tuple[int, ...] = (1, 4, 7, 10)
    retention_min: float = 0.35
    retention_max: float = 0.85
    extent: str = "All stations"
    candidates: int = 300
    seed: int = 22

    def validate(self):
        if not self.stations or len(set(self.stations)) != len(self.stations):
            raise ValueError("Select distinct stations")
        if not self.durations or any(type(d) is not int or not 30 <= d <= 365 for d in self.durations):
            raise ValueError("Duration must be 30–365 days")
        if not self.months or any(type(m) is not int or not 1 <= m <= 12 for m in self.months):
            raise ValueError("Select onset months from 1–12")
        if not 0 <= self.retention_min <= self.retention_max <= 1:
            raise ValueError("Rainfall retained must be between 0 and 100%")
        if self.extent not in ("All stations", "One station", "Mixed"):
            raise ValueError("Unknown spatial stress pattern")
        if type(self.candidates) is not int or not 10 <= self.candidates <= 1000 or type(self.seed) is not int or not 0 <= self.seed < 2**32:
            raise ValueError("Use 10–1000 candidates and a seed from 0 to 4294967295")


class Reference:
    """Fixed historical references independent of the generated pool."""

    def __init__(self, source: CachedSource, stations: list[str]):
        self.stations = stations
        self.daily = source.select(stations)
        normal = self.daily.loc["1991":"2020"]
        counts = normal.groupby(normal.index.month).count()
        if len(counts) != 12 or (counts < 600).any().any():
            raise ValueError("Insufficient monthly observations for the 1991–2020 reference")
        self.climatology = normal.groupby(normal.index.month).mean()
        expected = self.expected(normal.index)
        rolls = pd.DataFrame(expected - normal.to_numpy(), index=normal.index).rolling(30, min_periods=30).sum()
        self.thresholds = rolls.quantile(0.75).to_numpy()
        self._windows: dict = {}

    def expected(self, dates: pd.DatetimeIndex) -> np.ndarray:
        return self.climatology.loc[dates.month].to_numpy()

    def windows(self, month: int, duration: int) -> list[dict]:
        key = (month, duration)
        if key not in self._windows:
            windows = []
            for year in range(1991, 2026):
                start = pd.Timestamp(year, month, 1)
                dates = pd.date_range(start, periods=duration)
                frame = self.daily.reindex(dates)
                if frame.isna().any().any():
                    continue
                values = frame.to_numpy()
                deficit = float(np.maximum((self.expected(dates) - values).sum(axis=0), 0).mean())
                windows.append({"start": str(start.date()), "end": str(dates[-1].date()),
                                "values": values, "deficit_mm": deficit})
            self._windows[key] = windows
        return self._windows[key]

    def features(self, series: pd.DataFrame) -> dict:
        if list(series.columns) != self.stations or not 30 <= len(series) <= 365:
            raise ValueError("Series must contain the selected stations and 30–365 daily rows")
        if not series.index.equals(pd.date_range(series.index[0], periods=len(series))):
            raise ValueError("Dates must be unique, sorted, and consecutive")
        values = series.to_numpy(dtype=float)
        if not np.isfinite(values).all() or (values < 0).any():
            raise ValueError("Rainfall must be finite, nonnegative, and complete")
        expected = self.expected(series.index)
        net = expected - values
        station_deficits = np.maximum(net.sum(axis=0), 0)
        deficit = float(station_deficits.mean())
        rolling = pd.DataFrame(net).rolling(30, min_periods=30).sum().to_numpy()[29:]
        concurrent = (rolling > self.thresholds).all(axis=1)
        runs = []
        for col in values.T:
            best = current = 0
            for dry in col < 1.0:
                current = current + 1 if dry else 0
                best = max(best, current)
            runs.append(best)
        # Equal-duration and equal-onset references, with identical station aggregation.
        historic = self.windows(int(series.index[0].month), len(series))
        benchmark = [w["deficit_mm"] for w in historic if w["end"] <= "2015-12-31"]
        if len(benchmark) < 5:
            raise ValueError("Fewer than five complete pre-2016 matched windows; choose different stations or timing")
        percentile = float(np.mean(np.asarray(benchmark) <= deficit))
        maximum = float(max(benchmark))
        return {"duration_days": len(series), "onset_month": int(series.index[0].month),
                "deficit_mm": deficit, "station_deficits_mm": dict(zip(self.stations, station_deficits.tolist())),
                "rainfall_mm": float(values.sum(axis=0).mean()), "expected_mm": float(expected.sum(axis=0).mean()),
                "concurrence": float(concurrent.mean()), "eligible_concurrence_days": len(concurrent),
                "max_dry_days": int(max(runs)), "historical_percentile": percentile,
                "benchmark_mm": maximum, "benchmark_n": len(benchmark),
                "beyond_rainfall_reference": deficit > maximum + 1e-9,
                "high_priority_season_fraction": float(np.isin(series.index.month, [6, 7, 8, 9]).mean())}


class Scenario:
    def __init__(self, identifier: str, series: pd.DataFrame, provenance: dict, reference: Reference):
        self.id = identifier
        self.series = series.copy()
        self.provenance = provenance
        self.revision = 1
        self.status = "unreviewed"
        self.approved_revision = None
        self.history: list[dict] = []
        self.features = reference.features(self.series)
        self.cluster = 0
        self.cluster_name = "Unassigned"
        self.score = 0.0
        self.components: dict = {}

    def digest(self) -> str:
        return hashlib.sha256(self.series.to_csv(float_format="%.12g", lineterminator="\n").encode()).hexdigest()

    def review(self, accept: bool, note: str = ""):
        if not accept and not note.strip():
            raise ValueError("Add a reason so the rejection can be understood later")
        self.status = "accepted" if accept else "rejected"
        self.approved_revision = self.revision if accept else None
        self.history.append({"action": self.status, "revision": self.revision, "at": utc_now(),
                             "series_sha256": self.digest(), "private_note": note})

    def edit(self, reference: Reference, note: str, factor: float | None = None, replacement: pd.DataFrame | None = None):
        if not note.strip():
            raise ValueError("Explain the revision before applying it")
        if (factor is None) == (replacement is None):
            raise ValueError("Provide exactly one edit operation")
        if factor is not None and (not np.isfinite(factor) or not 0 <= factor <= 2):
            raise ValueError("Edit multiplier must be between 0 and 2")
        updated = replacement.copy() if replacement is not None else self.series * factor
        # Replacement is the same experiment window; changing timing requires a new run.
        if not updated.index.equals(self.series.index) or list(updated.columns) != list(self.series.columns):
            raise ValueError("Replacement must retain the exact scenario dates and station columns")
        features = reference.features(updated)
        prior = self.digest()
        self.series, self.features = updated, features
        self.revision += 1
        self.status, self.approved_revision = "unreviewed", None
        self.history.append({"action": "replace" if replacement is not None else "scale", "factor": factor,
                             "revision": self.revision, "at": utc_now(), "previous_sha256": prior,
                             "series_sha256": self.digest(), "private_note": note,
                             "replacement_values": updated.to_numpy().tolist() if replacement is not None else None})

    def record(self, include_notes=False, include_series=False):
        history = [{k: v for k, v in event.items() if include_notes or k != "private_note"} for event in self.history]
        result = {"id": self.id, "revision": self.revision, "status": self.status,
                  "approved_revision": self.approved_revision, "features": self.features,
                  "cluster": self.cluster, "cluster_name": getattr(self, "cluster_name", f"Group {self.cluster}"),
                  "score": self.score, "components": self.components,
                  "provenance": self.provenance, "history": history, "series_sha256": self.digest()}
        if include_series:
            result["dates"] = self.series.index.strftime("%Y-%m-%d").tolist()
            result["stations"] = list(self.series.columns)
            result["values"] = self.series.to_numpy().tolist()
        return result


class ScenarioGenerator:
    def __init__(self, source: CachedSource, params: ScenarioParams):
        params.validate()
        self.params = params
        self.reference = Reference(source, list(params.stations))

    def generate(self) -> tuple[list[Scenario], dict]:
        p, ref = self.params, self.reference
        rng = np.random.default_rng(p.seed)
        eligible = {}
        unavailable = []
        for month in p.months:
            for duration in p.durations:
                windows = ref.windows(month, duration)
                if len([w for w in windows if w["end"] <= "2015-12-31"]) >= 5:
                    eligible[(month, duration)] = windows
                else:
                    unavailable.append({"month": month, "duration": duration, "reason": "Insufficient complete reference windows"})
        if not eligible:
            raise ValueError("No complete, season-matched windows for these settings")
        scenarios, seen = [], set()
        keys = list(eligible)
        attempts = 0
        while len(scenarios) < p.candidates and attempts < p.candidates * 20:
            attempts += 1
            month, duration = keys[int(rng.integers(len(keys)))]
            windows = eligible[(month, duration)]
            window = windows[int(rng.integers(len(windows)))]
            retention = float(rng.uniform(p.retention_min, p.retention_max))
            extent = p.extent if p.extent != "Mixed" else ["All stations", "One station"][int(rng.integers(2))]
            factors = np.ones(len(p.stations))
            if extent == "All stations":
                factors[:] = retention
            else:
                factors[int(rng.integers(len(factors)))] = retention
            # Whole-window synchronized resampling: never splice blocks or independently resample stations.
            dates = pd.date_range(window["start"], periods=duration)
            series = pd.DataFrame(window["values"] * factors, index=dates, columns=p.stations)
            key = hashlib.sha256(series.to_numpy().tobytes() + str(month).encode()).hexdigest()
            if key in seen:
                continue
            seen.add(key)
            provenance = {"method": "synchronized-season-matched-whole-window-v1",
                          "source_start": window["start"], "source_end": window["end"],
                          "source_window_days": duration, "retention_by_station": dict(zip(p.stations, factors.tolist())),
                          "requested_extent": p.extent, "constructed_extent": extent,
                          "kind": "historical resample" if np.all(factors == 1) else "constructed rainfall stress test",
                          "date_meaning": "Historical source dates used as scenario day labels; not a forecast"}
            scenarios.append(Scenario(f"B-{len(scenarios)+1:03}", series, provenance, ref))
        return scenarios, {"attempts": attempts, "duplicates_skipped": attempts - len(scenarios),
                           "unavailable_settings": unavailable, "actual_candidates": len(scenarios),
                           "eligible_windows": {f"month={m},days={d}": len(w) for (m, d), w in eligible.items()}}
