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

# The optional native runtime for embedded Qwen lives in its own hash-locked file, installed
# only by scripts/install_native_runtime.py; see docs/native_runtime_handoff.md.
NATIVE_REQUIREMENTS = "requirements-native.txt"
NATIVE_INSTALLER = "scripts/install_native_runtime.py"
NATIVE_PACKAGES = ("llama-cpp-python",)
NATIVE_SOURCES = ("https://abetlen.github.io/llama-cpp-python/whl/cpu",)

_REQUIREMENT_FILE = re.compile(r"requirements[A-Za-z0-9_.-]*\.txt")
_INSTALL_TARGET = re.compile(r"-r\s+(requirements[A-Za-z0-9_.-]*\.txt)")
_COMMENT = re.compile(r"(^|\s)#.*$")
_SHA256_OPTION = re.compile(r"--hash[=\s]sha256:[0-9a-f]{64}(\s|$)")


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
    for line in logical_lines(path):
        if line.startswith(("-r", "--requirement")):
            include = line.split(maxsplit=1)[1].strip()
            found.update(resolve_requirements(path.parent / include, seen))
            continue
        if line.startswith("-"):
            continue
        spec = requirement_spec(line)
        found[requirement_name(spec)] = spec
    return found


def logical_lines(path: Path) -> list[str]:
    """Non-empty lines as pip reads them: comments dropped, backslash continuations joined."""
    lines: list[str] = []
    buffer = ""
    for raw in Path(path).read_text(encoding="utf-8").splitlines():
        line = _COMMENT.sub("", raw).rstrip()
        if line.endswith("\\"):
            buffer += line[:-1] + " "
            continue
        line = (buffer + line).strip()
        buffer = ""
        if line:
            lines.append(line)
    if buffer.strip():
        lines.append(buffer.strip())
    return lines


def requirement_spec(line: str) -> str:
    """The requirement itself, without per-requirement options such as ``--hash``."""
    return re.split(r"\s+--", line, maxsplit=1)[0].strip()


def requirement_name(spec: str) -> str:
    return normalise(re.split(r"[=<>!~\[;@\s]", spec)[0])


def native_problems(root: Path = ROOT) -> list[str]:
    """Rules for the optional native-runtime file.

    It must be additive (no includes, nothing also pinned by the core), exact, hash-locked
    and binary-only, and may only name the reviewed upstream wheel index. Hash-locking is
    what stops that optional install from changing any core package.
    """
    name = NATIVE_REQUIREMENTS
    path = root / name
    if not path.exists():
        return [f"{name}: missing"]
    problems: list[str] = []
    lines = logical_lines(path)
    options = [line for line in lines if line.startswith("-")]
    requirements = [line for line in lines if not line.startswith("-")]

    if "--require-hashes" not in options:
        problems.append(f"{name}: --require-hashes missing")
    if not any(re.fullmatch(r"--only-binary[=\s]+:all:", option) for option in options):
        problems.append(f"{name}: --only-binary :all: missing (a source build needs a C/C++ toolchain)")
    for option in options:
        if re.match(r"(-r|--requirement|-c|--constraint|-e|--editable|--trusted-host)\b", option):
            problems.append(f"{name}: option not allowed in the native file ({option})")
        source = re.match(r"(--extra-index-url|--index-url|-i|--find-links|-f)[=\s]+(\S+)", option)
        if source and source.group(2).rstrip("/") not in NATIVE_SOURCES:
            problems.append(f"{name}: unreviewed package source {source.group(2)}")

    specs: dict[str, str] = {}
    for line in requirements:
        spec = requirement_spec(line)
        package = requirement_name(spec)
        specs[package] = spec
        if not _SHA256_OPTION.search(line):
            problems.append(f"{name}: {package} has no --hash=sha256 pin")
        problems += [f"{name} -> {issue}" for issue in unpinned({package: spec}, packages=[package])]
    problems += [f"{name} -> {package}: absent" for package in NATIVE_PACKAGES
                 if normalise(package) not in specs]

    core = resolve_requirements(root / "requirements.txt") if (root / "requirements.txt").exists() else {}
    for package in sorted(set(specs) & set(core)):
        problems.append(f"{name}: {package} is also pinned by requirements.txt; keep one version list")
    return problems


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

    # The optional native file is checked whenever it exists or an installation path uses it.
    mentions_native = any(
        (root / relative).exists()
        and re.search(r"requirements-native\.txt|install_native_runtime\.py",
                      (root / relative).read_text(encoding="utf-8", errors="replace"))
        for relative in INSTALL_PATHS)
    if (root / NATIVE_REQUIREMENTS).exists() or mentions_native:
        problems += native_problems(root)
        if mentions_native and not (root / NATIVE_INSTALLER).exists():
            problems.append(f"{NATIVE_INSTALLER}: missing")

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
    if (ROOT / NATIVE_REQUIREMENTS).exists():
        native = resolve_requirements(ROOT / NATIVE_REQUIREMENTS)
        print(f"{NATIVE_REQUIREMENTS} (optional) pins {len(native)} packages, each exact, "
              "hash-locked and binary-only, with no overlap with requirements.txt.")
    print("Every installation path applies the same pins.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
