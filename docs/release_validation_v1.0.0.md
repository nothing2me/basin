# BASIN v1.0.0 release-candidate validation

Validated September 20, 2026 on the development Windows 11 x64 computer.

## Candidate identity

| Item | Result |
|---|---|
| Installer | `Setup-BASIN.exe` |
| Size | 274,714,655 bytes (261.99 MiB) |
| SHA-256 | `AB324AF603A9B31EE6CDD502022BEC5BBBFE61BD57945FB6A9C1ADDD98DB9891` |
| Authenticode | Not signed |
| Embedded payload | 16,367 files; 254.16 MiB compressed |
| Installed core footprint | 770,948,949 bytes (735.23 MiB) |
| Installed footprint with model | 2,869,434,385 bytes (2,736.51 MiB) |

## Results

| Check | Result | Evidence |
|---|---|---|
| Windows/native gates | PASS | Windows x64, CPython 3.12.7, AVX2, MSVCP140/VCOMP140, core imports, data snapshot, loopback port, and offline credentials all passed. |
| Clean build behavior | PASS | The packaging command rebuilt a staged native launcher and payload from the current checkout instead of reusing the September 16 payload. |
| Isolated runtime | PASS | The payload's own Python imported Streamlit, pandas, NumPy, SciPy, and scikit-learn with host environment variables excluded. |
| Silent core install | PASS | `--silent --dir D:\BASIN-release-test --no-shortcuts --no-register` extracted the complete application. |
| Installed launcher identity | PASS | Installed `BASIN.exe` matched the newly staged launcher SHA-256 `F1577236D7EF9F557332E8FB765D120B4CC7B19AD17A477D51A5879E2832B7BD`. |
| Installed app startup | PASS | The packaged launcher selected port 8502 because the development copy occupied 8501; the health endpoint and root page returned HTTP 200. |
| Real optional-model download | PASS | A separate `--with-ai` installation downloaded the model from the pinned upstream revision into a temporary file, then activated it only after verification. |
| Downloaded model integrity | PASS | 2,104,932,768 bytes; SHA-256 `626b4a6678b86442240e33df819e00132d3ba7dddfe1cdc4fbb18e0a9615c62d`. |
| Installed model inference | PASS | llama-cpp-python 0.3.35 loaded the model in 6.48 s, generated responses, retained conversational context, and emitted a valid `check_concurrence` call. |
| Focused automated suite | PASS | 93 passed, 2 skipped across bundle, native runtime, release gates, Qwen inference, and Qwen security tests. |

## Corrections made during validation

- The installer packager now rebuilds the launcher and offline payload on every release build, preventing stale payload reuse.
- Release builds use a dedicated staged launcher, so an open development `BASIN.exe` cannot cause the installer to contain an older launcher.
- Sibling build scripts are invoked by explicit subprocess paths, so direct execution of `scripts/package_setup_exe.py` works reliably.
- The live Qwen smoke test now waits for asynchronous model initialization before evaluating readiness.
- Both Windows executables now report BASIN v1.0.0 and Team NoMiMo in file properties.

## Remaining public-release gates

- Run the installer once on a clean Windows 10 or 11 machine or user profile that has never had BASIN or the development environment installed.
- Decide whether to obtain an Authenticode certificate. The current unsigned installer can trigger Windows SmartScreen or an unknown-publisher warning.
- Download the final asset back from the draft GitHub release and confirm its SHA-256 before publication.
- Test the presentation laptop, projector/zoom, download destination, and offline workflow separately; this development-machine result does not satisfy those device-specific checks.
