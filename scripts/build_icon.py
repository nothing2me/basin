"""Build exact BASIN wordmark and multi-resolution icon assets from the supplied logo."""
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
SOURCE = ASSETS / "basin-logo-source.png"


def build_icon():
    ASSETS.mkdir(exist_ok=True)
    if not SOURCE.exists():
        raise SystemExit(f"Missing source logo: {SOURCE}")

    source = Image.open(SOURCE).convert("RGBA")
    bounds = source.getbbox()
    if not bounds:
        raise SystemExit(f"Source logo has no visible pixels: {SOURCE}")

    # The transparent logo contains a white horizontal wordmark. Keep that
    # artwork exact and remove only transparent canvas around it.
    wordmark = source.crop(bounds)
    wordmark.save(ASSETS / "basin-logo.png", "PNG", optimize=True)

    # The leftmost square of the wordmark is the authored B mark. It remains
    # legible at taskbar and Explorer sizes where the full wordmark cannot.
    mark_size = wordmark.height
    mark = wordmark.crop((0, 0, mark_size, mark_size))
    img = mark.resize((512, 512), Image.Resampling.LANCZOS)

    png_path = ASSETS / "basin.png"
    img.resize((256, 256), Image.Resampling.LANCZOS).save(png_path, "PNG")

    # Save Windows multi-resolution .ico to both assets/ and root
    ico_sizes = [(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
    ico_path_assets = ASSETS / "basin.ico"
    ico_path_root = ROOT / "basin.ico"
    img.save(ico_path_assets, format="ICO", sizes=ico_sizes)
    img.save(ico_path_root, format="ICO", sizes=ico_sizes)

    print(f"Generated {ico_path_assets} ({ico_path_assets.stat().st_size} bytes)")
    print(f"Generated {ico_path_root} ({ico_path_root.stat().st_size} bytes)")
    print(f"Generated {png_path} ({png_path.stat().st_size} bytes)")
    print(f"Generated {ASSETS / 'basin-logo.png'} ({(ASSETS / 'basin-logo.png').stat().st_size} bytes)")


if __name__ == "__main__":
    build_icon()
