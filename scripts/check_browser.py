import sys
from pathlib import Path
ROOT = Path.cwd()
sys.path.insert(0, str(ROOT))

from basin_core.pdf_report import find_browser_executable, generate_pdf_report_with_status, _render_pdf_with_status

exe = find_browser_executable()
print("Found browser executable:", exe)
