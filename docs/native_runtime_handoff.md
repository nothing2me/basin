# Optional native Qwen runtime installation — task handoff

| | |
|---|---|
| Branch | `feat/native-runtime-install` (not merged, not pushed) |
| Worktree | `C:\Users\moham\Documents\GitHub\basin-native-runtime` |
| Base | `origin/main` at `0b3d9031b89674ef7279381284a70edb06f850bb` (fetched 2026-09-10) |
| Implementation commit | `51084b76a1ac856fcef29f8396d0c62416a852de` (this document is committed separately on top of it) |
| For | Astra review and integration. `TODO.md` and `HANDOFF.md` were deliberately not edited. |

## 1. What changed

Before this branch, `Setup BASIN.cmd --with-ai` tried to download model weights but nothing
installed `llama-cpp-python`, so weights could never activate inference. This branch adds a
supported **optional** Windows / CPython 3.12 x64 install and repair path for the native
runtime. It keeps runtime, weights and readiness separate in every message, and the core
install stays unchanged when AI is skipped or fails.

| File | Change |
|---|---|
| `requirements-native.txt` (new) | `llama-cpp-python==0.3.35` and its one extra dependency `diskcache==5.6.3`, each with a `--hash=sha256`. The file also has `--require-hashes`, `--only-binary :all:` and the upstream CPU wheel index. No core package is repeated. |
| `scripts/install_native_runtime.py` (new, stdlib only) | Install, `--repair` and `--check`. Refuses anything except Windows x64, CPython 3.12 inside a venv. Uses `wheelhouse/` offline when it holds the runtime wheel. Imports `llama_cpp` in a separate isolated interpreter and classifies the outcome: absent, wrong version, DLL/VC++ failure, illegal CPU instruction, crash, timeout. Reports weights using the application pin in `basin_core/qwen_runtime.py`. Never downloads weights. |
| `Setup BASIN.cmd` | Parses options before any work. Adds `--ai-runtime` and `--repair-ai`. `--with-ai` is now runtime plus weights. Interactive mode asks about runtime and weights as two separate questions (default No). A final `--check` prints the three states. Replaces the AI section, which failed to parse (§4). Core venv/install lines are byte-identical. |
| `scripts/check_install_consistency.py` | The resolver now strips per-requirement options (`--hash`) and joins `\` continuations. New `native_problems()` enforces exact, hash-locked, binary-only, reviewed source, no includes, and no overlap with `requirements.txt`. It runs whenever the file exists or an install path mentions it. |
| `tests/test_native_runtime_install.py` (new) | Focused behavioural tests; see §5. |
| `README.md` | One paragraph: the two pieces, setup options, `--check`, AVX2/VC++ prerequisites. |
| `.gitattributes` | `*.cmd text eol=crlf`, so batch files ship with CRLF endings. |

Packaging needed no code change. `scripts/package_demo.py` already globs `requirements*.txt`
and ships `scripts/*.py`, `Setup BASIN.cmd` and `basin_core/`; a test asserts all of these
are present and that the hash lines survive packaging. `package_demo.py --wheels` already
ships `wheelhouse/*.whl`, so an offline runtime can travel the same way (§8, step 2).

Not touched: `app.py`, `basin_ui.py`, `basin_core/assistant.py`, `basin_core/qwen_runtime.py`,
calculation/report modules, `requirements.txt`, `requirements-assistant.txt`, CI workflow,
`scripts/fetch_model.py`, `scripts/build_offline_bundle.py`.

## 2. Pin and source: how `llama-cpp-python 0.3.35` was chosen and verified

The old TODO line named 0.3.35 without an install path or evidence. The number was
re-derived from upstream sources on 2026-09-10 rather than copied:

- **Upstream-documented source.** The llama-cpp-python README ("Pre-built Wheel") documents
  `pip install llama-cpp-python --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cpu`
  for basic CPU support. That index page links to GitHub release assets. Its newest Windows
  entry is `v0.3.35/llama_cpp_python-0.3.35-py3-none-win_amd64.whl`, and 0.3.35 is also the
  newest release on PyPI.
- **PyPI has no Windows wheel.** PyPI's 0.3.35 JSON lists a single `sdist`, uploaded
  2026-08-17T09:41Z. Installing from PyPI alone would compile llama.cpp and needs a C/C++
  toolchain. `--only-binary :all:` refuses that, and a test proves it.
- **Release provenance (GitHub REST API).** Tag `v0.3.35`, target `main`, created
  2026-08-17T09:23:51Z, published 10:26:41Z by `github-actions[bot]`, not a prerelease. The
  asset `llama_cpp_python-0.3.35-py3-none-win_amd64.whl` is 7,086,788 bytes, uploaded by
  `github-actions[bot]`, with GitHub-reported digest
  `sha256:31590ea000d5aff6f05f1e428048e72318a83709288159a5bd4dabec530080bb`.
- **Independent check.** A separate `curl` download had the same size and SHA-256.
  `pip download` with the hash-locked file saved the same artifact.
- **Build recipe at the tag.** `.github/workflows/build-and-release.yaml` builds with
  `pypa/cibuildwheel@v3.4.1` on `windows-2022`, `CIBW_ARCHS_WINDOWS: AMD64`. The wheel tag is
  `py3-none-win_amd64`: the bindings use ctypes, so one wheel serves every CPython 3 x64.
  `WHEEL` metadata: `Generator: scikit-build-core 1.0.3`. License: MIT.
- **Not available:** no GitHub artifact attestation (`/attestations/sha256:3159…` returned
  404) and no Sigstore signature. The trust anchor is the GitHub release asset, published by
  the upstream workflow and pinned by hash. Provenance is *consistent*, not cryptographically
  attested.
- **Vendored llama.cpp:** the submodule at `v0.3.35` is `ggml-org/llama.cpp@4df29be4f4c3`
  (committed 2026-08-16). The changelog agrees.
- **Dependencies:** `typing-extensions>=4.5.0`, `numpy>=1.20.0`, `diskcache>=5.6.1`,
  `jinja2>=2.11.3`. All except diskcache are already pinned in `requirements.txt` (4.16.0,
  2.5.2, 3.1.6, markupsafe 3.0.3). diskcache 5.6.1 and 5.6.3 both satisfy the range. 5.6.3
  is the newest (2023-08-31), and no release fixes the advisory in §6. Its PyPI wheel hash
  is `5e31b2d5…ca19`.
- Noted, not relied on: PyPI's 0.3.35 sdist (`1139dbb5…`, 74,868,054 bytes) is a different
  file from the GitHub release sdist (`44867a40…`, 74,867,870 bytes). Neither is installed.

### What the wheel needs from the laptop (observed, not assumed)

- **Microsoft Visual C++ 2015–2022 Redistributable (x64).** `objdump -p` on the wheel's DLLs
  shows imports of `MSVCP140.dll`, `VCOMP140.DLL`, `VCRUNTIME140.dll`, `VCRUNTIME140_1.dll`
  and UCRT `api-ms-win-crt-*`. Python 3.12 ships only `vcruntime140.dll` and
  `vcruntime140_1.dll`, so `MSVCP140`/`VCOMP140` must come from the redistributable. This dev
  machine has them in System32; a clean laptop may not.
- **An AVX2-capable CPU, probably.** Upstream turns off `GGML_NATIVE` for Linux and macOS
  wheels but sets nothing for Windows. The installed wheel reports compiled features
  `SSE3 SSSE3 AVX AVX2 F16C FMA LLAMAFILE OPENMP REPACK` and ships a single `ggml-cpu.dll`
  with no per-CPU variants. A processor without AVX2/FMA/F16C may fault on load. The
  installer maps `STATUS_ILLEGAL_INSTRUCTION` to that explanation. This was not reproduced on
  an older CPU.
- The wheel has no `ggml-rpc.dll` and no server executable; the `llama_cpp.server` Python
  module is present but BASIN never imports it. Upstream builds with `LLAMA_CURL OFF`. The
  network behaviour of import and inference was **not observed** here (§8 step 8).

## 3. Install, repair and failure behaviour

| Invocation | Core | Runtime | Weights download | Final status |
|---|---|---|---|---|
| `Setup BASIN.cmd` (double-click) | yes | asks, default No | asks separately, default No | printed if either was chosen |
| `--no-ai` | yes | no | no | "Optional AI skipped" only |
| `--ai-runtime` | yes | install | **never** | yes |
| `--with-ai` | yes | install | yes, existing `fetch_model.py` | yes |
| `--repair-ai` | yes | force-reinstall native packages only | no | yes |
| unknown option | **nothing runs** | – | – | exit 2 |

- A core install failure still stops setup, with exit 1, before any AI step.
- Setup always exits 0 once the core is installed, whatever the AI result.
- Messages say "Native AI runtime is NOT installed or NOT usable. BASIN core is unaffected."
  for runtime failures and "Model weights were NOT downloaded or did NOT verify." for
  weights. `install_native_runtime.py --check` prints separate `Runtime:`, `Weights:` and
  `Readiness:` lines.
- **READY TO TRY** requires an importable reviewed runtime *and* weights whose size matches
  the pin. It explicitly says no live model test was run. The worker still rehashes the
  weights before every load (`--verify-weights` rehashes on demand).
- The install step can only add or replace `llama-cpp-python` and `diskcache`. Hash-checking
  mode makes pip refuse any unhashed package. Observed: in a venv without core dependencies,
  pip stopped with "In --require-hashes mode, all requirements must have their versions
  pinned with ==" for `typing-extensions` instead of installing it. The installer then says
  to run Setup first.
- A pip success is not reported as success unless the isolated import also succeeds with the
  pinned version.
- Offline: when `wheelhouse\` holds `llama_cpp_python-*.whl`, the installer adds
  `--no-index --find-links wheelhouse`. Otherwise it goes online with `--retries 2 --timeout 30`.
- Unchanged: model hash enforcement, `fetch_model.py`, default offline operation, the core
  and assistant pins, and the no-AI path, which never runs the native installer.

## 4. Pre-existing defect found: the previous AI section never ran

The previous `Setup BASIN.cmd` had `echo ... model (~2.1 GB)...` and
`echo (You can download ... fetch_model.py)` inside parenthesised `if`/`else` blocks. The
unescaped `)` ends the block early.

Running origin/main's script unmodified, except the venv-creation line, against the same
stub pip and stub fetcher used in the tests gave:

| Arguments | Exit | Core pip calls | `fetch_model.py` calls | Last output |
|---|---|---|---|---|
| `--no-ai` | 255 | 1 | 0 | `... was unexpected at this time.` |
| `--with-ai` | 255 | 1 | **0** | `... was unexpected at this time.` |
| none (prompt, empty stdin) | 255 | 1 | 0 | `... was unexpected at this time.` |

So after the core install, every mode aborted without "Setup complete". `--with-ai` never
started a download. This was observed with a stub pip; the parse failure is in the AI
section and does not depend on what pip did. The rewrite uses `goto` labels and keeps
parentheses out of `echo` text inside blocks. Every new mode is exercised by `cmd.exe` in
the tests.

## 5. Evidence (commands as run, results)

All Python runs used `C:\Users\moham\Documents\GitHub\basin\.venv\Scripts\python.exe`
(CPython 3.12.14, AMD64, pip 26.2.1), from the worktree, unless stated. The throwaway venvs
were created from the same base interpreter
(`C:\Users\moham\AppData\Roaming\uv\python\cpython-3.12-windows-x86_64-none\python.exe`).
`py -3.12` is **not** registered on this machine: `py -0p` lists only 3.14. That is why the
real `Setup BASIN.cmd` could not run unmodified here.

1. **Consistency checker:** `python scripts/check_install_consistency.py` → exit 0. Output:
   "requirements.txt resolves to 58 pinned packages; all 7 assistant packages pinned
   exactly. requirements-native.txt (optional) pins 2 packages, each exact, hash-locked and
   binary-only, with no overlap with requirements.txt."
2. **Focused tests:**
   `BASIN_NATIVE_WHEELHOUSE=<scratch>/wh python -m pytest -q -p no:cacheprovider --basetemp=tmp/pytest-focused tests/test_native_runtime_install.py tests/test_install_consistency.py tests/test_qwen_security.py tests/test_qwen_inference.py tests/test_embedded_assistant_ui.py`
   → **92 passed, 1 skipped in 19.01 s**. The skip is `test_real_qwen_inference`, which
   needs weights. After adding the diskcache guard test and staging this document,
   `python -m pytest -q -p no:cacheprovider --basetemp=tmp/pytest-focused3 tests/test_native_runtime_install.py tests/test_install_consistency.py`
   → **70 passed, 1 skipped in 15.70 s**. This time the skip is the genuine-wheel control,
   because the environment variable was not set. An earlier run of the same module failed
   once, on a test-stub bug (`os._exit(0xC000001D)` overflows); the stub now uses the signed
   status code.
   What the new module covers:
   - **Real pip, offline, proxies pointed at `127.0.0.1:9`:** a substituted wheel with the
     right filename is rejected (`THESE PACKAGES DO NOT MATCH THE HASHES`), and no index is
     consulted. A source-only runtime is refused (`from versions: none`) and never built.
     The genuine wheels resolve offline (positive control; runs only when
     `BASIN_NATIVE_WHEELHOUSE` is set, and it was set for this run).
   - **Checker negative controls:** eight weakenings of the file are each detected (hash
     removed, range pin, no `--only-binary`, no `--require-hashes`, unreviewed index, core
     overlap, include, runtime line removed).
   - **Installer unit tests:**
     - supported-target matrix;
     - pip commands are hash-locked and never name `requirements.txt`;
     - wheelhouse selection;
     - probe classification of seven outcomes plus timeout, and a real isolated probe
       reporting absence;
     - weights states through the real `verify_model_file`, including a same-size different
       file detected only with `--verify-weights`;
     - separate runtime/weights/readiness wording;
     - `--check`, unsupported interpreters and failures, with `urllib`/`socket` blocked:
       nothing installed, nothing downloaded, pip success without import reported as
       failure.
   - **`Setup BASIN.cmd` under `cmd.exe`:** the shipped script with only the venv line
     swapped for `python -m venv --without-pip`. A stub `pip` package in the tree records
     arguments; `fetch_model.py` is a stub that records its call. Thirteen cases:
     - `--no-ai`, no option, and answers `n,n`: core only, no native call, no fetch, no
       `llama_cpp` in site-packages;
     - `--ai-runtime`: runtime installed, no fetch, "Weights: NOT DOWNLOADED", "NOT READY";
     - answers `y,n`: runtime only;
     - native pip failure, a DLL import failure, and an illegal-instruction exit: each
       reported honestly, setup still exits 0, core complete;
     - `--with-ai` with a failing fetch: weights failure reported separately;
     - `--repair-ai`: `--force-reinstall --no-deps`;
     - wheelhouse present: both core and native installs use `--no-index`;
     - core failure: exit 1, no AI step;
     - unknown option: exit 2, no venv created.
   - **Package:** the source zip ships the native file, installer, fetcher, runtime module
     and CRLF `Setup BASIN.cmd`, and no `.gguf`. The extracted native file passes the
     checker.
   - **Core without a loadable runtime:** a subprocess where importing `llama_cpp` raises
     `OSError` still builds a `Workspace`, and `get_model_info()["installed"]` is `False`.
3. **Full suite:** `python -m pytest -q -p no:cacheprovider --basetemp=tmp/pytest-full` →
   **500 passed, 2 skipped in 431.65 s**, exit 0.
   - The skips are `test_real_qwen_inference` (no weights) and the genuine-wheel control
     (environment variable not set in that run). This follows from the focused runs above,
     where `test_install_consistency.py` skipped nothing.
   - This run was collected before the one-line diskcache guard test was added. That test
     passed separately (`-k "disk_cache or package"` → 4 passed), and so did the focused
     rerun in item 2.
   - No baseline full-suite run at `0b3d903` was made in this worktree. Test-count
     differences from older HANDOFF checkpoints are not interpreted here.
4. **Real binary install in a throwaway venv** (scratchpad, not the project `.venv`). Core
   subset pinned from `requirements.txt`: `numpy==2.5.2 jinja2==3.1.6 markupsafe==3.0.3
   typing-extensions==4.16.0`.
   - `pip install --dry-run --report` against the hash-locked file: "Would install
     diskcache-5.6.3 llama_cpp_python-0.3.35", with everything else already satisfied.
   - Real install, then `import llama_cpp`: `0.3.35`,
     `CPU : SSE3 = 1 | SSSE3 = 1 | AVX = 1 | AVX2 = 1 | F16C = 1 | FMA = 1 | LLAMAFILE = 1 | OPENMP = 1 | REPACK = 1`,
     `llama_supports_gpu_offload() == False`.
   - `pip uninstall` both packages, then `install_native_runtime.py --check` → "Runtime: NOT
     INSTALLED … Readiness: NOT READY - missing or unusable: runtime, weights", exit 1.
   - `install_native_runtime.py --wheelhouse <scratch>/wh` with
     `HTTP(S)_PROXY=http://127.0.0.1:9 PIP_RETRIES=0` → "Looking in links: …wh", "Successfully
     installed diskcache-5.6.3 llama-cpp-python-0.3.35", "Runtime: INSTALLED", exit 0. An
     offline install with the network path blocked.
   - `install_native_runtime.py --repair --no-summary` (online) → downloaded from the GitHub
     release URL, reinstalled both, dependency pass all "already satisfied", "Runtime:
     llama-cpp-python 0.3.35 imports successfully.", exit 0.
   - `pip freeze` after all of the above: only the six expected packages, at the same core
     versions.
5. **Wheelhouse command verified:**
   `pip download --only-binary :all: --platform win_amd64 --python-version 3.12 --implementation cp --no-deps -r requirements-native.txt -d wh`
   → saved both pinned wheels.
6. **Packaged end-to-end setup with real pip:** `package_demo.build_package()` built the
   source zip, which was extracted in the scratchpad. In the extracted `Setup BASIN.cmd`,
   only `py -3.12 -m venv .venv` was replaced by the base interpreter's `-m venv .venv`,
   because `py -3.12` is unavailable here. Then
   `cmd.exe /d /c "Setup BASIN.cmd" --ai-runtime` (stdin closed, run through Python
   `subprocess` with list arguments) → **exit 0** in 96 s (2026-09-11T02:03:31Z–02:05:07Z).
   - The core install from PyPI succeeded ("Core BASIN installation complete").
   - "[AI 1/2] Native AI runtime", "Installing from the internet …", "Successfully installed
     diskcache-5.6.3 llama-cpp-python-0.3.35", "Native AI runtime installed and importable."
   - The final `--check` printed "Runtime: INSTALLED - llama-cpp-python 0.3.35 …", the `CPU :`
     line above, "Weights: NOT DOWNLOADED", "Readiness: NOT READY - missing or unusable:
     weights.", then "Setup complete."
   - The resulting venv has 60 packages (58 core plus the 2 native). `numpy 2.5.2`,
     `jinja2 3.1.6`, `markupsafe 3.0.3`, `typing-extensions 4.16.0`, `httpx 0.28.1` and
     `streamlit 1.63.0` match the core pins. `pip check`: "No broken requirements found"
     (consistency only, not a security check).
   - An earlier attempt through Git Bash failed before setup ran (`'Setup' is not
     recognized`), because Bash re-quoted the `cmd` arguments. That was a harness problem,
     not the script.
7. `git diff --check` → clean.

## 6. Advisory review — 2026-09-11 01:28–01:30 UTC (2026-09-10 local)

Tool: `pip-audit 2.10.1` in its own venv (`tmp/audit-venv` in the worktree, gitignored), so
the scanner's own dependencies are outside the audited scope. Both the PyPI and OSV sources
were used. Upstream GitHub Security Advisories were read through the REST API, and OSV was
queried by package and by the vendored llama.cpp commit. `pip check` was not used and is not
a vulnerability scan.

Commands:

```bash
A=tmp/audit-venv/Scripts/python.exe
$A -m pip_audit -r <scratch>/native-freeze.txt --no-deps --disable-pip -s pypi --progress-spinner off --desc on
$A -m pip_audit -r <scratch>/native-freeze.txt --no-deps --disable-pip -s osv  --progress-spinner off --desc on
$A -m pip_audit -r requirements-native.txt --no-deps --disable-pip -s pypi --progress-spinner off   # identical content to the draft scanned
$A -m pip_audit -r requirements-native.txt --no-deps --disable-pip -s osv  --progress-spinner off
$A -m pip_audit -r requirements.txt -s pypi --progress-spinner off
$A -m pip_audit -r requirements.txt -s osv  --progress-spinner off
curl https://api.github.com/repos/abetlen/llama-cpp-python/security-advisories
curl https://api.github.com/repos/ggml-org/llama.cpp/security-advisories
curl https://api.github.com/repos/ggml-org/llama.cpp/compare/<fixed-tag>...4df29be4f4c3673f428170fda944a5b19f743bb8
curl -d '{"package":{"name":"llama-cpp-python","ecosystem":"PyPI"}}' https://api.osv.dev/v1/query
curl -d '{"commit":"4df29be4f4c3673f428170fda944a5b19f743bb8"}' https://api.osv.dev/v1/query
```

The scanned `requirements-native.txt` content was the draft in the scratchpad. Its package
lines and hashes are identical to the committed file; only the comments differ.

| Scope | Result |
|---|---|
| Native runtime environment (`pip freeze` of the throwaway venv: 6 packages) | 1 finding: diskcache 5.6.3 (below). `llama-cpp-python 0.3.35`: none. Same on PyPI and OSV. |
| Declared `requirements-native.txt` (2 packages, `--no-deps`) | Same single finding |
| Declared core `requirements.txt` (58 resolved), refreshed | No known vulnerabilities, both sources |
| `abetlen/llama-cpp-python` GHSA | GHSA-56xg-wfcc-g829 / CVE-2024-34359 (Jinja2 SSTI in chat templates), affects 0.2.30–0.2.71, fixed 0.2.72. **Not applicable** to 0.3.35. |
| `ggml-org/llama.cpp` GHSA (13 advisories) | Every advisory with a fix tag/commit is an ancestor of the vendored `4df29be4f`: compare API `ahead` with `behind_by 0` for b8146 (CVE-2026-27940), b7824 (CVE-2026-33298), b5721 (CVE-2025-52566), b5662 (CVE-2025-49847), 26a48ad (CVE-2025-53630), c33fe8b8 (GHSA-g4cc-763q-h9h6), b3561 (CVE-2024-42477/42478/42479) and b3427 (CVE-2024-41130). CVE-2026-34159 (RPC backend) lists no patched version; see RPC exclusion. CVE-2026-21869 is llama-server only; CVE-2024-32878 was fixed at b2740, long before this commit. |
| OSV by vendored commit | CVE-2026-52132 (llama-server `/rerank` DoS) and CVE-2026-86317 (RPC server `deserialize_tensor` assertion). Both ranges are CPE-derived. **Not applicable to the shipped binary:** the wheel contains no server executable and no `ggml-rpc.dll` (full file list inspected); BASIN loads models in-process only. |

**Finding N-1: diskcache 5.6.3, GHSA-w8v5-vhqr-4h9v / CVE-2025-69872 / PYSEC-2026-2447,
no fixed version.** DiskCache uses pickle by default; "an attacker with write access to the
cache directory can achieve arbitrary code execution when a victim application reads from
the cache." It is required by `llama-cpp-python` and imported with it (`llama_cache.py`).
Wheel inspection shows a `diskcache.Cache` is created only by `LlamaDiskCache`, which the
bundled server uses or a caller can pass to `Llama.set_cache()`. BASIN's
`basin_core/qwen_runtime.py` does neither; a new test guards that assumption. Exploitation
would also need local write access to a cache directory BASIN never creates. **Accepted
residual, not fixed** (no fixed release exists). Revisit if BASIN ever enables a llama.cpp
prompt cache, and re-scan before the showcase.

Exclusions and limits:

- Python advisory databases map package *versions*. They do not analyse the bundled C++
  DLLs. No binary/SBOM scan was run.
- No attestation or signature exists, so artifact trust rests on the GitHub release and the
  pinned hash.
- Absence of advisories is not absence of vulnerabilities, and results date from the scan
  time.
- Model weights, their license (`fetch_model.py` records "Qwen Research License") and model
  behaviour are **outside** this review.
- Core packages are version-pinned, not hash-pinned (unchanged).

## 7. Limitations and open gates

- **Not a clean-laptop installation.** The development machine already had the VC++
  runtimes, an AVX2 CPU and a pip cache. The real `Setup BASIN.cmd` could not run unmodified
  because `py -3.12` is not registered here. The stub tests prove control flow and messages,
  not a binary install. The real binary installs (§5.4, §5.6) prove this artifact loads *on
  this machine*.
- **No live inference.** No weights were downloaded, so no model was loaded and no timing,
  offline-inference, crash or timeout behaviour of the real worker was exercised. The live
  gates in `docs/qwen_security_review.md` §3 stay open.
- **AVX2 requirement** is inferred from compiled features, not reproduced on a CPU without
  AVX2. There is no reviewed fallback wheel; such a laptop keeps the direct tools.
- **UI guidance not changed (out of scope).** `basin_ui.py` still shows "Run
  scripts/fetch_model.py to enable local AI" in the `model_missing` state. When weights are
  present but the runtime is missing, the drawer falls through to "Active: Deterministic
  Intent Router" with no install hint. Recommended follow-up for the UI owner: mention
  `Setup BASIN.cmd --ai-runtime` and weights separately.
- `scripts/build_offline_bundle.py` copies whatever is in `.venv`. It will include the runtime
  if installed, but copies only `msvcp140.dll`, not `vcomp140.dll`. The native bundle path was
  not built or tested.
- `--with-ai` changed meaning from "download weights" to "install runtime, then download
  weights". The old meaning never worked (§4).
- The worker's 30-second initialisation budget includes model hashing; laptop timing is
  unmeasured.
- Not assessed: Windows Defender/SmartScreen behaviour on the downloaded DLLs; ARM64 Windows.

## 8. Actual-device steps (presentation laptop)

Record each result, including failures, with Windows version, CPU model and date. Do not
mark a step passed unless it was run on that laptop.

1. **Prerequisites.** Confirm 64-bit Python 3.12 (`py -3.12 -c "import struct;print(struct.calcsize('P')*8)"` → `64`).
   Check for the VC++ 2015–2022 x64 runtime: `C:\Windows\System32\msvcp140.dll` and
   `vcomp140.dll` exist. If missing, install Microsoft's redistributable before the event.
   Check that the CPU supports AVX2 (CPU model lookup, or step 4's output).
2. **Staging the offline copy (on an internet-connected machine).** In a Python 3.12 x64
   environment, from the BASIN folder:
   ```
   python -m pip download -r requirements.txt -d wheelhouse
   python -m pip download --only-binary :all: --platform win_amd64 --python-version 3.12 --implementation cp --no-deps -r requirements-native.txt -d wheelhouse
   python scripts\package_demo.py --wheels
   ```
   Keep the model separately if needed: `python scripts\fetch_model.py` produces
   `models\qwen2.5-3b-instruct-q4_k_m.gguf` (2,104,932,768 bytes, SHA-256
   `626b4a66…c62d`). Weights are not packaged.
3. **Core first, AI off.** Extract to a fresh folder, then `"Setup BASIN.cmd" --no-ai`.
   Expect "Core BASIN installation complete", "Optional AI skipped", "Setup complete". Start
   BASIN and confirm the core workflow and the assistant's direct tools work offline.
4. **Runtime.** `"Setup BASIN.cmd" --ai-runtime`, with the network disconnected if using the
   wheelhouse. Expect "Installing from local wheelhouse (offline)" and "Native AI runtime
   installed and importable". Record the `CPU :` feature line. If it reports a
   Visual C++/DLL problem or an illegal CPU instruction, stop here and record it; BASIN
   remains usable.
5. **Weights.** Copy the verified GGUF into `models\`, or run `.venv\Scripts\python.exe
   scripts\fetch_model.py` with internet. Then run
   `.venv\Scripts\python.exe scripts\install_native_runtime.py --check --verify-weights`.
   Expect "Weights: VERIFIED" and "Readiness: READY TO TRY", and record how long the hash
   took.
6. **Live inference, network disconnected.** Start BASIN, open the AI Assistant. Record
   whether the badge reaches "Ready", how long initialisation took against the 30-second
   budget, and one grounded answer. Optionally run `.venv\Scripts\python.exe
   scripts\qwen_smoke_test.py`.
7. **Failure and recovery.**
   - Rename `models\*.gguf` and confirm the direct-tools fallback, then restore it.
   - Corrupt a copy of the model (not the original) and confirm the worker refuses it.
   - End the worker process in Task Manager during a question and confirm recovery.
   - Run `"Setup BASIN.cmd" --repair-ai` and confirm the runtime returns.
   - To remove AI entirely: `.venv\Scripts\python.exe -m pip uninstall -y llama-cpp-python diskcache`,
     then confirm BASIN still works.
8. **Network behaviour** (separate gate): observe outbound connections from `python.exe`
   while the assistant answers with the network available, e.g. Resource Monitor or
   `Get-NetTCPConnection`. Do not change firewall rules for BASIN.

## 9. Suggested board updates at integration (for Astra)

- The native install/repair path exists, with a justified 0.3.35 pin and a hash-locked,
  binary-only source; §5 records the evidence and the advisory review.
- Record the §4 finding: the previous Setup AI section aborted, so earlier claims that
  `--with-ai` downloaded weights through Setup are not supported by this test.
- Keep open: clean-laptop install (§8 steps 1–4), live offline inference/timing/recovery
  (§8 steps 5–7), native egress observation (§8 step 8), UI install guidance (§7), and the
  model license/provenance review.
