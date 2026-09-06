"""Generate professional multi-resolution Windows .ico and PNG brand assets for BASIN."""
from pathlib import Path
import math
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"


def build_icon():
    ASSETS.mkdir(exist_ok=True)
    size = 512
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # 1. Outer deep spruce/slate circular disc container with layered border
    pad = 16
    draw.ellipse((pad, pad, size - pad, size - pad), fill="#0f2d29", outline="#1c4740", width=8)

    # 2. Concentric bathymetric reservoir contour tiers (representing elevation/depth)
    draw.chord((44, 44, size - 44, size - 44), start=30, end=150, fill="#087e8b", outline="#2098a6", width=5)
    draw.chord((76, 76, size - 76, size - 76), start=35, end=145, fill="#0d9488", outline="#2dd4bf", width=4)
    draw.chord((110, 110, size - 110, size - 110), start=40, end=140, fill="#14b8a6")

    # 3. Dynamic water wave contour in the bottom reservoir pool
    wave_pts = []
    for x in range(96, size - 96, 4):
        y = 330 + math.sin((x - 96) / 38.0) * 12
        wave_pts.append((x, y))
    wave_pts.extend([(size - 96, 420), (96, 420)])
    draw.polygon(wave_pts, fill="#0284c7")

    # 4. Stylized Golden Amber Rainfall Droplet (representing precipitation intelligence)
    drop_x = 256
    drop_top_y = 100
    drop_bottom_y = 250
    drop_r = 55
    # Bulb of the drop
    draw.ellipse((drop_x - drop_r, drop_bottom_y - drop_r, drop_x + drop_r, drop_bottom_y + drop_r),
                 fill="#cc9145", outline="#f59e0b", width=5)
    # Tapered tip of the drop
    tip_pts = [(drop_x, drop_top_y), (drop_x - drop_r + 6, drop_bottom_y - 10), (drop_x + drop_r - 6, drop_bottom_y - 10)]
    draw.polygon(tip_pts, fill="#cc9145")
    draw.line([tip_pts[0], tip_pts[1]], fill="#f59e0b", width=5)
    draw.line([tip_pts[0], tip_pts[2]], fill="#f59e0b", width=5)

    # Specular light highlight on the droplet
    draw.ellipse((drop_x - 30, drop_bottom_y - 24, drop_x - 12, drop_bottom_y + 8), fill="#fef08a")

    # 5. Accent arc ring representing compound concurrence
    draw.arc((120, 120, size - 120, size - 120), start=195, end=345, fill="#5eead4", width=4)

    # Save PNG representation
    png_path = ASSETS / "basin.png"
    img.resize((256, 256), Image.Resampling.LANCZOS).save(png_path, "PNG")

    # Save Windows multi-resolution .ico to both assets/ and root
    ico_sizes = [(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
    ico_path_assets = ASSETS / "basin.ico"
    ico_path_root = ROOT / "basin.ico"
    img.resize((256, 256), Image.Resampling.LANCZOS).save(ico_path_assets, format="ICO", sizes=ico_sizes)
    img.resize((256, 256), Image.Resampling.LANCZOS).save(ico_path_root, format="ICO", sizes=ico_sizes)

    print(f"Generated {ico_path_assets} ({ico_path_assets.stat().st_size} bytes)")
    print(f"Generated {ico_path_root} ({ico_path_root.stat().st_size} bytes)")
    print(f"Generated {png_path} ({png_path.stat().st_size} bytes)")


if __name__ == "__main__":
    build_icon()
