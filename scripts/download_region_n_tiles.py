"""Download and verify offline satellite tiles for Region N.

Fetches Esri World Imagery tiles covering the 11-county TWDB Region N
bounding box for zoom levels 6 through 11, saving them into
``static/tiles/World_Imagery/{z}/{y}/{x}.jpg`` for offline Streamlit serving.
"""
from __future__ import annotations

import concurrent.futures
import math
from pathlib import Path
import sys
import time
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "static/tiles/World_Imagery"

# Region N bounds: [west, south, east, north]
BOUNDS = (-98.80361, 26.59791, -96.71357, 28.78654)
ESRI_URL_TEMPLATE = "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"


def deg2num(lat_deg: float, lon_deg: float, zoom: int) -> tuple[int, int]:
    """Convert lat/lon degrees to Web Mercator tile x and y indices."""
    lat_rad = math.radians(lat_deg)
    n = 2.0 ** zoom
    xtile = int((lon_deg + 180.0) / 360.0 * n)
    ytile = int((1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * n)
    return xtile, ytile


def compute_tiles(min_zoom: int = 6, max_zoom: int = 11) -> list[tuple[int, int, int]]:
    """Compute all (z, y, x) tile coordinates covering Region N."""
    west, south, east, north = BOUNDS
    tiles: list[tuple[int, int, int]] = []
    for z in range(min_zoom, max_zoom + 1):
        x1, y2 = deg2num(south, west, z)
        x2, y1 = deg2num(north, east, z)
        min_x, max_x = min(x1, x2), max(x1, x2)
        min_y, max_y = min(y1, y2), max(y1, y2)
        # Margin for smooth panning at regional overview zoom levels
        if z <= 9:
            min_x -= 1
            max_x += 1
            min_y -= 1
            max_y += 1
        for x in range(min_x, max_x + 1):
            for y in range(min_y, max_y + 1):
                tiles.append((z, y, x))
    return tiles


def fetch_tile(tile: tuple[int, int, int], output_dir: Path = OUTPUT_DIR) -> tuple[tuple[int, int, int], int, str]:
    z, y, x = tile
    tile_file = output_dir / str(z) / str(y) / f"{x}.jpg"
    if tile_file.exists() and tile_file.stat().st_size > 500:
        return tile, tile_file.stat().st_size, "cached"

    tile_file.parent.mkdir(parents=True, exist_ok=True)
    url = ESRI_URL_TEMPLATE.format(z=z, y=y, x=x)
    req = urllib.request.Request(url, headers={"User-Agent": "BASIN-Offline-Cacher/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = resp.read()
            if len(data) < 100:
                return tile, 0, "empty"
            tile_file.write_bytes(data)
            return tile, len(data), "downloaded"
    except Exception as exc:
        return tile, 0, f"error: {exc}"


def download_all_tiles(max_workers: int = 16) -> dict[str, int]:
    tiles = compute_tiles(min_zoom=6, max_zoom=11)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Preparing to sync {len(tiles)} satellite tiles for Region N into {OUTPUT_DIR}...")

    t0 = time.time()
    results = {"cached": 0, "downloaded": 0, "failed": 0, "bytes": 0}

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        for tile, size, status in executor.map(fetch_tile, tiles):
            if status == "cached":
                results["cached"] += 1
                results["bytes"] += size
            elif status == "downloaded":
                results["downloaded"] += 1
                results["bytes"] += size
            else:
                results["failed"] += 1
                print(f"  Warning: failed {tile}: {status}", file=sys.stderr)

    duration = time.time() - t0
    mb = results["bytes"] / (1024 * 1024)
    print(f"Finished in {duration:.2f}s: {results['downloaded']} downloaded, "
          f"{results['cached']} already cached, {results['failed']} failed. "
          f"Total disk size: {mb:.2f} MB")
    return results


if __name__ == "__main__":
    download_all_tiles()
