# BASIN v1.0.0 GitHub release

## Release title

**BASIN v1.0.0 — Offline Rainfall Scenario Screening and Expert Handoff**

## Release notes

Copy the following text into the GitHub release description:

---

BASIN turns public precipitation records into a transparent shortlist of historical rainfall scenarios and a replay-verified handoff packet for technical review. It is designed for pre-model screening and discussion. It is not a calibrated reservoir-reliability model, a hydrologic forecast, or a substitute for an official water-supply model or professional review.

### What is included

- A Windows desktop installer with its own Python runtime; no separate Python installation is required.
- Synchronized multi-station historical-window resampling with deterministic PCG64 seeds.
- Rainfall-scenario clustering using five shared features plus one normalized station-deficit feature for each selected station.
- A transparent, assumption-driven reservoir stress illustration whose results are clearly separated from hydrologic validation.
- Replay-verified ZIP exports with SHA-256 file checks and independent calculation replay.
- Observed-versus-filled rainfall coverage, station provenance, explicit assumptions, and named human-review attribution.
- Thirteen deterministic, read-only assistant tools that work without a language model.
- An optional local Qwen2.5 3B assistant download for conversational tool selection.

### Install

1. Download `Setup-BASIN.exe` and run it on 64-bit Windows 10 or Windows 11.
2. The core application installs to the current user's profile and works without the optional model download.
3. To enable local conversational assistance, select the Qwen option during setup or run `Download AI Model.cmd` from the installation folder later. The model download is approximately 2.1 GB.

The installer is 274,714,655 bytes (261.99 MiB). A core installation uses approximately 735 MiB. An installation with the optional model uses approximately 2.67 GiB.

### Verify the installer

Run this command in PowerShell after downloading:

```powershell
Get-FileHash .\Setup-BASIN.exe -Algorithm SHA256
```

Expected SHA-256:

```text
AB324AF603A9B31EE6CDD502022BEC5BBBFE61BD57945FB6A9C1ADDD98DB9891
```

### Validation completed on September 20, 2026

- All seven Windows/native release gates passed on Windows 11 x64.
- The newly built installer completed an isolated no-model installation.
- The installed application's bundled Python imported the required scientific packages.
- The installed application started its local Streamlit service and returned HTTP 200.
- A second isolated installation downloaded the optional model from its pinned Hugging Face revision.
- The downloaded model was exactly 2,104,932,768 bytes and matched SHA-256 `626b4a6678b86442240e33df819e00132d3ba7dddfe1cdc4fbb18e0a9615c62d`.
- The installed Qwen runtime loaded the model, generated a novel response, retained follow-up context, and produced a valid structured `check_concurrence` tool call.
- Focused packaging, native-runtime, release-gate, inference, and security tests passed: 93 passed and 2 optional-path tests skipped.

This validation was performed on the development Windows 11 computer. It does not replace a final clean-machine test on the presentation or distribution laptop.

### Data, software, and model terms

- NOAA NCEI GHCN-Daily precipitation data: public-domain source data.
- Basemap: Sentinel-2 cloudless imagery by EOX IT Services GmbH, CC BY 4.0.
- Optional model: Qwen2.5-3B-Instruct GGUF at pinned revision `7dabda4d13d513e3e842b20f0d435c732f172cbe`, under the Qwen Research License.
- BASIN source code: MIT License. Third-party packages and data retain their own terms.

### Scope and limitations

“Replay-verified” means that the exported files and calculations can be checked for internal consistency. It does not mean that rainfall inputs, runoff relationships, reservoir operations, threshold dates, or water-supply conclusions have been hydrologically validated. Operational use would require watershed-representative precipitation, calibrated rainfall-runoff and routing, observed inflow and storage validation, dynamic net evaporation, actual transfers/releases/demand, uncertainty analysis, hindcasting, and independent practitioner review.

The Windows installer is not Authenticode-signed, so Windows may display an unknown-publisher or SmartScreen warning.

---

## Release asset

| Asset | Bytes | SHA-256 |
|---|---:|---|
| `Setup-BASIN.exe` | 274,714,655 | `AB324AF603A9B31EE6CDD502022BEC5BBBFE61BD57945FB6A9C1ADDD98DB9891` |

Do not upload the separate Qwen weight file as a BASIN release asset. The installer downloads the pinned upstream model only when the user selects that option.

## Publication checklist

1. Commit and push the release-pipeline fixes and this release document.
2. Test `Setup-BASIN.exe` on a clean 64-bit Windows 10 or 11 account or machine.
3. Decide whether to code-sign the installer. If it remains unsigned, keep the warning above in the release notes.
4. Create annotated tag `v1.0.0` at the final release commit.
5. Create a draft GitHub release using the title and notes above.
6. Upload only the validated `Setup-BASIN.exe` and confirm GitHub reports 274,714,655 bytes.
7. Download the draft asset once, re-run the SHA-256 command, install it, and start BASIN.
8. Publish the release.
9. Update `docs/index.html` to use the published asset URL, 261.99 MiB size, and the SHA-256 above; then verify both website download buttons.
