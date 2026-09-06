from __future__ import annotations

import hashlib
import io
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


class CachedSource:
    """Verified immutable snapshot; missing values remain missing."""

    def __init__(self, directory: Path = ROOT / "data", raw: bytes | None = None, manifest: dict | None = None):
        self.raw = raw if raw is not None else (directory / "observations.csv").read_bytes()
        self.manifest = manifest if manifest is not None else json.loads((directory / "manifest.json").read_text())
        if not isinstance(self.manifest, dict) or self.manifest.get("schema_version") != "1.0" or any(k not in self.manifest for k in ("sha256", "start", "end", "stations")):
            raise ValueError("Snapshot manifest is missing required fields or uses an unsupported schema")
        if hashlib.sha256(self.raw).hexdigest() != self.manifest["sha256"]:
            raise ValueError("Snapshot checksum mismatch. Restore the bundled data or refresh it explicitly.")
        frame = pd.read_csv(io.BytesIO(self.raw), parse_dates=["date"])
        if not {"date", "station_id", "precip_mm"} <= set(frame.columns):
            raise ValueError("Snapshot is missing date, station_id or precip_mm columns")
        if not pd.api.types.is_datetime64_any_dtype(frame.date) or frame.date.isna().any():
            raise ValueError("Snapshot dates must be valid daily dates")
        station_ids = [s["id"] for s in self.manifest["stations"]]
        if not station_ids or len(station_ids) != len(set(station_ids)) or set(frame.station_id) != set(station_ids):
            raise ValueError("Snapshot stations do not match the manifest registry")
        if not frame.date.between(pd.Timestamp(self.manifest["start"]), pd.Timestamp(self.manifest["end"])).all():
            raise ValueError("Snapshot dates are outside the declared period")
        try:
            frame["precip_mm"] = pd.to_numeric(frame.precip_mm, errors="raise")
        except (ValueError, TypeError) as error:
            raise ValueError("Snapshot precipitation must be numeric") from error
        if frame.duplicated(["date", "station_id"]).any():
            raise ValueError("Duplicate station dates in snapshot")
        values = frame.precip_mm.dropna().to_numpy()
        if not np.isfinite(values).all() or (values < 0).any():
            raise ValueError("Invalid precipitation in snapshot")
        self.daily = frame.pivot(index="date", columns="station_id", values="precip_mm").reindex(
            pd.date_range(self.manifest["start"], self.manifest["end"], freq="D"))
        self.daily.index.name = "date"

    def select(self, stations: list[str]) -> pd.DataFrame:
        if not stations or len(set(stations)) != len(stations) or not set(stations) <= set(self.daily.columns):
            raise ValueError("Choose at least one distinct station from the snapshot")
        return self.daily[stations].copy()
