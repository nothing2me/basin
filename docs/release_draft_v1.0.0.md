# BASIN v1.0.0 — GitHub Release Draft

> Draft for the Zoho "From The Ground Up" 2026 finalist showcase (Sept 22, 2026).
> **Action needed before publishing:** rebuild `Setup-BASIN.exe` from current `main`
> (the 9/16 build predates the data refresh, basemap swap and PDF TOC work), re-run
> the full offline suite on the target laptop, then update the SHA-256 here and in
> `docs/index.html` line 865 if the installer changes.

## Release metadata

- **Tag:** `v1.0.0`
- **Target commit:** current `main` tip (create tag after the final rebuild)
- **Title:** `BASIN v1.0.0 — Offline Rainfall-Scenario Screening & Expert Handoff`

## Release notes (paste into GitHub)

```
BASIN: Basin Analysis & Scenario Intelligence Navigator
100% on-device drought scenario screening for regional water authorities,
municipalities, and river basins — built for the Zoho "From The Ground Up"
AI Hackathon 2026 (TAMU-CC · Noah Wilborn, Mohammed Asad Khan, Misha Stegall).

WHAT IT DOES
BASIN turns 35 years of public NOAA precipitation observations into a
transparent rainfall-scenario shortlist and a replay-verified handoff bundle.
Replay verification checks the ZIP's declared files and calculations for
internal consistency; it does not validate hydrology or source suitability.
It is a pre-engineering screening layer — it does not replace statutory models
(WAM, HEC-ResSim), a hydrologist, or an official water-supply model.

INSTALL (Windows 10/11 64-bit)
1. Download Setup-BASIN.exe (~200 MB) — installs to your user folder, zero
   administrator privileges, fully offline.
2. Optional: during setup, check the box (or run "Download AI Model.cmd" later)
   to fetch the Qwen 2.5 3B model (~2.1 GB) for conversational tool dispatch.
   Core BASIN works 100% offline without it.

HIGHLIGHTS
- Synchronized multi-station historical-window resampling (PCG64, deterministic)
- Multi-factor rainfall clustering: five shared features plus one normalized
  station-deficit feature per selected station (K-Means k=6)
- Mass-conserving multi-reservoir drawdown simulation (|error| < 10^-6 ac-ft)
- 13 deterministic read-only assistant tools — grounded, no invented numbers
- Cryptographic replayable export bundle (SHA-256 manifest + independent verify)
- Companion Executive Technical Brief PDF (generated locally, stamped as outside
  the bundle verification contract)
- 0 KB network egress in core operation; optional model download only at install

VERIFY
PowerShell:  Get-FileHash Setup-BASIN.exe -Algorithm SHA256
Expected:    4E0212F5D26C86F7EB6AC1E93C2A14C0B7A901ADBE6484D892D318956CA51D8E
             (UPDATE AFTER REBUILD)

DATA & LICENSES
- Data: NOAA NCEI GHCN-Daily (public domain), TWDB / TCEQ public planning data
- Basemap: Sentinel-2 cloudless by EOX IT Services GmbH (CC BY 4.0)
- Optional model: Qwen2.5-3B-Instruct (Qwen Research License, SHA-256 pinned)
- Code: MIT License

DISCLAIMER
BASIN is an agile exploratory screening workbench, not a certified water
availability model or sealed engineering report. Formal determinations require
evaluation by a licensed Professional Engineer.
```

## Assets to attach

| Asset | Size | SHA-256 |
|---|---|---|
| `Setup-BASIN.exe` | 200.1 MB | `4E0212F5D26C86F7EB6AC1E93C2A14C0B7A901ADBE6484D892D318956CA51D8E` (re-verify after rebuild) |
| `BASIN.exe` | 14.2 MB | `E6AF49A892E13F4A492E57B658AFEBFA7C2EF6C46A0E488B451B897115D32997` (re-verify after rebuild) |
| `BASIN-demo-source.zip` | 2.6 MB | from `scripts/package_demo.py` (regenerate from final `main`) |
| `BASIN-rehearsal.zip` | 0.7 MB | replay-verified example within the ZIP's declared scope (regenerate via `scripts/demo_smoke.py` + `scripts/replay_bundle.py`) |
| `wheelhouse/` (49 wheels, zipped) | ~155 MB | optional offline-install dependency cache |

## Publish steps

1. Rebuild installer from final `main` (`python scripts/package_setup_exe.py`)
2. Re-verify SHA-256; update this file + `docs/index.html` `shaText` if changed
3. `git push origin main`
4. `git tag -a v1.0.0 -m "BASIN v1.0.0"` + `git push origin v1.0.0`
5. GitHub → Releases → "Draft a new release" → select `v1.0.0` → paste notes → attach assets
6. Create as **draft first**, final sanity check on a clean laptop, then publish
