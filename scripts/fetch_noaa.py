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

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
BASE = "https://www.ncei.noaa.gov/pub/data/ghcn/daily/"
# Regional network: official first-order + cooperative stations around the
# Corpus Christi footprint and neighboring communities.
REGIONAL_STATIONS = [
    "USW00012924", "USW00012926", "USC00412011", "USC00416739",
    "USW00012912",
    "USW00012921",
    "USW00012928", "USC00414810",
    "USC00417704", "USW00012972",
    "USW00012932",
]
# Watershed network: NOAA cooperative gauges inside the Nueces / Frio /
# Atascosa drainage basins that feed Choke Canyon Reservoir and Lake Corpus
# Christi, from headwaters to the reservoir pools.
WATERSHED_STATIONS = [
    "USC00415113",  # Leakey — Nueces headwaters
    "USC00411398",  # Camp Wood — Nueces headwaters
    "USC00414254",  # Hondo — Hondo Creek (Nueces tributary)
    "USC00412160",  # Crystal City — upper Nueces (Winter Garden)
    "USC00411486",  # Carrizo Springs 3S — upper Nueces (Winter Garden)
    "USC00416879",  # Pearsall — Frio River
    "USC00411720",  # Choke Canyon Dam — Frio at Choke Canyon Reservoir
    "USC00417111",  # Pleasanton — Atascosa River
    "USC00419007",  # Three Rivers 9 NE — Frio/Nueces confluence
    "USC00415661",  # Mathis 4 SSW — Nueces at Lake Corpus Christi
]
IDS = REGIONAL_STATIONS + WATERSHED_STATIONS

CITY_BY_ID = {
    "USW00012924": "Corpus Christi", "USW00012926": "Corpus Christi",
    "USC00412011": "Corpus Christi", "USC00416739": "Corpus Christi",
    "USW00012912": "Victoria", "USW00012921": "San Antonio",
    "USW00012928": "Kingsville", "USC00414810": "Kingsville",
    "USC00417704": "Rockport / Aransas", "USW00012972": "Rockport / Aransas",
    "USW00012932": "Alice",
    "USC00415113": "Leakey", "USC00411398": "Camp Wood",
    "USC00414254": "Hondo", "USC00412160": "Crystal City",
    "USC00411486": "Carrizo Springs", "USC00416879": "Pearsall",
    "USC00411720": "Choke Canyon Dam", "USC00417111": "Pleasanton",
    "USC00419007": "Three Rivers", "USC00415661": "Mathis",
}

# Ordered sources used only when the target station has no valid daily value.
# The first source is the same-city index where one exists; the complete Corpus
# Christi airport series is the final regional proxy. Every substitution is
# recorded in the output instead of being flattened into an apparent observation.
# Watershed gauges fill from declared watershed chains (Choke Canyon Dam and
# Mathis as the two full-window reservoir-pool stations); coastal proxies are
# never substituted into watershed gauges.
FILL_SOURCES = {
    "USW00012926": ("USW00012924",),
    "USC00412011": ("USW00012924",),
    "USC00416739": ("USW00012924",),
    "USW00012912": ("USW00012924",),
    "USW00012921": ("USW00012924",),
    "USW00012928": ("USW00012924",),
    "USC00414810": ("USW00012928", "USW00012924"),
    "USC00417704": ("USW00012924",),
    "USW00012972": ("USC00417704", "USW00012924"),
    "USW00012932": ("USW00012924",),
    # --- Watershed chains (headwaters -> reservoir pools) ---
    "USC00415113": ("USC00411398", "USC00414254", "USC00411720", "USC00415661"),
    "USC00411398": ("USC00415113", "USC00414254", "USC00411720", "USC00415661"),
    "USC00414254": ("USC00415113", "USC00411398", "USC00411720", "USC00415661"),
    "USC00412160": ("USC00411486", "USC00411720", "USC00415661"),
    "USC00411486": ("USC00412160", "USC00411720", "USC00415661"),
    "USC00416879": ("USC00411720", "USC00415661", "USC00414254", "USC00411486"),
    "USC00411720": ("USC00415661", "USC00419007", "USC00414254", "USC00411486"),
    "USC00417111": ("USC00419007", "USC00411720", "USC00415661", "USC00414254", "USC00411486"),
    "USC00419007": ("USC00411720", "USC00415661", "USC00414254", "USC00411486"),
    "USC00415661": ("USC00411720", "USC00419007", "USC00414254", "USC00411486"),
}


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


def build_analysis_snapshot(frames: list[pd.DataFrame]) -> tuple[pd.DataFrame, list[dict]]:
    """Build the complete screening matrix while preserving value-level lineage."""
    dates = pd.date_range("1991-01-01", "2025-12-31", name="date")
    raw = pd.concat(frames, ignore_index=True)
    raw["date"] = pd.to_datetime(raw["date"])
    raw = raw.set_index(["date", "station_id"]).reindex(
        pd.MultiIndex.from_product([dates, IDS], names=["date", "station_id"])
    ).reset_index()
    raw["excluded"] = raw["excluded"].fillna(True).astype(bool)
    for flag in ("mflag", "qflag", "sflag"):
        raw[flag] = raw[flag].fillna("")

    observed = raw.pivot(index="date", columns="station_id", values="precip_mm").reindex(columns=IDS)
    output = []
    quality = []
    expected = len(dates)
    for station in IDS:
        station_rows = raw.loc[raw.station_id.eq(station)].copy().set_index("date")
        raw_values = observed[station]
        analysis_values = raw_values.copy()
        fill_source = pd.Series("", index=dates, dtype="object")
        for source_station in FILL_SOURCES.get(station, ()):
            needs_value = analysis_values.isna() & observed[source_station].notna()
            analysis_values.loc[needs_value] = observed.loc[needs_value, source_station]
            fill_source.loc[needs_value] = source_station
        if analysis_values.isna().any():
            raise ValueError(f"No declared fill source covers every missing day for {station}")

        station_rows["raw_precip_mm"] = raw_values
        station_rows["precip_mm"] = analysis_values
        station_rows["value_origin"] = np.where(raw_values.notna(), "observed", "filled")
        station_rows["fill_source_station_id"] = fill_source
        output.append(station_rows.reset_index())

        observed_days = int(raw_values.notna().sum())
        filled_days = expected - observed_days
        quality.append({
            "station_id": station,
            "city": CITY_BY_ID[station],
            "expected_days": expected,
            "raw_observed_days": observed_days,
            "raw_completeness_pct": round(observed_days / expected * 100, 3),
            "filled_days": filled_days,
            "analysis_coverage_days": int(analysis_values.notna().sum()),
            "analysis_coverage_pct": round(analysis_values.notna().mean() * 100, 3),
            # Backward-compatible fields for saved packets and report readers.
            "valid_days": int(analysis_values.notna().sum()),
            "completeness_pct": round(analysis_values.notna().mean() * 100, 3),
            "missing_or_excluded_days": int(analysis_values.isna().sum()),
            "trace_days": int(station_rows.mflag.eq("T").sum()),
        })

    columns = ["date", "station_id", "precip_mm", "raw_precip_mm", "value_origin",
               "fill_source_station_id", "mflag", "qflag", "sflag", "excluded"]
    return pd.concat(output, ignore_index=True)[columns].sort_values(["date", "station_id"]), quality


def main():
    with ThreadPoolExecutor(max_workers=4) as pool:
        payloads = list(pool.map(download, ["ghcnd-stations.txt", "ghcnd-version.txt"] + [f"all/{s}.dly" for s in IDS]))
    metadata = payloads[0].decode("utf-8")
    registry = []
    for station in IDS:
        line = next(line for line in metadata.splitlines() if line[:11] == station)
        role = (
            "Watershed rainfall gauge within the Nueces/Frio/Atascosa drainage basins; "
            "gauge-level observations, not calibrated catchment rainfall"
            if station in WATERSHED_STATIONS
            else "Provisional regional station proxy; catchment representativeness unvalidated"
        )
        registry.append({"id": station, "name": line[41:71].strip(), "city": CITY_BY_ID[station],
                         "latitude": float(line[12:20]),
                         "longitude": float(line[21:30]), "elevation_m": float(line[31:37]),
                         "role": role,
                         "catchment": None, "source": BASE + f"all/{station}.dly"})
    frames = [parse_dly(raw, station) for station, raw in zip(IDS, payloads[2:])]
    frame, quality = build_analysis_snapshot(frames)
    raw_csv = frame.to_csv(index=False, lineterminator="\n").encode()
    manifest = {"schema_version": "1.0", "source": "NOAA NCEI GHCN-Daily", "dataset_version": payloads[1].decode().strip(),
                "downloaded_at": datetime.now(timezone.utc).isoformat(), "start": "1991-01-01", "end": "2025-12-31",
                "sha256": hashlib.sha256(raw_csv).hexdigest(), "stations": registry, "quality": quality,
                "raw_sha256": {s: hashlib.sha256(r).hexdigest() for s, r in zip(IDS, payloads[2:])},
                "lineage_columns": ["raw_precip_mm", "value_origin", "fill_source_station_id"],
                "policy": "PRCP only; tenths mm / 10; missing/negative, nonblank QFLAG, MFLAG P excluded; trace = 0. Regional station-days use the declared same-city index where available, then Corpus Christi airport as a provisional regional proxy. Watershed gauges (Leakey, Camp Wood, Hondo, Crystal City, Carrizo Springs, Pearsall, Choke Canyon Dam, Pleasanton, Three Rivers 9 NE, Mathis 4 SSW) cover the Nueces/Frio/Atascosa drainage basins; their missing days fill only from declared watershed chains ending at the full-window reservoir-pool gauges (Choke Canyon Dam, Mathis) - coastal proxies are never substituted into watershed gauges. raw_precip_mm, value_origin and fill_source_station_id preserve every substitution. MDPR is never used.",
                "documentation": BASE + "readme.txt"}
    target = ROOT / "data"
    target.mkdir(exist_ok=True)
    (target / "observations.csv").write_bytes(raw_csv)
    (target / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
