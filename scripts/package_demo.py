"""Create a clean distributable; never include sessions, attachments, or credentials."""
from pathlib import Path
import argparse
import hashlib
import json
import subprocess
import zipfile

ROOT = Path(__file__).resolve().parents[1]

TOP_LEVEL_FILES = ["README.md", "LICENSE", "app.py", "basin_ui.py", "basin_theme.py",
                   "pytest.ini", ".gitattributes", "Start BASIN.cmd", "Setup BASIN.cmd",
                   "start_basin.sh", ".streamlit/config.toml"]
SOURCE_DIRECTORIES = ["basin_core", "scripts", "tests", "data", "docs", "assets"]
SOURCE_SUFFIXES = [".py", ".csv", ".json", ".md", ".ico", ".png"]


def reviewed_files(root, candidates):
    """Package tracked source only; do not sweep untracked private documents."""
    tracked = set(subprocess.check_output(
        ['git', 'ls-files', '-z'], cwd=root).decode('utf-8').split('\0'))
    result = []
    for path in candidates:
        relative = path.relative_to(root).as_posix()
        if relative not in tracked:
            continue
        if path.is_symlink() or not path.resolve().is_relative_to(root.resolve()):
            raise ValueError('Refusing package file outside repository: ' + relative)
        result.append(path)
    return result


def collect_files(root=ROOT):
    """Every tracked file the source package ships, as absolute paths."""
    files = [root / name for name in TOP_LEVEL_FILES]
    # Every requirements file, not a hand-maintained subset: requirements.txt includes
    # requirements-assistant.txt, and omitting an included file breaks setup in the
    # distributed package while leaving the repository working.
    files.extend(sorted(root.glob("requirements*.txt")))
    for directory in SOURCE_DIRECTORIES:
        if (root / directory).exists():
            files.extend(p for p in (root / directory).rglob("*")
                         if p.is_file() and "__pycache__" not in p.parts and p.suffix in SOURCE_SUFFIXES)
    return reviewed_files(root, files)


def build_package(root=ROOT, target=None, wheels=False):
    """Write the distributable archive and return its path."""
    files = collect_files(root)
    if wheels:
        found = list((root / "wheelhouse").glob("*.whl"))
        if not found:
            raise SystemExit("No wheels. Download requirements into wheelhouse first.")
        if any(p.is_symlink() or not p.resolve().is_relative_to(root.resolve()) for p in found):
            raise ValueError('Wheel path escapes repository')
        files = files + found
    if target is None:
        output = root / "output"
        output.mkdir(exist_ok=True)
        target = output / ("BASIN-demo-windows-py312.zip" if wheels else "BASIN-demo-source.zip")
    target = Path(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as archive:
        for file in files:
            archive.write(file, "BASIN/" + file.relative_to(root).as_posix())
        archive.writestr("BASIN/package-checksums.json", json.dumps(
            {f.relative_to(root).as_posix(): hashlib.sha256(f.read_bytes()).hexdigest() for f in files},
            indent=2))
    with zipfile.ZipFile(target) as archive:
        assert archive.testzip() is None
        names = archive.namelist()
        assert not any("/local/" in n or "/.env" in n or "/.venv/" in n or "credentials.toml" in n
                       or n.endswith(".gguf") or n.endswith(".bin") or "__pycache__" in n
                       for n in names)
    return target


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--wheels", action="store_true", help="Include downloaded Windows CPython 3.12 wheels")
    args = parser.parse_args()
    created = build_package(ROOT, wheels=args.wheels)
    print(f"Created {created} ({created.stat().st_size / 1024**2:.1f} MB)")
