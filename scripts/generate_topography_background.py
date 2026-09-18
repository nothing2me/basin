"""Generate BASIN's seamless topographic background texture."""

from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter
from scipy.ndimage import binary_dilation, gaussian_filter


WIDTH = 1800
HEIGHT = 1000
SEED = 20260917
OUTPUT = Path(__file__).resolve().parents[1] / "assets" / "topographic_contours.png"
BLURRED_OUTPUT = Path(__file__).resolve().parents[1] / "assets" / "topographic_contours_blurred.png"


def _periodic_terrain(height: int, width: int) -> np.ndarray:
    """Return a seamless, multi-scale terrain field."""
    rng = np.random.default_rng(SEED)
    terrain = np.zeros((height, width), dtype=np.float32)
    for sigma, weight in ((165, 1.0), (82, 0.52), (40, 0.22), (20, 0.08)):
        noise = rng.normal(size=(height, width)).astype(np.float32)
        terrain += weight * gaussian_filter(noise, sigma=sigma, mode="wrap")
    terrain -= terrain.mean()
    terrain /= max(float(terrain.std()), 1e-6)
    return np.tanh(terrain * 0.72)


def generate() -> None:
    terrain = _periodic_terrain(HEIGHT, WIDTH)
    low, high = np.quantile(terrain, (0.035, 0.965))
    phase = np.clip((terrain - low) / (high - low), 0, 1) * 16
    bands = np.floor(phase).astype(np.int16)

    horizontal = bands != np.roll(bands, 1, axis=1)
    vertical = bands != np.roll(bands, 1, axis=0)
    contour = horizontal | vertical

    highlight_horizontal = horizontal & (
        (bands % 4 == 0) | (np.roll(bands, 1, axis=1) % 4 == 0)
    )
    highlight_vertical = vertical & (
        (bands % 4 == 0) | (np.roll(bands, 1, axis=0) % 4 == 0)
    )
    highlight = highlight_horizontal | highlight_vertical

    # Fine supporting contours and slightly stronger index contours mirror a
    # printed elevation map without competing with the application content.
    highlight = binary_dilation(highlight, iterations=1)

    rgba = np.zeros((HEIGHT, WIDTH, 4), dtype=np.uint8)
    rgba[contour] = (21, 82, 108, 58)
    rgba[highlight] = (9, 139, 194, 145)

    image = Image.fromarray(rgba, mode="RGBA")
    image.save(OUTPUT, optimize=True)
    # A restrained optical softening keeps the contour field atmospheric
    # while preserving its recognizable terrain shapes behind dense UI.
    softened = image.filter(ImageFilter.GaussianBlur(radius=0.9))
    softened = softened.quantize(
        colors=64,
        method=Image.Quantize.FASTOCTREE,
        dither=Image.Dither.NONE,
    ).convert("RGBA")
    softened.save(BLURRED_OUTPUT, optimize=True)
    print(f"Generated {OUTPUT} ({OUTPUT.stat().st_size:,} bytes)")
    print(f"Generated {BLURRED_OUTPUT} ({BLURRED_OUTPUT.stat().st_size:,} bytes)")


if __name__ == "__main__":
    generate()
