"""Installation, packaging and dependency-pin consistency.

BASIN installs dependencies from several entry points. These tests assert on what a
requirements file *resolves to* and on what the distributable actually contains, rather
than on the text of any particular command, so the checks survive a reworded script.
"""
from __future__ import annotations

import re
import subprocess
import sys
import textwrap
import zipfile
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import check_install_consistency as consistency  # noqa: E402
import package_demo  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
REVIEWED_PINS = {
    "ollama": "0.6.2",
    "httpx": "0.28.1",
    "httpcore": "1.0.9",
    "pydantic": "2.13.5",
    "pydantic-core": "2.46.5",
    "annotated-types": "0.8.0",
    "typing-inspection": "0.4.4",
}


@pytest.fixture(scope="module")
def source_package(tmp_path_factory):
    """Build the real source distributable once and hand back its entry names."""
    target = tmp_path_factory.mktemp("package") / "BASIN-demo-source.zip"
    package_demo.build_package(ROOT, target=target)
    with zipfile.ZipFile(target) as archive:
        return target, archive.namelist()


# --------------------------------------------------------------------------------------
# The checker itself must be able to fail
# --------------------------------------------------------------------------------------

def test_checker_detects_a_path_that_skips_the_assistant_pins(tmp_path):
    """Negative control: without the include, the pins are not in force."""
    (tmp_path / "requirements.txt").write_text("altair==6.2.2\nollama==0.6.2\n", encoding="utf-8")
    (tmp_path / "requirements-assistant.txt").write_text("httpx==0.28.1\n", encoding="utf-8")
    (tmp_path / "Setup BASIN.cmd").write_text('pip install -r requirements.txt\n', encoding="utf-8")
    (tmp_path / ".github" / "workflows").mkdir(parents=True)
    (tmp_path / ".github/workflows/tests.yml").write_text("- run: pip install -r requirements.txt\n", encoding="utf-8")
    (tmp_path / "README.md").write_text("pip install -r requirements.txt\n", encoding="utf-8")
    (tmp_path / "start_basin.sh").write_text("pip install -r requirements.txt\n", encoding="utf-8")

    problems = consistency.check(tmp_path)
    assert problems, "a requirements.txt that does not include the assistant pins must fail"
    assert any("httpx" in problem for problem in problems)

    # Adding the include is what fixes it, with no version numbers duplicated.
    (tmp_path / "requirements.txt").write_text(
        "-r requirements-assistant.txt\naltair==6.2.2\nollama==0.6.2\n", encoding="utf-8")
    (tmp_path / "requirements-assistant.txt").write_text(
        "\n".join(f"{name}=={version}" for name, version in REVIEWED_PINS.items() if name != "ollama"),
        encoding="utf-8")
    assert consistency.check(tmp_path) == []


def test_checker_detects_a_range_pin(tmp_path):
    (tmp_path / "requirements.txt").write_text("ollama>=0.4.0\n", encoding="utf-8")
    problems = consistency.unpinned(consistency.resolve_requirements(tmp_path / "requirements.txt"))
    assert any("not pinned" in problem and "ollama" in problem for problem in problems)


def test_resolver_follows_includes_and_survives_a_cycle(tmp_path):
    (tmp_path / "a.txt").write_text("-r b.txt\nalpha==1.0\n", encoding="utf-8")
    (tmp_path / "b.txt").write_text("-r a.txt\nbeta==2.0\n", encoding="utf-8")
    resolved = consistency.resolve_requirements(tmp_path / "a.txt")
    assert resolved == {"alpha": "alpha==1.0", "beta": "beta==2.0"}


# --------------------------------------------------------------------------------------
# The repository's own installation paths
# --------------------------------------------------------------------------------------

def test_repository_is_consistent():
    assert consistency.check(ROOT) == []


def test_requirements_resolve_to_the_reviewed_pins():
    resolved = consistency.resolve_requirements(ROOT / "requirements.txt")
    for name, version in REVIEWED_PINS.items():
        assert resolved.get(name) == f"{name}=={version}", name


@pytest.mark.parametrize("relative", consistency.INSTALL_PATHS)
def test_every_install_path_resolves_to_the_same_pins(relative):
    """Whatever file a path installs must carry the reviewed pins, however it is worded."""
    text = (ROOT / relative).read_text(encoding="utf-8", errors="replace")
    targets = consistency.install_targets(text)
    if not targets:
        pytest.skip(f"{relative} does not invoke pip with a requirements file")
    for target in targets:
        resolved = consistency.resolve_requirements(ROOT / target)
        assert consistency.unpinned(resolved) == [], f"{relative} -> {target}"


def test_version_numbers_are_not_duplicated_across_requirements_files():
    """One package, one place. Duplicated lists are how pins drift apart."""
    seen: dict[str, list[str]] = {}
    for path in sorted(ROOT.glob("requirements*.txt")):
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.split("#")[0].strip()
            if not line or line.startswith("-"):
                continue
            name = consistency.normalise(re.split(r"[=<>!~\[;]", line)[0])
            seen.setdefault(name, []).append(path.name)
    duplicated = {name: files for name, files in seen.items() if len(files) > 1}
    assert duplicated == {}


def test_offline_and_online_setup_install_the_same_requirements():
    """The wheelhouse branch must not drift from the online branch."""
    text = (ROOT / "Setup BASIN.cmd").read_text(encoding="utf-8", errors="replace")
    assert "--no-index" in text and "wheelhouse" in text, "offline wheelhouse path must be preserved"
    install_lines = [line for line in text.splitlines() if "pip install" in line]
    assert len(install_lines) == 2, "expected one offline and one online install branch"
    targets = [consistency.install_targets(line) for line in install_lines]
    assert targets[0] == targets[1] == {"requirements.txt"}


def test_nested_requirements_are_honoured_with_no_index(tmp_path):
    """pip must follow the include even in the offline wheelhouse mode.

    Uses an empty find-links directory: the resolution fails, but the package it fails on
    proves pip read the nested file rather than only the outer one.
    """
    (tmp_path / "outer.txt").write_text("-r inner.txt\n", encoding="utf-8")
    (tmp_path / "inner.txt").write_text("basin-nested-probe==9.9.9\n", encoding="utf-8")
    empty = tmp_path / "wheelhouse"
    empty.mkdir()

    result = subprocess.run(
        [sys.executable, "-m", "pip", "install", "--dry-run", "--no-index",
         "--find-links", str(empty), "-r", str(tmp_path / "outer.txt")],
        capture_output=True, text=True,
    )
    assert result.returncode != 0
    assert "basin-nested-probe" in (result.stdout + result.stderr)


# --------------------------------------------------------------------------------------
# What the distributable actually contains
# --------------------------------------------------------------------------------------

def test_package_contains_every_requirements_file(source_package):
    _, names = source_package
    for path in sorted(ROOT.glob("requirements*.txt")):
        assert f"BASIN/{path.name}" in names, path.name


def test_package_contains_every_requirements_file_its_own_instructions_reference(source_package):
    """Scan the shipped text and demand each requirements file it names is present."""
    target, names = source_package
    referenced: set[str] = set()
    with zipfile.ZipFile(target) as archive:
        for name in names:
            if not name.endswith((".md", ".cmd", ".sh", ".txt", ".yml", ".py")):
                continue
            text = archive.read(name).decode("utf-8", "replace")
            referenced |= consistency.requirements_files_referenced_by(text)
    assert referenced, "the package should document how to install dependencies"
    for filename in sorted(referenced):
        assert f"BASIN/{filename}" in names, f"{filename} is referenced but not packaged"


def test_packaged_requirements_resolve_without_the_repository(source_package, tmp_path):
    """Extracted on its own, the package's requirements must still resolve completely."""
    target, _ = source_package
    with zipfile.ZipFile(target) as archive:
        for name in archive.namelist():
            if name.startswith("BASIN/requirements"):
                archive.extract(name, tmp_path)
    extracted = tmp_path / "BASIN"
    resolved = consistency.resolve_requirements(extracted / "requirements.txt")
    assert consistency.unpinned(resolved) == []
    for name, version in REVIEWED_PINS.items():
        assert resolved.get(name) == f"{name}=={version}", name


def test_package_still_excludes_private_material(source_package):
    _, names = source_package
    assert not any("/local/" in n or "/.env" in n or "/.venv/" in n or "credentials.toml" in n
                   for n in names)
    assert not any(n.endswith(".zip") for n in names)


# --------------------------------------------------------------------------------------
# The core must not need the optional client
# --------------------------------------------------------------------------------------

def test_core_imports_and_runs_without_the_ollama_package(tmp_path):
    """Simulate a machine where the optional client was never installed."""
    blocker = tmp_path / "sitecustomize.py"
    blocker.write_text(textwrap.dedent('''
        import sys

        class _Blocker:
            def find_spec(self, name, path=None, target=None):
                if name == "ollama" or name.startswith("ollama."):
                    raise ModuleNotFoundError("No module named ollama", name=name)
                return None

        sys.meta_path.insert(0, _Blocker())
    '''), encoding="utf-8")

    program = textwrap.dedent('''
        import sys
        from basin_core.data import CachedSource
        from basin_core.engine import ScenarioParams
        from basin_core.workspace import Workspace
        source = CachedSource()
        workspace = Workspace(source, ScenarioParams(tuple(source.daily.columns), candidates=10), size=2)
        assert workspace.scenarios
        assert "ollama" not in sys.modules
        print("core-ok")
    ''')
    result = subprocess.run(
        [sys.executable, "-c", program], capture_output=True, text=True,
        cwd=str(ROOT), env={**__import__("os").environ, "PYTHONPATH": f"{tmp_path}{__import__('os').pathsep}{ROOT}"},
    )
    assert "core-ok" in result.stdout, result.stderr[-2000:]
