# Report and presentation-device acceptance

Status: manual checks pending. Automated tests and rendered fixtures do not establish that browser/native downloads, installation or scientific interpretation work on the presentation laptop. Record the tested commit, device, browser, date and actual result when doing each check.

1. **Settings match the PDF.** Start a disposable run. In Review, open Reservoir simulation, select 35% initial storage, 30% conservation and pipeline unavailable. Accept the scenario, then preview/export. Confirm scenario ID/revision and all three settings match. Return to Review: those settings should remain selected. A new workspace should use explicitly labelled defaults.
2. **Stale files are no longer offered.** Prepare a preview/export, change a setting or a consented note, and return to Exports. Confirm the old prepared download is cleared or a rebuild is required. Edit the selected scenario: a previous revision must not be silently simulated. Existing downloaded files on disk are historical and are not automatically erased.
3. **Long text is complete and readable.** In the disposable run, add a long review note ending in `END-OF-REVIEW`; opt into notes, export and inspect every page at 100% zoom. Confirm the ending appears, nothing overlaps the footer, and continuation pages have correct numbers. Try accents and an em dash; unsupported CJK/emoji currently produce a disclosed replacement rather than full Unicode text.
4. **Private-note consent works.** Use a fake sentinel such as `PRIVATE-DEMO-123`, never real private information. Export with notes excluded and search the PDF and extracted ZIP contents for it: it must be absent. Opt in and rebuild: it should appear. Revoke consent and rebuild: it must be absent again. Custom-data consent is a separate control; exercise both flags separately with a synthetic CSV.
5. **Downloads work on the actual device.** Test Chrome and the supported native launcher separately. Download/open both PDF and ZIP from the actual destination. Try cancelling a download and rebuilding. Record native write/download errors; a unit test does not cover the native shell.
6. **Offline rehearsal.** After installing the required runtime/dependencies, disconnect the presentation laptop from the network. Launch, create a run, review, export and open the files. Check that optional assistant failure does not block the rainfall workflow. This tests offline operation, not offline installation or daemon egress.
7. **UI/UX.** At normal laptop size and 125% zoom, try light/dark themes, all tutorial steps and keyboard Tab navigation. Check that tutorial targets are actual controls, text is readable, charts remain legible, and no buttons disappear offscreen. Record the exact step and a screenshot for defects.

For repository verification in PowerShell, from the repository directory:

```powershell
.venv/Scripts/python.exe -m pytest -q
.venv/Scripts/python.exe scripts/check_snapshot_checkout.py
.venv/Scripts/python.exe scripts/demo_smoke.py
.venv/Scripts/python.exe scripts/replay_bundle.py output/BASIN-rehearsal.zip
```

Run the smoke before replaying so the rehearsal ZIP is freshly built. Require successful exits and replay `implementation_matches_current: true`.

Still separate: dependency advisory review and optional-stack pinning, live assistant/daemon network checks (SEC.4), frozen-package privacy inspection (SEC.5), renderer failure/degradation handling (B17.3), saved/replayable simulation configuration (B16), and practitioner review of model terminology/units/baselines (B15/B09). Confirm the official speaking time and rehearse the agreed format before freezing the demo. This checklist does not certify the application secure or scientifically validated.
