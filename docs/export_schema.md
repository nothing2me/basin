# BASIN Export Package & Interoperability Schema

This specification describes the open data formats, file structures, schemas, and units contained in every verified BASIN export package (`BASIN-[id].zip`) and companion report.

Any external system — including regional water planning models (e.g. Texas WAM Run 3, HEC-ResSim, HEC-HMS), agricultural decision tools, farm spreadsheets, or GIS software — can consume BASIN's outputs directly using these specifications.

---

## 1. Package File Inventory

A verified export package is a standard ZIP archive containing:

```
BASIN-[id].zip
├── daily_rainfall.csv           # Clean tabular scenario precipitation
├── shortlist.csv                # Candidate metadata, ranking scores & features
├── audit.json                   # Cryptographic provenance & decision log
├── manifest.json                # Bundled NOAA GHCN-Daily source snapshot
├── methodology.md               # Scientific algorithms, thresholds & policies
├── SHA256SUMS.txt               # Per-file cryptographic checksums
└── Hydrologist_Handoff_Brief.md # Human-readable technical brief
```

---

## 2. Daily Rainfall Series (`daily_rainfall.csv`)

### Format & Conventions
- **Format**: Standard RFC 4180 CSV
- **Index Column**: `date` (ISO 8601: `YYYY-MM-DD`), unique, sorted chronologically
- **Data Columns**: One column per NOAA station ID (e.g., `USW00012924`)
- **Units**: Precipitation in **millimeters per day (mm/day)**
- **Precision**: Floating-point values (`%.12g`), non-negative, finite, no null/missing values

### Example
```csv
date,USW00012924,USW00012912,USW00012921
2011-06-01,0.0,0.0,0.0
2011-06-02,0.0,0.0,1.2
2011-06-03,4.5,0.0,0.0
```

### Interoperability Notes
- **Texas WAM Run 3 / HEC-HMS / HEC-ResSim**: To convert mm/day to inches/day for standard hydrologic models, multiply values by `0.0393701` (or divide by `25.4`).
- **Unit conversions**:
  - `1 mm = 0.03937 inches`
  - `1 inch = 25.4 mm`
  - `1 mm depth over 1 acre = 0.0032585 ac-ft`

---

## 3. Shortlist Metadata Table (`shortlist.csv`)

### Columns & Definitions

| Column | Type | Unit | Description |
|---|---|---|---|
| `ID` | string | — | Scenario identifier (e.g., `B-042`) |
| `Days` | integer | days | Total duration of the window (30 to 365) |
| `Onset` | string | — | Onset month name (e.g., `Apr`, `Jul`) |
| `Deficit mm` | float | mm | Equal-station arithmetic mean precipitation deficit against 1991–2020 monthly normal |
| `Stations stressed together %` | float | % | Concurrence: % of rolling 30-day windows where all monitored stations simultaneously exceed their 75th percentile deficit |
| `Score` | float | 0–100 | Weighted priority score reflecting user-configured community preferences |
| `Group` | string | — | Unsupervised cluster assignment (K-Means k=6) |
| `Profile` | string | — | Semantic cluster profile label (e.g., `Concurrent Stations`, `Peak Summer`) |
| `Status` | string | — | Human review status (`accepted`, `rejected`, `unreviewed`) |
| `Revision` | integer | — | Revision sequence number (incremented on any data edit) |

---

## 4. Audit & Provenance Trail (`audit.json`)

### Structure & Replay Verification
`audit.json` contains complete machine-verifiable provenance for mathematical replay:

- `schema_version`: e.g. `"2.0"` or `"2.1"`
- `workspace_id`: 12-character unique identifier
- `params`: Resampling parameters (stations, durations, onset months, retention range, seed, extent)
- `scenarios`: Full candidate audit array:
  - `id`: Scenario identifier
  - `series_sha256`: SHA-256 hash of the normalized daily rainfall CSV
  - `features`: Computed statistical metrics (percentiles, benchmarks, concurrence)
  - `score`: Ranking score and constituent component scores
  - `history`: Sequence of human review decisions, edit actions, and revision digests
- `evidence`: Public evidence records attached to this analysis
- `conflicts`: Documented disagreements and resolutions
- `footprint`: Machine resource measurements (wall time, CPU seconds, memory RSS, estimated energy range)

---

## 5. Companion Documents

- **`Hydrologist_Handoff_Brief.md`**: Clean Markdown executive brief structured for consulting engineers and regional water boards.
- **`BASIN-Executive-Brief-[id].pdf`**: Companion publication-grade executive briefing for council members and decision-makers, featuring bottom-line summaries, storage trajectories, and breach risk matrices.
