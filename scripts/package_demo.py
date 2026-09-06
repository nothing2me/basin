"""Create a clean distributable; never include sessions, attachments, or credentials."""
from pathlib import Path
import argparse
import hashlib
import json
import zipfile

ROOT = Path(__file__).resolve().parents[1]

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--wheels", action="store_true", help="Include downloaded Windows CPython 3.12 wheels")
    args = parser.parse_args()
    files = [ROOT / name for name in ["README.md", "LICENSE", "app.py", "basin_ui.py", "pytest.ini", ".gitattributes", "requirements.txt", "Start BASIN.cmd", "Setup BASIN.cmd", "start_basin.sh", ".streamlit/config.toml"]]
    for directory in ["basin_core", "scripts", "tests", "data", "docs", "assets"]:
        if (ROOT / directory).exists():
            files.extend(p for p in (ROOT / directory).rglob("*") if p.is_file() and "__pycache__" not in p.parts and p.suffix in [".py", ".csv", ".json", ".md", ".ico", ".png"])
    if args.wheels:
        wheels = list((ROOT / "wheelhouse").glob("*.whl"))
        if not wheels:
            raise SystemExit("No wheels. Download requirements into wheelhouse first.")
        files.extend(wheels)
    output = ROOT / "output"
    output.mkdir(exist_ok=True)
    target = output / ("BASIN-demo-windows-py312.zip" if args.wheels else "BASIN-demo-source.zip")
    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as archive:
        for file in files:
            archive.write(file, "BASIN/" + file.relative_to(ROOT).as_posix())
        archive.writestr("BASIN/package-checksums.json", json.dumps({f.relative_to(ROOT).as_posix(): hashlib.sha256(f.read_bytes()).hexdigest() for f in files}, indent=2))
    with zipfile.ZipFile(target) as archive:
        assert archive.testzip() is None
        assert not any("/local/" in n or "/.env" in n or "/.venv/" in n or "credentials.toml" in n for n in archive.namelist())
    print(f"Created {target} ({target.stat().st_size / 1024**2:.1f} MB)")
