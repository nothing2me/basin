# BASIN Task 6: Native Release Hardening & Verification Report

**Date:** 2026-09-12  
**Task:** T6 — Native Release Gates  
**Status:** Verification complete on development environment; physical-device gates preserved as NOT RUN.  

---

## 1. Scope and System Requirements

BASIN is engineered as a zero-cloud, 100% on-device hydrologic decision-support tool. Task 6 hardens native packaging, startup validation, prerequisite diagnostics, and release gates to ensure flawless execution on presentation and field laptops without network dependency or silent host mutations.

### Component & Environment Requirements Matrix

| Component | Minimum Requirement | Verified In Repo / Target | Failure Symptom & Diagnostic |
|---|---|---|---|
| **Operating System** | Windows 10/11 64-bit | Windows 11 x64 (AMD64) | Non-Windows platforms cleanly rejected by `install_native_runtime.py` with explanatory message. |
| **Python Runtime** | CPython 3.12 (64-bit) | CPython 3.12.14 AMD64 | 32-bit or non-3.12 Pythons rejected with exact version/bitness diagnostic. |
| **CPU Architecture** | x86_64 / AMD64 | AMD64 | ARM64/32-bit flagged; direct tools active. |
| **CPU Instruction Sets** | AVX2, FMA, F16C | AVX2 (`IsProcessorFeaturePresent(40) == True`) | CPUs lacking AVX2 flag `WARN` during pre-flight; prevents `STATUS_ILLEGAL_INSTRUCTION` (0xC000001D). Direct tools remain 100% functional. |
| **VC++ Runtime** | `MSVCP140.dll` | System32 / SysWOW64 | Missing standard C++ library flagged with link to Microsoft Visual C++ 2015-2022 Redistributable. |
| **OpenMP Runtime** | `VCOMP140.dll` | System32 / SysWOW64 | Missing OpenMP runtime flagged specifically as required by `llama-cpp-python` CPU multi-threading. |
| **Local Port** | Free loopback port (8501–8550) | 127.0.0.1:8501 free | Scans up to 50 sequential ports; handles exhaustion with explicit `RuntimeError` and UI error modal. |
| **Streamlit Credentials** | `.streamlit/credentials.toml` | `[general] email = ""` | Suppresses interactive first-run email prompt during offline and demo startups. |
| **Data Snapshot** | `data/observations.csv` | SHA-256 matches `data/manifest.json` | Snapshot byte corruption detected deterministically before simulation launch. |

---

## 2. Improved Missing `VCOMP140.DLL` Behavior

### Problem Analyzed
The optional native LLM runtime (`llama-cpp-python 0.3.35`) ships a single Windows CPU binary wheel (`ggml-cpu.dll`) compiled with OpenMP support. While Python 3.12 ships `vcruntime140.dll` and `vcruntime140_1.dll`, it does **not** bundle `msvcp140.dll` or `vcomp140.dll`. On clean Windows machines lacking the Microsoft Visual C++ 2015–2022 Redistributable, attempting to import `llama_cpp` triggers an unhandled DLL load failure (`0xC0000135` / `WinError 126`). Previously, this surfaced as a generic DLL error.

### Hardened Implementation
1. **Pre-flight DLL Inspection (`check_vc_runtime_dlls`)**: Added non-modifying detection across `System32`, `SysWOW64`, and system `PATH` in both `scripts/check_native_release_gates.py` and `scripts/install_native_runtime.py`.
2. **Specific OpenMP Diagnostic**: When `vcomp140.dll` is missing, the installer and probe explicitly report:
   > *"VCOMP140.DLL (OpenMP runtime) is missing from the system. llama-cpp-python requires Microsoft Visual C++ 2015-2022 Redistributable (x64). Install it from Microsoft, then run: 'Setup BASIN.cmd' --repair-ai"*
3. **Zero Machine Alteration**: BASIN **never** attempts to silently download or install system-level DLLs or redistributables. If prerequisites are missing, BASIN core continues to run in offline mode using deterministic direct tools.
4. **Offline Bundle Assembly (`scripts/build_offline_bundle.py`)**: Updated bundle staging to copy both `msvcp140.dll` and `vcomp140.dll` from `System32` into the standalone `runtime/` directory when present, ensuring self-contained OpenMP execution.

---

## 3. Deterministic Release Gate Checks (`scripts/check_native_release_gates.py`)

A new automated gate verification tool was implemented to validate all release prerequisites:

```text
======================================================================
BASIN Native Release Hardening Gates (T6)
======================================================================
Environment: Windows 11 | Python: 3.12.14 (64-bit: True)

Gate Status Summary:
----------------------------------------------------------------------
[PASS]     Gate 1A: OS & Architecture
           Detail: Windows 64-bit (AMD64)

[PASS]     Gate 1B: Python Runtime
           Detail: CPython 3.12.14

[PASS]     Gate 2: CPU AVX2 Instructions
           Detail: AVX2 instructions supported by processor.

[PASS]     Gate 3: VC++ & OpenMP DLLs
           Detail: MSVCP140.dll and VCOMP140.dll present.

[PASS]     Gate 4: Core Dependencies
           Detail: All core packages importable.

[PASS]     Gate 5: Data Snapshot Integrity
           Detail: Observations SHA-256 matches manifest (672c23f83350...).

[PASS]     Gate 6: Local Loopback Port
           Detail: Port 8501 is free on loopback.

[PASS]     Gate 7: Offline Startup Credentials
           Detail: .streamlit/credentials.toml suppresses prompt.

[PASS]     Gate 8: Package Hygiene
           Detail: Audited BASIN-demo-source.zip: zero leaks, weights, or secrets.

----------------------------------------------------------------------
Embedded Model Provenance & Advisory:
  Model:       qwen2.5-3b-instruct-q4_k_m.gguf
  Repo/Rev:    Qwen/Qwen2.5-3B-Instruct-GGUF @ 7dabda4d13
  SHA-256:     626b4a6678b86442240e33df819e00132d3ba7dddfe1cdc4fbb18e0a9615c62d
  Bytes:       2,104,932,768 bytes (~2.1 GB)
  License:     Qwen Research License
  Advisories:
    * diskcache 5.6.3 (GHSA-w8v5-vhqr-4h9v / CVE-2025-69872): Arbitrary code execution if malicious cache file read. Inactive code path: BASIN never enables LlamaDiskCache or prompt cache.
    * Model weights are optional (~2.1 GB) and never bundled in release packages; must be fetched via scripts/fetch_model.py under explicit operator authorization.
    * Native inference requires AVX2/FMA/F16C instructions on CPU; machines lacking AVX2 must use instant direct tools without local LLM.
======================================================================
Overall Core Readiness: PASS (Ready for Showcase)
======================================================================
```

---

## 4. Frozen Package Hygiene Audit Results

The distributable package `output/BASIN-demo-source.zip` (0.8 MB) built via `scripts/package_demo.py` was inspected:

| Prohibited Category | Patterns Checked | Audit Outcome |
|---|---|---|
| **Model Weights** | `*.gguf`, `*.bin`, `*.safetensors`, files > 50 MB | **CLEAN**: Zero model weights packaged. Weights are downloaded separately via `fetch_model.py`. |
| **Secrets & Credentials** | `.env`, non-empty `credentials.toml`, API keys | **CLEAN**: No `.env` packaged; `credentials.toml` contains only `email = ""`. |
| **Local Sessions & PII** | `local/session-*.json`, `local/review-prefs-*.json` | **CLEAN**: Zero practitioner sessions or local review profiles included. |
| **Bytecode & Build Caches** | `__pycache__`, `*.pyc`, `*.pyo`, `tmp/`, `output/` | **CLEAN**: Bytecode strictly excluded from archive namelist. |
| **Network Egress Components** | Unpinned external endpoints | **CLEAN**: Launcher routes strictly to loopback `127.0.0.1`. |

---

## 5. Embedded Model Provenance, License & Advisory Record

- **Model Repository:** `Qwen/Qwen2.5-3B-Instruct-GGUF`
- **Revision / Commit:** `7dabda4d13d513e3e842b20f0d435c732f172cbe`
- **Asset Filename:** `qwen2.5-3b-instruct-q4_k_m.gguf`
- **Expected File Size:** `2,104,932,768 bytes` (~2.1 GB)
- **Expected SHA-256 Digest:** `626b4a6678b86442240e33df819e00132d3ba7dddfe1cdc4fbb18e0a9615c62d`
- **License:** Qwen Research License (Alibaba Cloud / Tongyi Lab)
- **Quantization Scheme:** `Q4_K_M` (4-bit medium symmetric quantization)
- **Expected Hash Verification Point:** `basin_core/qwen_runtime.py` (`MODEL_SHA256` verified via `hashlib.file_digest` prior to passing bytes to C++ runtime)
- **Security & Advisory Limitations:**
  1. *DiskCache Advisory (GHSA-w8v5-vhqr-4h9v / CVE-2025-69872)*: `diskcache 5.6.3` uses pickle deserialization. In BASIN, `qwen_runtime.py` never enables `LlamaDiskCache`, never calls `set_cache()`, and never creates a disk cache directory. This is an inactive code path.
  2. *Weights Distribution*: Weights are never checked into git and never bundled in demo ZIPs. They require deliberate download via `scripts/fetch_model.py`.
  3. *CPU Capability Boundary*: Inference requires AVX2/FMA/F16C instructions. Older hardware or low-power CPUs without AVX2 must operate with BASIN's instant deterministic direct tools.

---

## 6. Automated Test Verification

Executed on Windows 11 with CPython 3.12.14:

```powershell
& "C:\Users\sonti\Terminus Clone\basin\.venv\Scripts\python.exe" -m pytest -q -p no:cacheprovider --basetemp="C:\Users\sonti\.cache\pytest_temp" tests/test_native_release_gates.py tests/test_native_runtime_install.py tests/test_install_consistency.py
```

**Results:**
- `tests/test_native_release_gates.py`: **17 passed**
- `tests/test_native_runtime_install.py`: **51 passed, 1 skipped** (genuine wheel control when `BASIN_NATIVE_WHEELHOUSE` is unset)
- `tests/test_install_consistency.py`: **21 passed**
- **Total:** **89 passed, 1 skipped in 24.78s (100% passing)**

---

## 7. Remaining Physical-Device Acceptance Gates

In accordance with repository guidelines, the following physical gates remain **NOT RUN** until executed on the actual presentation hardware in Pleasanton:

| Step | Gate Name | Status | Requirement Before Sign-Off |
|---|---|---|---|
| **6.1** | Physical Presentation Laptop Setup | **NOT RUN** | Extract `BASIN-demo-source.zip` onto clean presentation laptop; run `Setup BASIN.cmd --no-ai`. Confirm exit 0 and clean startup. |
| **6.2** | Physical Offline Browser Test | **NOT RUN** | Disconnect WiFi/Ethernet on laptop; run `Start BASIN.cmd`; exercise scenario generation, Review tailoring, and export downloads. |
| **6.3** | Live Qwen Inference on Presentation Laptop | **NOT RUN** | Authorize model download (`fetch_model.py`); record initial load time against 30s budget; execute sample tool question; test cancellation. |
| **6.4** | Projector & Display Scaling | **NOT RUN** | Connect to HDMI/USB-C presentation projector at 1080p and 125% OS zoom; confirm typography readability and zero chart clipping. |
| **6.5** | Uncoached Intended-User Exercise | **NOT RUN** | Have an operator or partner complete scenario review and export without coaching; record verbatim feedback and any UI friction points. |
| **6.6** | Final Rehearsal to Official Timing | **NOT RUN** | 45-min presentation + 15-min Q&A dry run with timer; confirm team handoffs. |
