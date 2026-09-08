"""Hydrologist interaction harness for BASIN.

Allows an agent or user to inspect scenarios, ask the built-in AI assistant
questions, run multi-tier stress spectrum simulations, log professional review
notes, and export a cryptographically verified hydrologist handoff packet.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
import zipfile

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Add project root to sys.path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from basin_core.data import CachedSource
from basin_core.engine import ScenarioParams
from basin_core.workspace import Workspace
from basin_core.assistant import run_assistant, run_tool_directly
from basin_core.tools import run_stress_spectrum
from basin_core.exporter import export_bundle, verify_bundle
from basin_ui import fallback_query_route

SESSION_FILE = ROOT / "output" / "hydrologist_session.json"
WORKSPACE_DIR = ROOT / "output" / "workspaces"


def get_or_create_workspace() -> tuple[Workspace, dict]:
    WORKSPACE_DIR.mkdir(parents=True, exist_ok=True)
    source = CachedSource()

    session_meta = {
        "workspace_id": None,
        "session_path": None,
        "chat_history": []
    }

    if SESSION_FILE.exists():
        try:
            session_meta = json.loads(SESSION_FILE.read_text(encoding="utf-8"))
            session_path = Path(session_meta["session_path"])
            if session_path.exists():
                ws = Workspace.load(source, session_path)
                return ws, session_meta
        except Exception:
            pass

    # Create fresh workspace
    params = ScenarioParams(tuple(source.daily.columns), candidates=30)
    ws = Workspace(source, params, size=3)
    saved_path = ws.save(WORKSPACE_DIR)
    session_meta["workspace_id"] = ws.id
    session_meta["session_path"] = str(saved_path)
    session_meta["chat_history"] = []
    SESSION_FILE.write_text(json.dumps(session_meta, indent=2), encoding="utf-8")
    return ws, session_meta


def save_workspace(ws: Workspace, session_meta: dict):
    saved_path = ws.save(WORKSPACE_DIR)
    session_meta["session_path"] = str(saved_path)
    SESSION_FILE.write_text(json.dumps(session_meta, indent=2), encoding="utf-8")


def cmd_status(args):
    ws, meta = get_or_create_workspace()
    print(f"=== BASIN Workspace [{ws.id}] Status ===")
    print(f"Created: {ws.created_at}")
    print(f"NOAA Snapshot SHA-256: {ws.source.manifest['sha256'][:16]}...")
    print(f"Stations ({len(ws.source.manifest['stations'])}): {', '.join(s['id'] for s in ws.source.manifest['stations'])}")
    print(f"\nShortlisted Scenarios ({len(ws.selected)}):")
    for sid in ws.selected:
        s = ws.get(sid)
        rev = f"r{s.revision}"
        stat = s.status
        deficit_in = s.features['deficit_mm'] / 25.4
        duration = s.features['duration_days']
        start = s.provenance['source_start']
        end = s.provenance['source_end']
        print(f"  * {s.id} ({getattr(s, 'cluster_name', f'Group {s.cluster}')}) | Score: {s.score:.2f} | Status: {stat} ({rev})")
        print(f"    - Window: {start} to {end} ({duration} days)")
        print(f"    - Deficit: {s.features['deficit_mm']:.1f} mm ({deficit_in:.2f} in) | Concurrence: {s.features['concurrence']:.1%}")
        latest_note = s.history[-1].get("private_note", "") if s.history else ""
        if latest_note:
            print(f"    - Notes: {latest_note}")
    print("\nUse 'ask', 'spectrum', 'review', or 'export' to proceed.")


def cmd_ask(args):
    ws, meta = get_or_create_workspace()
    query = args.prompt
    history = meta.get("chat_history", [])

    print(f"\n[Hydrologist Query] -> \"{query}\"\n")
    try:
        reply, updated_history = run_assistant(ws, query, history)
    except Exception as exc:
        # Fallback to deterministic routing
        print(f"(Note: LLM call diverted to deterministic tool routing: {exc})")
        reply = fallback_query_route(ws, query)
        updated_history = history + [
            {"role": "user", "content": query},
            {"role": "assistant", "content": reply}
        ]

    meta["chat_history"] = updated_history
    save_workspace(ws, meta)
    print(reply)


def cmd_spectrum(args):
    ws, meta = get_or_create_workspace()
    sid = args.scenario_id or ws.selected[0]
    init_pct = args.initial_pct
    cons_pct = args.conservation_pct

    print(f"\n=== Running Multi-Tier Stress Spectrum for {sid} ===")
    print(f"Initial Storage: {init_pct*100:.1f}% | Conservation: {cons_pct:.1f}%\n")

    res = run_stress_spectrum(ws, scenario_id=sid,
                              initial_storage_pct=init_pct,
                              conservation_pct=cons_pct)
    from basin_core.assistant import render_tool_result
    rendered = render_tool_result("run_stress_spectrum", res)
    print(rendered)


def cmd_review(args):
    ws, meta = get_or_create_workspace()
    sid = args.scenario_id
    s = ws.get(sid)
    accept = not args.reject
    note = args.note or "Hydrologist verified for drought contingency planning."

    s.review(accept, note)
    save_workspace(ws, meta)
    print(f"Successfully reviewed {sid}: status={s.status}, revision=r{s.revision}")
    print(f"Review note: \"{note}\"")


def cmd_export(args):
    ws, meta = get_or_create_workspace()
    out_path = Path(args.output) if args.output else (ROOT / "output" / f"BASIN-Export-{ws.id}.zip")
    out_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"Building verified hydrologist export bundle for workspace {ws.id}...")
    try:
        bundle_bytes = export_bundle(ws, include_notes=True)
        out_path.write_bytes(bundle_bytes)
        print(f"Export written to: {out_path} ({len(bundle_bytes):,} bytes)")

        # Verify bundle
        print("\nVerifying bundle cryptographic and mathematical integrity...")
        verification = verify_bundle(bundle_bytes)
        print(json.dumps(verification, indent=2))

        # Extract and print the handoff brief
        with zipfile.ZipFile(out_path, "r") as z:
            brief_content = z.read("Hydrologist_Handoff_Brief.md").decode("utf-8")
            print("\n" + "="*70)
            print("=== Hydrologist_Handoff_Brief.md ===")
            print("="*70 + "\n")
            print(brief_content)

    except ValueError as exc:
        print(f"Export blocked: {exc}")
        sys.exit(1)


def cmd_reset(args):
    if SESSION_FILE.exists():
        SESSION_FILE.unlink()
    ws, meta = get_or_create_workspace()
    print(f"Reset complete. Created fresh workspace {ws.id}.")


def main():
    parser = argparse.ArgumentParser(description="BASIN Hydrologist CLI Harness")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # status
    p_status = subparsers.add_parser("status", help="Inspect workspace status and shortlisted scenarios")
    p_status.set_defaults(func=cmd_status)

    # ask
    p_ask = subparsers.add_parser("ask", help="Ask the BASIN AI assistant a technical query")
    p_ask.add_argument("prompt", type=str, help="Question or instruction for the AI assistant")
    p_ask.set_defaults(func=cmd_ask)

    # spectrum
    p_spectrum = subparsers.add_parser("spectrum", help="Run 1-click multi-tier stress spectrum sweep")
    p_spectrum.add_argument("scenario_id", type=str, nargs="?", default="", help="Scenario ID (e.g. B-016)")
    p_spectrum.add_argument("--initial-pct", type=float, default=0.48, help="Initial reservoir storage fraction (0.48 = 48%)")
    p_spectrum.add_argument("--conservation-pct", type=float, default=0.0, help="Emergency conservation cut percentage (0 to 30)")
    p_spectrum.set_defaults(func=cmd_spectrum)

    # review
    p_review = subparsers.add_parser("review", help="Log professional review note and approve/reject scenario")
    p_review.add_argument("scenario_id", type=str, help="Scenario ID to review")
    p_review.add_argument("--reject", action="store_true", help="Reject scenario instead of accepting")
    p_review.add_argument("--note", type=str, required=True, help="Professional hydrologist justification note")
    p_review.set_defaults(func=cmd_review)

    # export
    p_export = subparsers.add_parser("export", help="Export and verify hydrologist handoff bundle")
    p_export.add_argument("--output", type=str, default="", help="Custom output zip path")
    p_export.set_defaults(func=cmd_export)

    # reset
    p_reset = subparsers.add_parser("reset", help="Reset and generate fresh workspace")
    p_reset.set_defaults(func=cmd_reset)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
