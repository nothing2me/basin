# BASIN

**Basin Analysis and Scenario Intelligence Navigator** is a local rainfall evidence workbench for the Coastal Bend / Region N hackathon project.

Use public NOAA observations to construct rainfall stress scenarios, compare their measurements and priorities, challenge assumptions, and prepare a reviewed packet for deeper hydrologic analysis. The core calculation engine is 100% deterministic Python with local KMeans clustering and no required LLM or cloud inference. The built-in analyst assistant uses an embedded deterministic intent engine for read-only questions. It requires no Ollama installation, model download, or inference service.

## Key features

- **Deterministic scenario generation:** Resample complete synchronized historical rainfall windows (NOAA GHCN-Daily 1991–2025) across regional stations with declared stress retention factors.
- **Unsupervised profile grouping:** Cluster hundreds of drought candidates into distinct profiles using local KMeans (severity, duration, concurrence, seasonality, and dry spells).
- **Human review & revision tracking:** Inspect metrics, challenge assumptions, record evidence disagreements with human dispositions, and apply multipliers or CSV edits with automatic approval invalidation.
- **Cryptographically verified data packet:** Package shortlisted scenarios into a reproducible `.zip` bundle with SHA-256 manifest, audit trail, and raw daily rainfall CSV.
- **Executive brief (PDF deliverable):** Generate a publication-grade PDF summary for City Council members and water planners, featuring dynamic breach countdowns and illustrative drought response benchmarks.
- **Illustrative stress spectrum:** Sweep 4-tier storage drawdowns (100%, 80%, 60%, 40% rainfall) on a two-pool reservoir model to identify Stage 3 tipping points and quantify emergency conservation benefits.
- **Privacy-first & offline by design:** 100% local execution with loopback binding, zero cloud telemetry, and strict opt-in consent before exporting private reviewer notes.
- **Embedded analyst assistant:** Explore scenarios, station stress, and priority sensitivity using the built-in intent engine and deterministic calculation tools. Supported questions map to fixed templates; this is not a general-purpose language model. Ask complete questions and include scenario IDs when comparing.

## Supported Windows presentation path

Use **Python 3.12, 64-bit** and the browser launcher. Extract the complete package, run **Setup BASIN.cmd** once, then **Start BASIN.cmd**. Setup installs the exact requirements from `wheelhouse/` when supplied, otherwise from the internet. After setup, the app and its coordinate overview work locally. Keep the console open; Ctrl+C stops the app.

The launcher starts at port 8501 and chooses another local port if needed. Its console prints the actual address. Runtime needs no API key or account. On Windows, the rebuilt `BASIN.exe` opens the same local app in a native WebView2 window after **Setup BASIN.cmd** has created the Python environment.

```powershell
py -3.12 -m venv .venv
.venv/Scripts/python.exe -m pip install -r requirements.txt
.venv/Scripts/python.exe scripts/start_browser.py
```

The offline Windows wheel bundle is specific to CPython 3.12 x64. Python itself must be installed beforehand. macOS/Linux require their own dependency installation and validation; `start_basin.sh` is provided without a presentation-support claim.

## Appearance and help

Start with **Try an example** to open an unapproved rainfall scenario, or **Use my data** for CSV preview and comparison. Advanced scenario settings remain in the sidebar.

Open **Settings** in the sidebar for Light, Dark or System appearance and color customization. Three horizontal color pickers control buttons, selected options and the sidebar; choose **Apply colors** to apply drafts or **Reset colors** to restore defaults. Custom choices last for the current session; the native theme choice is remembered by the browser. **Color-blind mode** uses a consistent interface accent and chart colors with line styles, shapes and patterns. This is an accessibility aid, not a complete accessibility certification.

**Take a tour** or **Help & tutorial** starts the guided walkthrough. Instructions appear beside the highlighted target and the app scrolls to it automatically. **AI Assistant** opens a slide-out drawer for conversational questions about scenarios, station stress, and sensitivity (routing strictly to deterministic read-only tools). **Personal notes** is available at the top right of an active analysis; notes save locally and are excluded from exports unless explicitly included. **Exports** offers an in-app brief preview, downloadable Markdown brief, and publication-ready **PDF Executive Brief** before building the verified packet. Previewing does not bypass approval requirements.

After pulling updates, restart the running app to load changed Python modules and theme configuration. Saved analyses remain in the local directory; save notes before stopping the process. See [UX research and foundation checklist](docs/ux_research_and_simplification.md) for implementation status and remaining area-model work.

## Analyst workflow

1. **Data:** inspect provisional stations, completeness, flags, observation history and the snapshot manifest.
2. **Workspace:** generate complete historical rainfall windows with declared retention factors. Inspect groups and score contributions, compare two or three candidates, and preview alternative priorities on the same pool. Ranking changes preserve your shortlist until an explicit rebuild or swap.
3. **Review:** trace a metric to its evidence, compare two cited records, record a public disagreement and human disposition, and leave unresolved issues visible. Add cited records to a scenario. Private annotations stay local by default.
4. **Review rainfall:** edit daily values, apply a multiplier or replace the same dates/stations from CSV. Edits recompute metrics and clear acceptance. Accept or reject each shortlisted revision; rejection requires a reason. Acceptance is a local content decision, not professional certification.
5. **Exports:** inspect included evidence and unresolved issues, set privacy consent for free-text review notes, and build verified deliverables: a publication-grade **Executive Brief (PDF)** for council decision-makers, a **Technical Handoff Brief (Markdown)**, and an immutable **Data Bundle (ZIP)**. Replay verifies cryptographic SHA-256 and mathematical consistency before download.

The optional **Reservoir simulation** view is an uncalibrated, illustrative experiment. All material assumptions are shown. It provides a **1-Click Multi-Tier Stress Spectrum** across four rainfall retention tiers (100%, 80%, 60%, 40%) to calculate days-to-breach countdowns for Stage 1, 2, and 3 triggers and quantify emergency conservation buffer impact. Its settings, results and conditional storage bands are excluded from saved evidence packets and their verification. It does not predict reservoir levels, deliveries, safe yield or official restriction dates.

## Data, limits and privacy

The bundled NOAA GHCN-Daily snapshot covers 1991–2025 at Corpus Christi, Victoria and San Antonio airport stations. These are provisional regional proxies, not validated catchment rainfall. Whole-window sampling preserves complete simultaneous observations. Retention scales rainfall, not streamflow or hydrologic drought severity. The rainfall reference uses matched onset/duration/stations and windows ending by 2015, with 1991–2020 climatology. It is not the hydrologic drought of record or an occurrence probability.

Sessions and append-only review snapshots are in gitignored `local/`. Restore a run from the sidebar. Local files are not encrypted. The server binds loopback, has no accounts, and is intended for one operator. Automatic refreshing and telemetry are disabled. Explicit refresh: `python scripts/fetch_noaa.py`; retain original snapshots with old sessions.

Public evidence and conflict dispositions enter the packet. Provider notes, review notes, and private evidence/conflict annotations are excluded from both the Markdown brief and PDF report unless explicitly opted in. Cryptographic SHA-256 verification applies to the companion ZIP data bundle (rainfall series, shortlist, and audit trail); the PDF is a companion decision brief. Unsigned hashes detect internal inconsistencies within the verifier's scope, not coordinated tampering or source authenticity.

Analyses without custom evidence retain session/export schema 2.0. Saving custom evidence uses schema 2.1; implementation remains v0.2.0. The current verifier supports both 2.0 and 2.1 packets. Version 1.0 sessions migrate in memory after content/history validation. Save them to persist the migration. Version 1.0 bundles must be re-exported from their original sessions; the new verifier does not silently apply its stronger claim to old packets.

## Verify and package

```powershell
.venv/Scripts/python.exe -m pytest -q
.venv/Scripts/python.exe scripts/check_snapshot_checkout.py
.venv/Scripts/python.exe scripts/demo_smoke.py
.venv/Scripts/python.exe scripts/replay_bundle.py output/BASIN-rehearsal.zip
.venv/Scripts/python.exe scripts/evaluate_selection.py
.venv/Scripts/python.exe scripts/package_demo.py --wheels
```

The rehearsal blocks Python network connections and exercises scaling, replacement, changed priorities, a rejection, evidence conflict, session restoration and privacy-default export. Browser network isolation has a separate developer harness, `scripts/browser_rehearsal.mjs`, which needs Node and Playwright; no run of it is recorded in `docs/build_validation.md`. Packages include source, tests, documentation, verified data and optional wheels; they exclude user sessions, credentials, private correspondence and legacy executable artifacts.

Core modules live in `basin_core/`; `app.py` and `basin_ui.py` contain the interface. See [finalist excellence plan](docs/finalist_excellence_plan.md), [competition submission & Q&A](docs/submission_record.md), [current claim inventory](docs/claim_inventory.md), [presentation plan](docs/presentation_plan.md), [methodology](docs/methodology.md), [verification scope](docs/verification_scope.md), [build evidence](docs/build_validation.md), [practitioner exercise](docs/validation_notes.md), [demo runbook](docs/demo_runbook.md), and [shared task board](TODO.md).

The actual presentation laptop, practitioner usefulness, catchment suitability and final team acceptance remain separate release gates.

## Data research

See the [research library](research/README.md) for source packets, policy evidence, reviewed corrections and research assignments. Read its review before using imported AI claims.


## Try local rainfall uploads

After pulling the latest code, run Setup BASIN.cmd to install/update dependencies, then Start BASIN.cmd (Python 3.12 required). Each teammate runs their own local app; sharing a localhost URL does not share a running session. On macOS/Linux, use the setup commands above and start_basin.sh; this release was tested on Windows only.

Open **Data → Upload and observe your custom CSV.** (also visible in the initial Workspace). Download the in-app template or use [the illustrative sample](docs/examples/local-rainfall-example.csv). Enter a station name, location description and explicit mm/inches unit. Use exactly `date,precipitation` columns and YYYY-MM-DD dates. One station per file; 10 MB / 250,000 rows maximum.

The preview reports valid/missing days, converts values to mm and shows a chart/table plus the original file hash. Blank values and absent dates remain gaps. Invalid dates, duplicate dates, negative/non-finite values and malformed files are rejected. Removing the file clears its preview. The example is illustrative, not verified historical station data.

**Save reviewed custom evidence:** create or open an analysis, then visit Data. Uploading alone remains temporary. Choose a NOAA reference, then open **Save reviewed upload into this analysis**. Enter the source/provider, daily observation definition, suitability rationale (including uncertainty), scenario links and explicit local-storage confirmation. Original CSV bytes are stored separately from normalized records inside the local session JSON; filenames are not stored. Saved custom evidence can be inspected after reopening an analysis.

This links supporting comparison evidence; it does **not** replace NOAA scenario rainfall, create a local-station model or establish catchment suitability. Unknown station relationships or daily periods are saved with a blocked comparison rather than fabricated results. Choose an existing current evidence version to replace it, retaining its scenario links. Every version stays in history and affected approvals are cleared, including when the rationale or reference changes. Existing Review-page numerical CSV replacement remains a separate exact-date/station operation.

In Exports, explicitly choose **Include custom numerical inputs and source metadata in this replayable export**. This includes all saved normalized versions, station/location/provider metadata and suitability rationale required to reproduce and interpret the comparisons. Original CSV bytes are never included. Private notes retain their separate opt-in. Without custom-data consent, the replayable export is blocked; BASIN does not label an incomplete packet reproducible. Source metadata can be sensitive: review the inclusion notice. The local store is unencrypted and single-operator.

PDF ingestion, numerical scenarios driven by a new local station, seasonal baseline validation and geographic modeling remain separate future work.

See [the implementation plan](docs/local_upload_and_research_plan.md) and [verified build status](docs/build_validation.md). The plan includes future work; its unchecked tasks are not available features.

## Updating an already running app

Stop BASIN with Ctrl+C in its server console **before pulling updates**. Pull the latest main, run Setup BASIN.cmd if dependencies changed (or when unsure), then run Start BASIN.cmd again. Refresh the browser at the address printed by the launcher and restore a saved session or generate a new run. Unsaved in-memory work is not preserved by a restart; save before updating when the current app is functioning.

If you see `AttributeError: 'Workspace' object has no attribute 'selection_reason'` or a missing `evidence` attribute after an update, restart the server, not just the browser tab. An old process may retain an earlier Workspace class or session object while loading newer interface code. The current source includes these members. Use the Python/browser launcher above; the legacy downloaded executable is not rebuilt by git pull.

## Part B: compare uploaded rainfall with public data

In **Data → Upload and observe your custom CSV.**, upload data within the bundled NOAA period (1991–2025), then use **Compare with public rainfall**. Choose one public station deliberately, declare whether it is the same physical station or only a regional proxy, and confirm that daily observation periods are comparable. Leave these unconfirmed when unknown; BASIN then blocks calculation.

The comparison shows daily series and totals on dates where both datasets have valid values. Missing days are excluded from both totals. The signed difference is uploaded minus reference; relative difference is unavailable when the reference total is zero. This is not a seasonal normal, historical percentile, catchment calibration or shortage prediction. A regional difference does not establish which source is correct.

You may explicitly opt in to download a separate comparison JSON containing the numerical rows, method, reference station/snapshot hash, original upload hash and user-declared comparison basis. It omits the entered station/location text and does not include the original uploaded file. Numerical rows may still be private. This report is not the scenario ZIP and is not covered by that verifier. That standalone download remains separate. Use Save reviewed upload for versioned session/evidence integration and the consented schema 2.1 scenario packet for verified replay. The verifier recomputes custom paired-day results against its bundled NOAA snapshot; the original byte hash is recorded but cannot be independently verified without the private original.
