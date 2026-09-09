# Dependency advisory review — September 9, 2026

Scope: BASIN's declared Python dependencies, the newly pinned optional assistant closure,
and the packages actually installed in this repository's `.venv`. Baseline commit
`3dd1916`. This is an advisory-database review, not a penetration test, code audit or
supply-chain attestation.

## How the scan was run

| | |
|---|---|
| Tool | `pip-audit` 2.10.1, installed in a throwaway venv (`tmp/audit-venv`) so the project environment was not modified by the scanner |
| Advisory sources | PyPI advisory database (pip-audit default) **and** OSV (`-s osv`), run separately as a cross-check |
| Scan date | 2026-09-09, 19:57–20:10 UTC |
| Platform | Windows-11-10.0.26200-SP0, CPython 3.12.14 |
| Network | Both services were reachable; results reflect their databases as of the scan date |

Commands, exactly as run:

```bash
tmp/audit-venv/Scripts/python.exe -m pip_audit -r requirements.txt            --progress-spinner off
tmp/audit-venv/Scripts/python.exe -m pip_audit -r requirements-build.txt      --progress-spinner off
tmp/audit-venv/Scripts/python.exe -m pip_audit -r requirements-assistant.txt  --progress-spinner off
.venv/Scripts/python.exe -m pip freeze > tmp/audit/freeze_after.txt
tmp/audit-venv/Scripts/python.exe -m pip_audit -r tmp/audit/freeze_after.txt  --progress-spinner off

# Cross-check against the second source
tmp/audit-venv/Scripts/python.exe -m pip_audit -r requirements.txt            -s osv --progress-spinner off
tmp/audit-venv/Scripts/python.exe -m pip_audit -r requirements-assistant.txt  -s osv --progress-spinner off
tmp/audit-venv/Scripts/python.exe -m pip_audit -r tmp/audit/freeze_after.txt  -s osv --progress-spinner off
```

## Scope and results

Declared requirements and the installed environment are reported separately, because they
are not the same set: the installed venv also carries test and build tooling, and a
requirements file describes what a fresh install *would* resolve rather than what is here.

| Scope | Source file | Packages | PyPI service | OSV service |
|---|---|---|---|---|
| Declared core | `requirements.txt` | 50 | No known vulnerabilities | No known vulnerabilities |
| Declared build-only | `requirements-build.txt` | 3 | No known vulnerabilities | not run |
| Declared assistant closure | `requirements-assistant.txt` | 6 | No known vulnerabilities | No known vulnerabilities |
| Installed environment | `pip freeze` of `.venv` | 55 resolved | No known vulnerabilities | No known vulnerabilities |

No advisories were returned for any scope by either service on the scan date.

## Findings

Nothing was found by the databases. The findings below come from the compatibility
testing done alongside the scan and are the actionable items.

### A-1 — The remote-model guards in `check_ollama()` cannot fire (medium)

`basin_core/assistant.py` filters listed models with
`not getattr(m, "remote_host", None) and not getattr(m, "remote_model", None)`.

Every tested client release (0.4.0, 0.4.9, 0.5.4, 0.6.2) parses list responses into
pydantic models whose field set is `{details, digest, model, modified_at, size}` and whose
`model_config` does not allow extra fields, so a daemon returning `remote_host` has it
dropped during parsing. Both guards therefore evaluate against `None` on real data and
never exclude anything.

`tests/test_security.py::test_cloud_models_excluded_and_exact_tag_selected` passes because
it feeds `SimpleNamespace` objects, where `getattr` does find the attribute. The mock and
the real client disagree.

The control that does work is the `"cloud"` substring check in `local_model()`.

**Recommended:** decide whether remote-model exclusion is a requirement. If it is, filter
on the raw response payload rather than the parsed model, and change the mocked test to
use real `ollama.ListResponse` objects. Left unchanged here to stay inside this task's
scope; pinned as observed behaviour by
`tests/test_ollama_client.py::test_remote_fields_are_dropped_by_the_real_client`.

### A-2 — The assistant's transitive dependencies were unpinned (fixed here)

`ollama>=0.4.0` allowed any client from 0.4.0 to 0.6.2, and its dependencies resolved
freshly on every install. `httpx` and `pydantic` — the packages that actually implement
the proxy, redirect and timeout behaviour BASIN's security posture depends on — were
therefore whatever pip happened to pick.

**Fixed:** `requirements.txt` now pins `ollama==0.6.2`, and `requirements-assistant.txt`
pins the closure (`httpx==0.28.1`, `httpcore==1.0.9`, `pydantic==2.13.5`,
`pydantic-core==2.46.5`, `annotated-types==0.8.0`, `typing-inspection==0.4.4`). Installing
these into the project venv upgraded nothing that was already present.

### A-3 — Pinning 0.4.0 would have held back `httpx` (informational)

`ollama==0.4.0` declares `httpx>=0.27.0,<0.28.0`; 0.4.9 and later relax it to
`httpx>=0.27`. Pinning the floor of the old range would have capped `httpx` below 0.28 for
everyone installing the assistant, which is the opposite of what a security pin should do.

### A-4 — `pip check` is not a vulnerability scan (informational)

The September 8 security review recorded a clean `pip check`. That command only reports
broken or inconsistent installed requirements. It consults no advisory database and must
not be cited as evidence of vulnerability status. This document is the first advisory
review for BASIN.

## Limitations

- **Absence of advisories is not absence of vulnerabilities.** Both databases only know
  what has been reported and published. A clean result dates from the scan date and says
  nothing about unreported or newly disclosed issues.
- **Declared versus installed.** The requirements scans audit version strings, not the
  artifacts a future install would fetch. No hash pinning is in place, so these files do
  not protect against a republished or substituted artifact.
- **No non-Python scope.** The Ollama service itself is a separate native application and
  is not covered by any Python advisory database. Neither is `BASIN.exe`, the bundled
  browser used for PDF rendering, or the OS.
- **No model scope.** No model weights were downloaded and no model was scanned. Model
  provenance and behaviour are outside this review.
- **Client boundary only.** The compatibility tests constrain BASIN's HTTP client. They do
  not observe what the Ollama daemon does with its own outbound connections; that needs
  real traffic observation on the presentation machine (SEC.4, still open).
- The scanner ran in its own venv, so its own dependencies are not part of the audited
  scope.

## Re-running this review

```bash
python -m venv tmp/audit-venv && tmp/audit-venv/Scripts/python.exe -m pip install pip-audit
tmp/audit-venv/Scripts/python.exe -m pip_audit -r requirements.txt --progress-spinner off
```

Re-run before the September 22 showcase and whenever a dependency changes. Record the new
date and result rather than editing this one; a stale scan date is itself a finding.
