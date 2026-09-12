# BASIN device and people acceptance results

Updated: 2026-09-11

This record uses **PASS**, **FAIL**, **PARTIAL** and **NOT RUN**. Development-machine evidence is retained here but cannot satisfy a presentation-laptop, projector, intended-user or organizer gate.

## Release identity

| Field | Recorded value |
|---|---|
| Source revision tested before documentation reconciliation | `cf374bd010295fdc46bb73dca889032a8ff97345` |
| Working device | Development Windows machine; not identified as the presentation laptop |
| OS | Microsoft Windows NT `10.0.26200.0`, AMD64 |
| Python used for browser acceptance/startup check | CPython `3.12.14` from the adjacent project environment |
| Streamlit | `1.63.0` |
| Tracked `BASIN.exe` | 14,869,768 bytes; SHA-256 `838ee698c8ec3d879af622818fb566fcd30c496833b0a2057e0c9dad1e195809` |

The executable identity is recorded, not accepted: it was not launched or frozen-package inspected in this pass.

## Acceptance matrix

| Step | Result | Evidence / remaining work |
|---|---|---|
| Core no-AI browser startup on development machine | **PASS** | `scripts/start_browser.py --no-browser --port 8504` started the app and selected `8505` because `8504` was occupied. It reported readiness at `http://127.0.0.1:8505/`; the test process was stopped afterward. |
| Missing-prerequisite behavior | **PASS on dev / PARTIAL clean-laptop** | Deterministic release gates added in `scripts/check_native_release_gates.py` covering CPython 3.12, AVX2 CPU detection via kernel32, MSVCP140/VCOMP140 OpenMP DLL detection, snapshot integrity, and port exhaustion (89 passing tests). See `docs/t6_native_release_hardening.md`. |
| Actual presentation-laptop install/extract/start/recovery | **NOT RUN** | Requires the named physical device and frozen package. |
| Actual browser offline workflow | **NOT RUN** | Requires the user to control connectivity on the presentation laptop. The Python socket-blocked smoke test is separate evidence. |
| Development-browser tailored Review | **PASS** | Chromium at 1280×720 and 375×812, Dark/Light, all four focus profiles, skipped setup, Show all, Change focus, save/reopen, keyboard focus and tutorial targeting. See `review_acceptance_handoff.md`. |
| Embedded Qwen on presentation laptop | **NOT RUN** | No weights were downloaded and no network setting was changed. Record model hash, runtime readiness, load time, answer timing, cancellation and failure recovery when authorized on the device. |
| Development-browser PDF/ZIP generation, replay and visual inspection | **PASS** | A six-scenario disposable run produced `verified: true`; independent replay verified six scenarios and 300 audit records with `implementation_matches_current: true`. The three-page vector PDF was rendered to PNG and inspected page by page with no clipping, overlap or unreadable section. |
| Development-browser private sentinel off/on/revoked | **PASS after correction** | `PRIVATE-DEMO-123` was absent with consent off, present in the ZIP and PDF with consent on, then absent from both after revocation and rebuild. The revoked PDF disclosed that provider notes were omitted. This exposed and corrected a PDF omission of consented workspace-level provider notes; focused PDF/consent tests passed. |
| Actual browser/native download destination | **NOT RUN** | The browser showed all download controls and the app wrote local artifacts, but the buttons were not used to download through the presentation browser/native shell. Repeat on the actual device and inspect its download location. |
| Projector and 125% zoom | **NOT RUN** | Requires presentation display equipment. |
| Screen-reader acceptance | **NOT RUN** | Not covered by the development browser pass. |
| Intended-user uncoached exercise | **NOT RUN** | Record participant role, task, confusion, completion and resulting wording changes; do not infer domain approval. |
| Organizer format/submission confirmation | **NOT RUN** | Confirm speaking time, submission mechanism/deadline, A/V constraints, publicity and disclosure requirements from organizer communication. |
| Final team rehearsal and backup | **NOT RUN** | Rehearse the confirmed format and record the frozen release plus backup media location. |

## Next physical sequence

1. Freeze and record the final source/package SHA after teammate integration.
2. Run clean no-AI setup and occupied-port/startup recovery on the presentation laptop.
3. With the user controlling connectivity, complete the offline browser workflow and downloads.
4. Inspect consent off/on/revoked PDF and ZIP outputs, then replay the downloaded ZIP.
5. Test the native model only after its runtime/license/provenance gates are ready and the user authorizes any weights download.
6. Test projector/zoom/keyboard, then run the uncoached intended-user exercise.
7. Confirm organizer requirements and rehearse the final, evidence-safe script.

## Development acceptance artifact hashes

These disposable outputs contain no real private information. The final state has consent revoked:

- ZIP SHA-256: `f334f1d25ee633310f5f94c8c3b30a4fd199f1448b4172c1b826ff8fb6f0c9a7`
- PDF SHA-256: `b47494733d705689da3c0d1416f360a6d6c3f242af871faa2b5359d48b431c9d`
