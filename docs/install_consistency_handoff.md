# Installation and dependency-pin consistency — integration handoff

Branch `chore/assistant-install-consistency`, based on `origin/main` at
**`354590924e168eb8a6adcb6569579489273ed0d1`** (`3545909`). Developed in a separate
worktree while another agent worked on assistant model filtering. Not merged, not pushed.

`TODO.md` and `HANDOFF.md` were deliberately left untouched to avoid conflicting with
concurrent work; fold the summary below into them at integration time.

## 1. Inventory of installation, CI, packaging and build paths

| Path | Installs Python dependencies? | What it does |
|---|---|---|
| `Setup BASIN.cmd` | **Yes** | Creates `.venv`, then `pip install -r requirements.txt`, using `--no-index --find-links wheelhouse` when a `wheelhouse/` directory is present |
| `.github/workflows/tests.yml` | **Yes** | `python -m pip install -r requirements.txt`, then snapshot check, pytest, smoke, replay and source packaging |
| `README.md` documented commands | **Yes** | `py -3.12 -m venv .venv` then `pip install -r requirements.txt` |
| `start_basin.sh` | No | Refuses to start without `.venv` and prints the manual install command |
| `scripts/build_offline_bundle.py` | No | Copies the already-populated `.venv/Lib/site-packages` into a runtime directory |
| `scripts/build_exe.py` | No | Runs PyInstaller against the existing environment (needs `requirements-build.txt` installed separately) |
| `scripts/package_setup_exe.py`, `scripts/basin_installer.iss` | No | Wrap already-built artifacts |
| `scripts/package_demo.py` | No | Zips tracked source; `--wheels` adds `wheelhouse/*.whl` |
| `wheelhouse/` | n/a | Populated by hand with `pip download`; no script generates it and none is committed |

Three paths actually install dependencies, and all three named `requirements.txt` only.

## 2. Problems found

1. **The reviewed assistant pins were in force nowhere.** `requirements-assistant.txt`
   pinned `httpx`, `httpcore`, `pydantic`, `pydantic-core`, `annotated-types` and
   `typing-inspection`, but no installing path read that file. Every install resolved those
   packages freshly, so the versions implementing the assistant's proxy, redirect and
   timeout behaviour were whatever pip picked that day.
2. **The source package omitted a requirements file its own instructions reference.**
   `scripts/package_demo.py` carried a hand-written file list containing `requirements.txt`
   only. A recipient extracting `BASIN-demo-source.zip` and following `docs/ollama_setup.md`
   would hit a missing `requirements-assistant.txt`. `requirements-build.txt` was missing too.

## 3. What changed

**One version list, referenced once.** `requirements.txt` now begins with
`-r requirements-assistant.txt`. Every path that installs `requirements.txt` — the Windows
setup script in both its online and offline branches, CI, and the documented manual
commands — applies the reviewed pins with no change to any of those commands and no
version number duplicated anywhere. The alternative, adding `-r requirements-assistant.txt`
to each caller, would have put the same list of files in four places to drift apart.

**Packaging globs instead of listing.** `collect_files()` picks up
`ROOT.glob("requirements*.txt")`, so a future requirements file is packaged automatically.
`package_demo.py` was refactored to expose `collect_files()` and `build_package()` so the
behaviour is testable without a subprocess; the CLI is unchanged and CI still calls it the
same way.

**A checkable invariant.** `scripts/check_install_consistency.py` resolves requirements
files the way pip does (following `-r` includes) and reports any installing path whose file
does not carry exact pins for the assistant packages. Run it directly for a pass/fail
summary; it exits non-zero on drift.

**Documentation matched to reality.** `docs/ollama_setup.md` drops the now-unnecessary
two-file install command and gains the path table above. `README.md` states that the single
install command brings the reviewed pins.

Changed files: `requirements.txt`, `requirements-assistant.txt`, `scripts/package_demo.py`,
`scripts/check_install_consistency.py` (new), `tests/test_install_consistency.py` (new),
`docs/ollama_setup.md`, `README.md`, this file.

## 4. Evidence

- **Full suite: 295 passed** (278 at the base commit plus 17 new). `scripts/package_demo.py`
  and `scripts/check_snapshot_checkout.py` both run clean.
- **Clean-venv resolution.** `pip install --dry-run --report` against `requirements.txt` in a
  throwaway venv resolves 56 packages, every declared package appears, and all seven reviewed
  pins match exactly: `ollama 0.6.2`, `httpx 0.28.1`, `httpcore 1.0.9`, `pydantic 2.13.5`,
  `pydantic-core 2.46.5`, `annotated-types 0.8.0`, `typing-inspection 0.4.4`.
- **The pin actually binds.** Resolving `-r requirements.txt` together with `httpx==0.27.2`
  now fails with `ResolutionImpossible: Cannot install httpx==0.27.2 and httpx==0.28.1`.
  With the include removed, the same request silently resolves `httpx` to `0.27.2`.
- **Honest nuance:** today's default resolution is *identical* with and without the include,
  because the pinned versions happen to be the current best candidates. The include does not
  change what you get today; it stops a future `httpx` or `pydantic` release from changing it
  silently. The conflict test above is what demonstrates the pin is in force.
- **Tests are behavioural, not string matching.** They assert on what a requirements file
  resolves to and on what the built archive contains. A negative-control test builds a
  deliberately inconsistent tree and asserts the checker fails on it, so the positive
  assertions cannot pass vacuously. Another test scans the shipped package's own text for
  requirements filenames and demands each is present in the archive.
- **Offline mechanism:** a synthetic nested requirements pair resolved under
  `pip install --dry-run --no-index --find-links <empty dir>` fails naming the package from
  the *inner* file, proving pip follows `-r` includes in offline mode. A test also asserts the
  setup script's offline and online branches install the same requirements file.
- **Core without the assistant:** a subprocess with `ollama` blocked at import builds a
  `Workspace` successfully and confirms `ollama` never enters `sys.modules`.

## 5. Not exercised, and remaining gaps

- **No real offline wheelhouse install.** The repository contains no `wheelhouse/`, so
  `pip install --no-index --find-links wheelhouse -r requirements.txt` was never run against a
  populated directory. Only the nested-include mechanism was proven offline. **Before relying
  on the offline path, rebuild the wheelhouse** — `pip download -r requirements.txt` now pulls
  the assistant closure too, and a wheelhouse created before this change will be missing those
  wheels and will fail with `--no-index`.
- **Windows installer not rebuilt or certified.** `build_offline_bundle.py`,
  `build_exe.py`, `package_setup_exe.py` and `basin_installer.iss` were read, not run.
- **`build_offline_bundle.py` inherits its environment.** It copies `.venv/Lib/site-packages`
  rather than installing, so a bundle built from a venv created before this change ships the
  old resolution. Run `Setup BASIN.cmd` or `pip install -r requirements.txt` first. This is a
  real gap that no test can close, because the script has no dependency step to assert on.
- **Resolution reflects PyPI on 2026-09-09.** There is no hash pinning, so nothing here
  protects against a republished artifact.
- **No vulnerability claim.** No advisory scan was run in this pass; see
  `docs/dependency_advisories_2026-09-09.md` for the September 9 review. `pip check` was not
  run and is not a vulnerability scan in any case.
- **No models, daemons, firewall or remote access** were touched.
- **Concurrent work.** The assistant model-filtering branch was not merged or inspected. If it
  changes any requirements file, re-run `python scripts/check_install_consistency.py`; the new
  tests will also fail loudly if a pin stops being exact.
- `basin_core/assistant.py`, `tests/test_security.py`, `tests/test_ollama_client.py`, `app.py`
  and the PDF/report modules were not modified.

## 6. Suggested board entries at integration

- Mark the installation-consistency work done, referencing this file.
- Open a follow-up for rebuilding and testing the wheelhouse and the offline bundle on the
  presentation machine, which remains part of B10 and SEC.5.
