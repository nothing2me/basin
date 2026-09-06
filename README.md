# BASIN

**Basin Analysis and Scenario Intelligence Navigator** is a local rainfall evidence workbench for the Coastal Bend / Region N hackathon project.

Use public NOAA observations to construct rainfall stress scenarios, compare their measurements and priorities, challenge assumptions, and prepare a reviewed packet for deeper hydrologic analysis. Local KMeans groups candidates; the product has no LLM or cloud inference.

## Supported Windows presentation path

Use **Python 3.12, 64-bit** and the browser launcher. Extract the complete package, run **Setup BASIN.cmd** once, then **Start BASIN.cmd**. Setup installs the exact requirements from `wheelhouse/` when supplied, otherwise from the internet. After setup, the app and its coordinate overview work locally. Keep the console open; Ctrl+C stops the app.

The launcher starts at port 8501 and chooses another local port if needed. Its console prints the actual address. Runtime needs no API key or account. This release supports a browser on Windows; the old tracked `BASIN.exe` and native wrapper are legacy artifacts and are excluded from the current distribution. They have not been rebuilt or accepted for this release.

```powershell
py -3.12 -m venv .venv
.venv/Scripts/python.exe -m pip install -r requirements.txt
.venv/Scripts/python.exe scripts/start_browser.py
```

The offline Windows wheel bundle is specific to CPython 3.12 x64. Python itself must be installed beforehand. macOS/Linux require their own dependency installation and validation; `start_basin.sh` is provided without a presentation-support claim.

## Analyst workflow

1. **Data:** inspect provisional stations, completeness, flags, observation history and the snapshot manifest.
2. **Workspace:** generate complete historical rainfall windows with declared retention factors. Inspect groups and score contributions, compare two or three candidates, and preview alternative priorities on the same pool. Ranking changes preserve your shortlist until an explicit rebuild or swap.
3. **Review:** trace a metric to its evidence, compare two cited records, record a public disagreement and human disposition, and leave unresolved issues visible. Add cited records to a scenario. Private annotations stay local by default.
4. **Review rainfall:** edit daily values, apply a multiplier or replace the same dates/stations from CSV. Edits recompute metrics and clear acceptance. Accept or reject each shortlisted revision; rejection requires a reason. Acceptance is a local content decision, not professional certification.
5. **Exports:** inspect included evidence and unresolved issues, choose whether to include private notes, and build a packet. Replay verifies its declared internal-consistency checks before download.

The optional **Reservoir simulation** view is an uncalibrated, illustrative experiment. All material assumptions are shown. It tracks actual served losses, unmet demand and spill. Its settings, results and conditional storage bands are excluded from saved evidence packets and their verification. It does not predict reservoir levels, deliveries, safe yield or official restriction dates.

## Data, limits and privacy

The bundled NOAA GHCN-Daily snapshot covers 1991–2025 at Corpus Christi, Victoria and San Antonio airport stations. These are provisional regional proxies, not validated catchment rainfall. Whole-window sampling preserves complete simultaneous observations. Retention scales rainfall, not streamflow or hydrologic drought severity. The rainfall reference uses matched onset/duration/stations and windows ending by 2015, with 1991–2020 climatology. It is not the hydrologic drought of record or an occurrence probability.

Sessions and append-only review snapshots are in gitignored `local/`. Restore a run from the sidebar. Local files are not encrypted. The server binds loopback, has no accounts, and is intended for one operator. Automatic refreshing and telemetry are disabled. Explicit refresh: `python scripts/fetch_noaa.py`; retain original snapshots with old sessions.

Public evidence and conflict dispositions enter the packet. Provider notes, review notes and private evidence/conflict annotations are excluded unless opted in. Unsigned hashes detect internal inconsistencies within the verifier's scope, not coordinated tampering or source authenticity.

Session/export schema 2.0 and implementation v0.2.0 identify this workflow. Version 1.0 sessions migrate in memory after content/history validation. Save them to persist the migration. Version 1.0 bundles must be re-exported from their original sessions; the new verifier does not silently apply its stronger claim to old packets.

## Verify and package

```powershell
.venv/Scripts/python.exe -m pytest -q
.venv/Scripts/python.exe scripts/check_snapshot_checkout.py
.venv/Scripts/python.exe scripts/demo_smoke.py
.venv/Scripts/python.exe scripts/replay_bundle.py output/BASIN-rehearsal.zip
.venv/Scripts/python.exe scripts/evaluate_selection.py
.venv/Scripts/python.exe scripts/package_demo.py --wheels
```

The rehearsal blocks Python network connections and exercises scaling, replacement, changed priorities, a rejection, evidence conflict, session restoration and privacy-default export. Browser network isolation is a separate developer rehearsal described in `docs/build_validation.md`. Packages include source, tests, documentation, verified data and optional wheels; they exclude user sessions, credentials, private correspondence and legacy executable artifacts.

Core modules live in `basin_core/`; `app.py` and `basin_ui.py` contain the interface. See [methodology](docs/methodology.md), [verification scope](docs/verification_scope.md), [build evidence](docs/build_validation.md), [practitioner exercise](docs/validation_notes.md), [demo runbook](docs/demo_runbook.md), and [shared task board](TODO.md).

The actual presentation laptop, practitioner usefulness, catchment suitability and final team acceptance remain separate release gates.

## Data research

See the [research library](research/README.md) for source packets, policy evidence, reviewed corrections and research assignments. Read its review before using imported AI claims.


## Try local rainfall uploads

After pulling the latest code, run Setup BASIN.cmd to install/update dependencies, then Start BASIN.cmd (Python 3.12 required). Each teammate runs their own local app; sharing a localhost URL does not share a running session. On macOS/Linux, use the setup commands above and start_basin.sh; this release was tested on Windows only.

Open **Data → Preview your local rainfall CSV** (also visible in the initial Workspace). Download the in-app template or use [the illustrative sample](docs/examples/local-rainfall-example.csv). Enter a station name, location description and explicit mm/inches unit. Use exactly `date,precipitation` columns and YYYY-MM-DD dates. One station per file; 10 MB / 250,000 rows maximum.

The preview reports valid/missing days, converts values to mm and shows a chart/table plus the original file hash. Blank values and absent dates remain gaps. Invalid dates, duplicate dates, negative/non-finite values and malformed files are rejected. Removing the file clears its preview. The example is illustrative, not verified historical station data.

**Current scope: preview only.** Uploads are not saved to disk, added to scenarios, assigned historical percentiles or included in exports. PDF ingestion, new-station scenarios and research comparisons are planned next. The existing Review-page CSV replacement is a separate workflow requiring matching scenario dates/stations. The updated app also has manual evidence records and scenario comparisons; those do not yet ingest this local upload. Local app processes are single-user and not an authenticated company server.

See [the implementation plan](docs/local_upload_and_research_plan.md) and [verified build status](docs/build_validation.md). The plan includes future work; its unchecked tasks are not available features.
