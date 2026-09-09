"""Download and cryptographically verify pinned Qwen2.5-3B-Instruct GGUF weights.

This script fetches the exact official GGUF quantization from Hugging Face,
verifies its SHA-256 integrity against the pinned manifest, and saves it
to the models/ directory for embedded local inference.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys
import time
import urllib.request

ROOT = Path(__file__).resolve().parent.parent
MODELS_DIR = ROOT / "models"

MODEL_REPO = "Qwen/Qwen2.5-3B-Instruct-GGUF"
MODEL_REVISION = "7dabda4d13d513e3e842b20f0d435c732f172cbe"
MODEL_FILENAME = "qwen2.5-3b-instruct-q4_k_m.gguf"
MODEL_SHA256 = "626b4a6678b86442240e33df819e00132d3ba7dddfe1cdc4fbb18e0a9615c62d"
MODEL_BYTES = 2104932768
MODEL_LICENSE = "Qwen Research License"
DOWNLOAD_URL = f"https://huggingface.co/{MODEL_REPO}/resolve/{MODEL_REVISION}/{MODEL_FILENAME}"


def fetch_model(force: bool = False) -> Path:
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    target_path = MODELS_DIR / MODEL_FILENAME
    manifest_path = MODELS_DIR / "manifest.json"

    manifest_data = {
        "repo": MODEL_REPO,
        "revision": MODEL_REVISION,
        "filename": MODEL_FILENAME,
        "sha256": MODEL_SHA256,
        "size_bytes": MODEL_BYTES,
        "license": MODEL_LICENSE,
        "quantization": "Q4_K_M",
        "format": "GGUF",
        "chat_template": "qwen",
    }

    if target_path.exists() and not force:
        print(f"Checking existing model at {target_path}...")
        hasher = hashlib.sha256()
        with target_path.open("rb") as f:
            while chunk := f.read(1024 * 1024):
                hasher.update(chunk)
        digest = hasher.hexdigest()
        if digest == MODEL_SHA256:
            print(f"Verified existing weights ({digest[:12]}... == {MODEL_SHA256[:12]}...).")
            manifest_path.write_text(json.dumps(manifest_data, indent=2), encoding="utf-8")
            return target_path
        else:
            print(f"Existing file SHA mismatch ({digest} != {MODEL_SHA256}), re-downloading...")

    tmp_path = MODELS_DIR / f"{MODEL_FILENAME}.tmp"
    print(f"Downloading {MODEL_FILENAME} from {DOWNLOAD_URL}...")
    req = urllib.request.Request(DOWNLOAD_URL, headers={"User-Agent": "BASIN-Model-Fetcher/1.0"})

    hasher = hashlib.sha256()
    downloaded = 0
    start_time = time.time()
    last_report = start_time

    with urllib.request.urlopen(req) as resp, tmp_path.open("wb") as out_file:
        total = int(resp.headers.get("Content-Length", MODEL_BYTES))
        while chunk := resp.read(1024 * 512):
            out_file.write(chunk)
            hasher.update(chunk)
            downloaded += len(chunk)
            now = time.time()
            if now - last_report >= 3.0:
                pct = (downloaded / total) * 100
                mb = downloaded / (1024 * 1024)
                total_mb = total / (1024 * 1024)
                speed = mb / (now - start_time) if now > start_time else 0
                print(f"Progress: {mb:.1f}/{total_mb:.1f} MB ({pct:.1f}%) - {speed:.1f} MB/s")
                last_report = now

    actual_sha = hasher.hexdigest()
    if actual_sha != MODEL_SHA256:
        tmp_path.unlink(missing_ok=True)
        raise ValueError(f"Integrity check failed: expected {MODEL_SHA256}, got {actual_sha}")

    if tmp_path.stat().st_size != MODEL_BYTES:
        tmp_path.unlink(missing_ok=True)
        raise ValueError(f"Size mismatch: expected {MODEL_BYTES} bytes, got {tmp_path.stat().st_size}")

    if target_path.exists():
        target_path.unlink()
    tmp_path.rename(target_path)
    manifest_path.write_text(json.dumps(manifest_data, indent=2), encoding="utf-8")

    elapsed = time.time() - start_time
    print(f"Downloaded and verified {MODEL_FILENAME} in {elapsed:.1f}s (SHA: {actual_sha}).")
    return target_path


if __name__ == "__main__":
    force_flag = "--force" in sys.argv
    try:
        path = fetch_model(force=force_flag)
        print(f"SUCCESS: Model ready at {path}")
    except Exception as err:
        print(f"ERROR: {err}", file=sys.stderr)
        sys.exit(1)
