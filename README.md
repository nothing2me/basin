# BASIN

**Basin Analysis and Scenario Intelligence Navigator** — a local rainfall-scenario workbench for the Coastal Bend / Region N project, built for From the Ground Up 2026.

Generate hundreds of stress tests from NOAA observations, group patterns with local KMeans, choose community priorities, review/edit/reject candidates, and export an auditable shortlist for professional hydrologic review.

**Research prototype:** bundled airport stations are provisional regional proxies. Catchment representativeness, scientific assumptions and user benefit still require practitioner validation. BASIN does not forecast water supply, reservoir levels, restriction dates, drought probability or the hydrologic drought of record.

## Start on Windows

Requires Python 3.12 (64-bit). Double-click **Setup BASIN.cmd** once, then **Start BASIN.cmd**. Setup uses bundled wheels if wheelhouse/ exists; otherwise it needs internet. Open http://127.0.0.1:8501 and keep the console running. This checkout already has an installed environment.

```powershell
py -3.12 -m venv .venv
.venv/Scripts/python.exe -m pip install -r requirements.txt
.venv/Scripts/python.exe -m streamlit run app.py
```

macOS/Linux: create a Python 3.12 venv, install requirements, then `sh start_basin.sh`. The Windows wheel bundle does not install on those operating systems; their launch script is provided but was not tested here. Runtime needs no internet, API key, account or paid service after setup.

## Workflow

1. **Workspace:** run settings and ranking weights in the sidebar; scenario distribution, score contributions, searchable/filterable candidate grid, and shortlist selection. Select a table row to inspect a candidate.
2. **Review:** daily/cumulative rainfall and rolling deficits; direct daily-value editing, CSV replacement, scaling, accept/reject and candidate swaps. Edits recompute measurements/groups/scores and invalidate approval.
3. **Exports:** review every shortlisted item and accept at least one current revision. Build and replay-verify a CSV/JSON/snapshot ZIP. Free-text notes stay excluded unless explicitly opted in.
4. **Data:** station quality table, observed daily/monthly/annual rainfall, source records and downloadable methodology.

The interface contains operational controls and data. Pitch language, competition information, discovery findings and rehearsal guidance are kept in docs/.

Sessions and append-only review logs save in gitignored local/. Restore from the sidebar after a refresh. The server binds 127.0.0.1; LAN/multiuser access is not configured. Local files are not encrypted. Runtime telemetry, automatic data fetching and cloud inference are absent.

## Data and method

Real NOAA GHCN-Daily records for 1991–2025: USW00012924 (Corpus Christi), USW00012912 (Victoria), USW00012921 (San Antonio). Snapshot and flags are bundled. Missing or failed-quality values never become zero. Explicit ahead-of-time refresh: `python scripts/fetch_noaa.py`. Preserve old snapshots with old sessions; refreshed observations invalidate session compatibility.

Generation uses complete, synchronized, season-matched **whole historical windows**, correcting the design draft's unspecified block bootstrap. Retention scales rainfall, not hydrologic deficit. The rainfall reference uses the same stations, onset and duration among complete windows ending by 2015, with 1991–2020 climatology. It is not the model's drought of record. See [full methodology](docs/methodology.md).

## Verify and package

```powershell
.venv/Scripts/python.exe -m pytest -q
.venv/Scripts/python.exe scripts/demo_smoke.py
.venv/Scripts/python.exe scripts/replay_bundle.py output/BASIN-rehearsal.zip
python -m pip download --only-binary=:all: -r requirements.txt --dest wheelhouse
.venv/Scripts/python.exe scripts/package_demo.py --wheels
```

The rehearsal blocks network connections and exercises generation, a revision, approval, privacy-default export and replay. Packaging under output/ includes source, docs, verified observations and optional platform-specific wheels. It excludes notes, sessions, credentials and attachments. Python must be installed beforehand; the kit is not a standalone executable.

## Structure and handoff

basin_core/: data verification, generator/reference, learning/ranking, revision/persistence workflow, exporter/replayer. app.py: Streamlit/Plotly UI. scripts/: explicit refresh, offline rehearsal, replay, packaging. tests/: numerical/data invariants, privacy/review integrity, persistence, offline pipeline and UI workflow.

Read the [demo runbook](docs/demo_runbook.md), [validation status](docs/validation_notes.md), [AI disclosure](docs/ai_use_log.md) and [third-party materials](docs/third_party_materials.md).

Working software is not field validation. The team still needs practitioner review, actual-laptop/projector rehearsal, backup video and final pitch materials. No local chat agent or live utility integration is included.
