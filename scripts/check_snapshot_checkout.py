"""Prove repository attributes preserve snapshot bytes in a fresh CRLF-configured clone."""
from pathlib import Path
import hashlib
import json
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def check():
    scratch = ROOT / "tmp"
    scratch.mkdir(exist_ok=True)
    root = Path(tempfile.mkdtemp(prefix="snapshot-checkout-", dir=scratch)).resolve()
    if not root.is_relative_to(scratch.resolve()):
        raise ValueError("Validation directory is outside the workspace scratch directory")
    source, target = root / "source", root / "clone"
    source.mkdir()
    for relative in (".gitattributes", "data/observations.csv", "data/manifest.json"):
        dest = source / relative
        dest.parent.mkdir(exist_ok=True)
        shutil.copy2(ROOT / relative, dest)
    def git(*args):
        return subprocess.run(["git", *args], check=True, capture_output=True, text=True).stdout.strip()
    git("init", "-q", str(source))
    git("-C", str(source), "config", "core.autocrlf", "true")
    git("-C", str(source), "add", ".")
    git("-C", str(source), "-c", "user.name=BASIN checkout test", "-c", "user.email=test@example.invalid",
        "commit", "-qm", "Snapshot checkout fixture")
    git("-c", "core.autocrlf=true", "clone", "-q", str(source), str(target))
    raw = (target / "data/observations.csv").read_bytes()
    expected = json.loads((target / "data/manifest.json").read_text())["sha256"]
    actual = hashlib.sha256(raw).hexdigest()
    if actual != expected or b"\r\n" in raw:
        raise ValueError("Fresh Windows-style checkout changed snapshot bytes")
    return {"verified": True, "sha256": actual, "clone": str(target),
            "attributes": git("-C", str(target), "check-attr", "eol", "--", "data/observations.csv")}


if __name__ == "__main__":
    print(json.dumps(check(), indent=2))
