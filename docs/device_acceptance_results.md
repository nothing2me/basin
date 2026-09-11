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
| Missing-prerequisite behavior | **PARTIAL** | Explicit failure messages exist and automated tests cover port exhaustion. A clean machine with missing Python/Streamlit was not exercised. |
| Actual presentation-laptop install/extract/start/recovery | **NOT RUN** | Requires the named physical device and frozen package. |
| Actual browser offline workflow | **NOT RUN** | Requires the user to control connectivity on the presentation laptop. The Python socket-blocked smoke test is separate evidence. |
| Development-browser tailored Review | **PASS** | Chromium at 1280×720 and 375×812, Dark/Light, all four focus profiles, skipped setup, Show all, Change focus, save/reopen, keyboard focus and tutorial targeting. See `review_acceptance_handoff.md`. |
| Embedded Qwen on presentation laptop | **NOT RUN** | No weights were downloaded and no network setting was changed. Record model hash, runtime readiness, load time, answer timing, cancellation and failure recovery when authorized on the device. |
| PDF/ZIP actual downloads and visual inspection | **NOT RUN** | Automated renderer, consent and replay tests are recorded elsewhere; they do not prove browser/native download behavior or final-page readability on the device. |
| Private sentinel off/on/revoked through actual downloads | **NOT RUN** | Use harmless `PRIVATE-DEMO-123`; inspect extracted ZIP and PDF for absence/presence/absence. |
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
