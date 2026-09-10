"""Check that every installation path applies the same reviewed dependency pins.

BASIN has several entry points that install Python dependencies (the Windows setup
script, CI, the documented manual commands). Each one names a requirements file. If a
reviewed pin lives in a file that some of those paths never read, the pin is not actually
in force where it matters, and the repository can look correct while a distributed package
is broken.

This module resolves requirements files the way pip does — following ``-r`` includes — so
callers can assert on the resulting package set rather than on the text of any one
command. Run it directly for a pass/fail summary:

    python scripts/check_install_consistency.py
"""
from __future__ import annotations

import re
import sys
from pathlib import Path
from packaging.requirements import Requirement, InvalidRequirement

ROOT = Path(__file__).resolve().parents[1]

# Files whose text documents or performs an installation. Each is searched for the
# requirements files it installs; the assertion is about what those files resolve to.
INSTALL_PATHS = ("Setup BASIN.cmd", ".github/workflows/tests.yml", "README.md", "start_basin.sh")

# Packages the assistant boundary depends on. Pinning these is what makes the reviewed
# proxy/redirect/timeout behaviour reproducible; see docs/dependency_advisories_2026-09-09.md.
ASSISTANT_PACKAGES = ("ollama", "httpx", "httpcore", "pydantic", "pydantic-core",
                      "annotated-types", "typing-inspection")

_REQUIREMENT_FILE = re.compile(r"requirements[A-Za-z0-9_.-]*\.txt")
_INSTALL_TARGET = re.compile(r"-r\s+(requirements[A-Za-z0-9_.-]*\.txt)")


def normalise(name: str) -> str:
    return name.strip().lower().replace("_", "-")


def resolve_requirements(path: Path, _seen: set[Path] | None = None) -> dict[str, str]:
    """Resolve a requirements file into ``{package: specifier}``, following ``-r`` includes.

    Mirrors how pip expands a requirements file, so a caller can ask what an install of
    that file would actually pin without running pip.
    """
    path = Path(path)
    if not path.is_absolute():
        path = ROOT / path
    seen = _seen if _seen is not None else set()
    resolved = path.resolve()
    if resolved in seen:
        return {}
    seen.add(resolved)

    found: dict[str, str] = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.split("#")[0].strip()
        if not line:
            continue
        if line.startswith(("-r", "--requirement")):
            include = line.split(maxsplit=1)[1].strip()
            found.update(resolve_requirements(path.parent / include, seen))
            continue
        if line.startswith("-"):
            continue
        name = re.split(r"[=<>!~\[;]", line)[0]
        found[normalise(name)] = line
    return found


def requirements_files_referenced_by(text: str) -> set[str]:
    """Requirements filenames a document or script tells a reader to install."""
    return set(_REQUIREMENT_FILE.findall(text))


def install_targets(text: str) -> set[str]:
    """Requirements files an install command in ``text`` passes to pip via ``-r``."""
    return set(_INSTALL_TARGET.findall(text))


def unpinned(specs: dict[str, str], packages=ASSISTANT_PACKAGES) -> list[str]:
    """Packages from ``packages`` that are missing or not pinned to an exact version."""
    problems = []
    for package in packages:
        spec = specs.get(normalise(package))
        if spec is None:
            problems.append(f"{package}: absent")
        else:
            try:
                requirement = Requirement(spec)
                pins = list(requirement.specifier)
                exact = (normalise(requirement.name) == normalise(package)
                         and requirement.marker is None and len(pins) == 1
                         and pins[0].operator == "==" and "*" not in pins[0].version)
            except InvalidRequirement:
                exact = False
            if not exact:
                problems.append(f"{package}: not pinned ({spec})")
    return problems


def check(root: Path = ROOT) -> list[str]:
    """Return a list of problems; empty means every installation path is consistent."""
    problems: list[str] = []

    core = root / "requirements.txt"
    problems += [f"requirements.txt -> {issue}" for issue in unpinned(resolve_requirements(core))]

    for relative in INSTALL_PATHS:
        path = root / relative
        if not path.exists():
            problems.append(f"{relative}: missing")
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for target in install_targets(text):
            target_path = root / target
            if not target_path.exists():
                problems.append(f"{relative}: installs missing file {target}")
                continue
            for issue in unpinned(resolve_requirements(target_path)):
                problems.append(f"{relative} installs {target} -> {issue}")

    # Every requirements file a shipped instruction names must exist to be packaged.
    for relative in INSTALL_PATHS + ("docs/ollama_setup.md",):
        path = root / relative
        if not path.exists():
            continue
        for referenced in requirements_files_referenced_by(path.read_text(encoding="utf-8", errors="replace")):
            if not (root / referenced).exists():
                problems.append(f"{relative} references missing {referenced}")

    return problems


def main() -> int:
    problems = check()
    if problems:
        print("Installation consistency problems:")
        for problem in problems:
            print(f"  - {problem}")
        return 1
    resolved = resolve_requirements(ROOT / "requirements.txt")
    print(f"requirements.txt resolves to {len(resolved)} pinned packages; "
          f"all {len(ASSISTANT_PACKAGES)} assistant packages pinned exactly.")
    print("Every installation path applies the same pins.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
