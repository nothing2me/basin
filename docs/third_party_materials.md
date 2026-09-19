# Third-party materials

## Data

NOAA NCEI GHCN-Daily: https://doi.org/10.7289/V5D21VHZ. Documentation: https://www.ncei.noaa.gov/pub/data/ghcn/daily/readme.txt. Dataset version, retrieval time, URLs and hashes are in data/manifest.json. These are public federal meteorological observations, not BASIN-authored measurements; no endorsement is implied.

TWDB (Texas Water Development Board) reservoir storage/capacity data and TCEQ (Texas Commission on Environmental Quality) WAM parameter baselines are public state planning materials cited in `docs/methodology.md` and the export methodology. Original research bytes in `research/incoming/` and `research/sources/` are preserved for audit; the supplied city drought contingency plan PDF is retained for offline page-level verification only and is not redistributed.

## Code and packaged wheels

Pinned Python libraries are in requirements.txt. Bundled wheels retain upstream license/metadata files. Core libraries: Streamlit (Apache-2.0), NumPy, pandas and scikit-learn (BSD-style), Plotly.py (MIT). Native assistant runtime binding: llama-cpp-python (MIT). Consult distributions for authoritative notices and transitive dependencies. This document makes no new license grant for the team's own code.

## Optional AI model

The optional embedded assistant model is **Qwen2.5-3B-Instruct** (quantized GGUF), distributed under the **Qwen Research License** (Alibaba Cloud / Tongyi Lab). The weights (~2.1 GB) are **never bundled** in the repository, installer or source package; `scripts/fetch_model.py` downloads them on demand from the official Hugging Face source and records the license and SHA-256. The Qwen Research License permits non-commercial research use; commercial deployment would require the separate Qwen commercial license.

## Offline satellite basemap

`static/tiles/s2cloudless/` contains offline tiles from **Sentinel-2 cloudless by EOX IT Services GmbH**, distributed under **CC BY 4.0** (contains modified Copernicus Sentinel data; attribution is shown in the app and the download script). The previous **Esri World Imagery** cache was replaced in September 2026 because Esri's Terms of Use do not grant offline redistribution; no Esri tiles remain in the repository. Online fallback layers (`region_n_map.py`, `geo_map.py`) use the same EOX WMTS endpoint.

## Other

No event logos, contact details, event PDFs, raw survey responses or private notes are packaged. Event context is summarized, not reproduced.