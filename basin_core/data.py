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
        if hashlib.sha256(self.raw).hexdigest() != self.manifest["sha256"]:
            raise ValueError("Snapshot checksum mismatch. Restore the bundled data or refresh it explicitly.")
        frame = pd.read_csv(io.BytesIO(self.raw), parse_dates=["date"])
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
