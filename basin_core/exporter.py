from __future__ import annotations

import hashlib
import importlib.metadata
import io
import json
import zipfile

import numpy as np
import pandas as pd

from basin_core import __version__
from basin_core.data import CachedSource, ROOT
from basin_core.engine import Reference


def dumps(value):
    return json.dumps(value, indent=2, allow_nan=False).encode()


def generate_brief(workspace, accepted) -> str:
    rows = []
    for s in accepted:
        f = s.features
        p = s.provenance
        def_mm = f["deficit_mm"]
        def_in = def_mm / 25.4
        profile = getattr(s, "cluster_name", f"Group {s.cluster}")
        exceeded = "Yes" if f.get("beyond_rainfall_reference") else "No"
        rows.append(f"| {s.id} | r{s.revision} | {profile} | {f['duration_days']}d | {def_mm:.1f} mm | {def_in:.2f} in | {f['concurrence']:.1%} | {exceeded} | {p.get('source_start')} to {p.get('source_end')} |")
    table_text = "\n".join(rows)
    return f"""# BASIN -- Hydrologist Handoff Brief & Engineering Specification
**Run Identifier:** `{workspace.id}`  
**Created:** `{workspace.created_at}`  
**Software Version:** BASIN v{__version__}  

---

## 1. Executive Summary & Purpose
This handoff brief accompanies an auditable meteorological drought scenario packet prepared for professional hydrologic review. The scenarios prioritize compound rainfall deficits across key regional supply indicators for the Coastal Bend / Texas Region N water planning area.

* **Target Application:** Professional evaluation through Texas Water Availability Models (WAM / WRAP) or reservoir balance models (e.g. Corpus Christi Water Supply Model for Lake Corpus Christi, Choke Canyon Reservoir, and Lake Texana).
* **Community Decision Context:** Prioritized by local water district stakeholders to focus scarce engineering consulting resources on drought patterns matching local community risk tolerance, high-demand summer timing, and multi-basin concurrence.
* **Scope Boundary:** These are meteorological rainfall-stress scenarios (expressed in daily mm/day). They represent **precipitation stress tests**, not streamflow forecasts or hydrologic firm yield determinations. Official engineering analyses must be conducted by or under the supervision of a licensed Professional Engineer (P.E.).

---

## 2. Community Priority Configuration
The shortlist was evaluated from `{len(workspace.scenarios)}` candidate scenarios using the following stakeholder weights:
* **Severity (Historical Percentile):** {workspace.weights.get('severity', 0)}%
* **Duration:** {workspace.weights.get('duration', 0)}%
* **Multi-Basin Spatial Concurrence:** {workspace.weights.get('concurrence', 0)}%
* **Peak Summer Timing (Jun-Sep):** {workspace.weights.get('season', 0)}%

---

## 3. Approved Scenario Specifications
The following {len(accepted)} scenario revisions were formally reviewed, refined, and approved for expert evaluation:

| Scenario ID | Revision | Profile | Duration | Net Deficit (mm) | Net Deficit (in) | Concurrence | Ref Exceeded? | Source Baseline Window |
| :--- | :---: | :--- | :---: | :---: | :---: | :---: | :---: | :--- |
{table_text}

---

## 4. Modeling Work Order & WAM Translation Guidance
For consulting engineers translating these scenarios into Texas WAM / WRAP inputs:
1. **Source Window Alignment:** Each scenario is anchored to an intact, synchronized historical observation window (`source_start` to `source_end`). 
2. **Sub-Basin Translation:** Tabulated daily precipitation series in `daily_rainfall.csv` provide station-specific daily totals and retention factors. Apply the corresponding monthly retention percentages to naturalized streamflow files (`.DAT`) for the respective sub-basins (Nueces River above Lake Corpus Christi, Frio River above Choke Canyon, and Navidad River above Lake Texana).
3. **Audit Verification:** The mathematical integrity of this bundle can be verified offline from the repository:
   ```bash
   python scripts/replay_bundle.py <bundle_path.zip>
   ```

---
*Provisional regional station proxies (USW00012924, USW00012912, USW00012921) shown for methodology demonstration. Catchment gauge calibration required for operational compliance.*
"""


def export_bundle(workspace, include_notes=False) -> bytes:
    accepted = workspace.exportable()
    rows, summaries = [], []
    for s in accepted:
        frame = s.series.rename_axis("date").reset_index().melt(id_vars="date", var_name="station_id", value_name="precip_mm")
        frame["scenario_id"], frame["revision"], frame["units"] = s.id, s.revision, "mm/day"
        rows.append(frame)
        summaries.append({"scenario_id": s.id, "revision": s.revision, "priority_score": s.score,
                          **{k: v for k, v in s.features.items() if not isinstance(v, dict)}})
    files = {"daily_rainfall.csv": pd.concat(rows).to_csv(index=False, lineterminator="\n").encode(),
             "shortlist.csv": pd.DataFrame(summaries).to_csv(index=False, lineterminator="\n").encode(),
             "audit.json": dumps(workspace.record(include_notes)),
             "Hydrologist_Handoff_Brief.md": generate_brief(workspace, accepted).encode("utf-8"),
             "snapshot/observations.csv": workspace.source.raw,
             "snapshot/manifest.json": dumps(workspace.source.manifest),
             "methodology.md": (ROOT / "docs/methodology.md").read_bytes(),
             "README.txt": b"BASIN rainfall scenarios for expert review. Historical dates label scenario days, not forecasts.\nVerify offline from the BASIN checkout: python scripts/replay_bundle.py path/to/bundle.zip\nPrivate notes are excluded unless explicitly opted in. Station proxies are provisional; no hydrologic yield or drought-of-record claim.\n"}
    manifest = {"schema_version": "1.0", "basin_version": __version__, "run_id": workspace.id,
                "accepted_ids": [s.id for s in accepted], "private_notes_included": include_notes,
                "software": {p: importlib.metadata.version(p) for p in ["numpy", "pandas", "scikit-learn", "streamlit"]},
                "files": {name: hashlib.sha256(payload).hexdigest() for name, payload in files.items()}}
    files["bundle_manifest.json"] = dumps(manifest)
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, payload in files.items():
            archive.writestr(name, payload)
    return buffer.getvalue()


def verify_bundle(payload: bytes) -> dict:
    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        if sum(f.file_size for f in archive.infolist()) > 100_000_000:
            raise ValueError("Bundle is too large")
        manifest = json.loads(archive.read("bundle_manifest.json"))
        for name, digest in manifest["files"].items():
            if hashlib.sha256(archive.read(name)).hexdigest() != digest:
                raise ValueError(f"Checksum mismatch: {name}")
        source = CachedSource(raw=archive.read("snapshot/observations.csv"), manifest=json.loads(archive.read("snapshot/manifest.json")))
        audit = json.loads(archive.read("audit.json"))
        reference = Reference(source, audit["params"]["stations"])
        rainfall = pd.read_csv(io.BytesIO(archive.read("daily_rainfall.csv")), parse_dates=["date"])
        if set(rainfall.scenario_id) != set(manifest["accepted_ids"]):
            raise ValueError("Exported scenario list mismatch")
        for record in audit["scenarios"]:
            if record["id"] not in manifest["accepted_ids"]:
                continue
            if record["status"] != "accepted" or record["revision"] != record["approved_revision"]:
                raise ValueError("Unapproved scenario in export")
            rows = rainfall[rainfall.scenario_id.eq(record["id"])]
            if not rows.revision.eq(record["revision"]).all() or not rows.units.eq("mm/day").all():
                raise ValueError("Revision or units mismatch")
            series = rows.pivot(index="date", columns="station_id", values="precip_mm")[reference.stations]
            p = record["provenance"]
            original = source.select(reference.stations).loc[p["source_start"]:p["source_end"]]
            replay = original * pd.Series(p["retention_by_station"])
            for event in record["history"]:
                if event["action"] == "scale":
                    replay = replay * event["factor"]
                elif event["action"] == "replace":
                    replay = pd.DataFrame(event["replacement_values"], index=replay.index, columns=replay.columns)
            np.testing.assert_allclose(replay.to_numpy(), series.to_numpy(), rtol=1e-10, atol=1e-10)
            features = reference.features(series)
            for key, value in features.items():
                if isinstance(value, dict):
                    np.testing.assert_allclose(list(value.values()), list(record["features"][key].values()), rtol=1e-9, atol=1e-8)
                else:
                    np.testing.assert_allclose(value, record["features"][key], rtol=1e-9, atol=1e-8)
        return {"verified": True, "run_id": audit["id"], "scenarios_replayed": len(manifest["accepted_ids"]),
                "checks": ["file hashes", "approval revisions", "source window and all edits", "all exported features"]}
