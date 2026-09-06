"""Explicit, ahead-of-time NOAA refresh. Never imported by the application."""
from __future__ import annotations

import calendar
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import io
import json
from pathlib import Path
import urllib.request

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
BASE = "https://www.ncei.noaa.gov/pub/data/ghcn/daily/"
IDS = ["USW00012924", "USW00012912", "USW00012921"]


def download(path):
    with urllib.request.urlopen(BASE + path, timeout=90) as response:
        return response.read()


def parse_dly(raw: bytes, station: str) -> pd.DataFrame:
    rows = []
    for line in raw.decode("ascii").splitlines():
        if line[17:21] != "PRCP" or not 1991 <= int(line[11:15]) <= 2025:
            continue
        if line[:11] != station or len(line) < 269:
            raise ValueError("Malformed NOAA record")
        year, month = int(line[11:15]), int(line[15:17])
        for day in range(1, calendar.monthrange(year, month)[1] + 1):
            cell = line[21 + (day - 1) * 8:29 + (day - 1) * 8]
            value, mflag, qflag, sflag = int(cell[:5]), cell[5].strip(), cell[6].strip(), cell[7].strip()
            # GHCN DLY PRCP is tenths of mm; P means missing presumed zero.
            # Reject P, nonblank QFLAG and missing/negative values. Trace stays zero.
            valid = value >= 0 and not qflag and mflag != "P"
            rows.append({"date": f"{year}-{month:02}-{day:02}", "station_id": station,
                         "precip_mm": value / 10 if valid else None,
                         "mflag": mflag, "qflag": qflag, "sflag": sflag,
                         "excluded": not valid})
    if not rows:
        raise ValueError(f"No precipitation observations for {station}")
    return pd.DataFrame(rows)


def main():
    with ThreadPoolExecutor(max_workers=4) as pool:
        payloads = list(pool.map(download, ["ghcnd-stations.txt", "ghcnd-version.txt"] + [f"all/{s}.dly" for s in IDS]))
    metadata = payloads[0].decode("utf-8")
    registry = []
    for station in IDS:
        line = next(line for line in metadata.splitlines() if line[:11] == station)
        registry.append({"id": station, "name": line[41:71].strip(), "latitude": float(line[12:20]),
                         "longitude": float(line[21:30]), "elevation_m": float(line[31:37]),
                         "role": "Provisional regional station proxy; catchment representativeness unvalidated",
                         "catchment": None, "source": BASE + f"all/{station}.dly"})
    frames = [parse_dly(raw, station) for station, raw in zip(IDS, payloads[2:])]
    frame = pd.concat(frames).sort_values(["date", "station_id"])
    raw_csv = frame.to_csv(index=False, lineterminator="\n").encode()
    quality = []
    expected = len(pd.date_range("1991-01-01", "2025-12-31"))
    for station, group in frame.groupby("station_id"):
        valid = int(group.precip_mm.notna().sum())
        quality.append({"station_id": station, "expected_days": expected, "valid_days": valid,
                        "missing_or_excluded_days": expected - valid,
                        "completeness_pct": round(valid / expected * 100, 3),
                        "trace_days": int(group.mflag.eq("T").sum())})
    manifest = {"schema_version": "1.0", "source": "NOAA NCEI GHCN-Daily", "dataset_version": payloads[1].decode().strip(),
                "downloaded_at": datetime.now(timezone.utc).isoformat(), "start": "1991-01-01", "end": "2025-12-31",
                "sha256": hashlib.sha256(raw_csv).hexdigest(), "stations": registry, "quality": quality,
                "raw_sha256": {s: hashlib.sha256(r).hexdigest() for s, r in zip(IDS, payloads[2:])},
                "policy": "PRCP only; tenths mm / 10; missing/negative, nonblank QFLAG, MFLAG P excluded; trace = 0; no imputation; MDPR never used. Complete simultaneous windows only.",
                "documentation": BASE + "readme.txt"}
    target = ROOT / "data"
    target.mkdir(exist_ok=True)
    (target / "observations.csv").write_bytes(raw_csv)
    (target / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
