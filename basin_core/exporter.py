from __future__ import annotations

import hashlib
import importlib.metadata
import io
import json
from types import SimpleNamespace
import zipfile

import numpy as np
import pandas as pd

from basin_core import __version__
from basin_core.data import CachedSource, ROOT
from basin_core.evidence import public_copy
from basin_core.integrity import compare_values, reconstruct_audit

SCHEMA = '2.0'
CHECKS = ['complete file inventory and hashes', 'source snapshot identity', 'exact dates, station order and units',
          'all scenario transformations and revision digests', 'selected/accepted IDs and approval history',
          'rainfall features, scores, components and shortlist summaries', 'evidence links and privacy defaults',
          'readable brief matches audited content']
EXCLUDED = ['scientific validity or source authenticity', 'professional approval or user benefit',
            'KMeans labels, selection history and saved comparison results (recorded and hash-checked only)',
            'reservoir experiment and threshold timing', 'performance measurements and implementation identity attestation']
FILES = {'daily_rainfall.csv', 'shortlist.csv', 'audit.json', 'Hydrologist_Handoff_Brief.md',
         'snapshot/observations.csv', 'snapshot/manifest.json', 'methodology.md', 'README.txt'}


def dumps(value):
    return json.dumps(value, indent=2, allow_nan=False).encode()


def implementation_identity():
    paths = [ROOT / 'app.py', ROOT / 'basin_ui.py', ROOT / 'requirements.txt', ROOT / 'scripts/replay_bundle.py',
             ROOT / 'docs/methodology.md', *sorted((ROOT / 'basin_core').glob('*.py'))]
    # Normalize text line endings so Windows and Unix identify the same source.
    files = {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes().replace(b'\r\n', b'\n')).hexdigest() for p in paths}
    return {'method': 'sha256 of named UTF-8 source files with LF line endings', 'files': files,
            'sha256': hashlib.sha256(json.dumps(files, sort_keys=True).encode()).hexdigest()}


def text_cell(value):
    return str(value).replace('|', '\\|').replace('\n', ' ').replace('\r', ' ').replace('<', '&lt;').replace('>', '&gt;')


def generate_brief(workspace, accepted):
    total = sum(workspace.weights.values())
    lines = ['# BASIN — Rainfall Scenario Handoff', '', f'Run: `{workspace.id}` · created {workspace.created_at} · BASIN {__version__}', '',
             '## Purpose and limits', '',
             'An analyst selected rainfall stress scenarios for deeper drought-planning analysis. Accept records a local rainfall-content review; it does not establish professional sign-off, validated catchment suitability, probability, water supply or restriction dates.', '',
             'Stations are provisional regional airport proxies. Rainfall retention cannot be applied directly to naturalized streamflow. A domain specialist must determine geographic suitability, rainfall–runoff modeling, operating rules and any appropriate downstream modeling application.', '',
             '## Community Priority Configuration', '', 'User-selected normalized weights (illustrative priorities; no provider endorsement):', '']
    lines += [f'- {k.title()}: {v / total:.1%} (raw weight {v})' for k, v in workspace.weights.items()]
    lines += ['', 'Approval applies to rainfall content; current weights may differ from weights at approval. The shortlist changes only on an explicit rebuild or manual swap.', '',
              '## Accepted rainfall revisions', '',
              '| Scenario | Revision | Days | Net deficit (mm/station) | Net Deficit (in) | Station stress fraction | Reference n | Source window |',
              '|---|---|---|---|---|---|---|---|']
    for s in accepted:
        f, p = s.features, s.provenance
        lines.append(f"| {s.id} | {s.revision} | {f['duration_days']} | {f['deficit_mm']:.2f} | {f['deficit_mm']/25.4:.2f} | {f['concurrence']:.1%} | {f['benchmark_n']} | {p['source_start']} – {p['source_end']} |")
    lines.append('')
    for s in accepted:
        lines.append(f"Evidence for {s.id}: " + ', '.join(workspace.evidence_refs[s.id]))
    lines += ['', '## Evidence and assumptions', '']
    # Include the registry so both sides of every conflict remain interpretable.
    for e in workspace.evidence:
        lines += [f"### {text_cell(e['id'])}: {text_cell(e['title'])}",
                  f"{text_cell(e['kind'])} · {text_cell(e['review_status'])} · {text_cell(e['publisher'])}",
                  f"Source: {text_cell(e['source_locator'])}; source date/version date: {text_cell(e['source_date']) or 'not supplied'}; retrieved: {text_cell(e['retrieved_at']) or 'not supplied'}.",
                  f"Geography: {text_cell(e['geographic_scope'])}. Units: {text_cell(e['units']) or 'not applicable'}.",
                  text_cell(e['description']), '']
    lines += ['## Unresolved issues and conflict dispositions', '', 'Catchment suitability and practitioner methodology review remain unvalidated.', '']
    if not workspace.conflicts:
        lines.append('No evidence disagreements have been recorded; this does not establish that none exist.')
    for c in workspace.conflicts:
        lines += [f"- {text_cell(c['id'])} [{c['status']}]: {text_cell(c['left_id'])} vs {text_cell(c['right_id'])} — {text_cell(c['disagreement'])}",
                  '  Comparability: ' + text_cell(c['comparability']), '  Human disposition: ' + (text_cell(c['resolution']) or 'Unresolved; no disposition recorded.')]
    lines += ['', '## Recipient next action', '',
              'Inspect daily_rainfall.csv and the matched references, challenge the listed assumptions, and decide what further data or modeling is appropriate. Scenario dates identify historical source days. The separate illustrative reservoir experiment is excluded from this packet.', '',
              'Replay: `python scripts/replay_bundle.py path/to/bundle.zip`.', '',
              'Verification checks internal consistency, not authenticity or scientific validity. Grouping, selection history and saved comparisons are recorded and hash-checked only. Unsigned hashes do not protect against coordinated changes. Public evidence and dispositions are included; private annotations only appear in audit.json when opted in.']
    return '\n'.join(lines) + '\n'


def summary_record(s):
    return {'scenario_id': s.id, 'revision': s.revision, 'priority_score': s.score,
            **{k: v for k, v in s.features.items() if not isinstance(v, dict)}}


def rainfall_rows(s):
    frame = s.series.rename_axis('date').reset_index().melt(id_vars='date', var_name='station_id', value_name='precip_mm')
    frame['scenario_id'], frame['revision'], frame['units'] = s.id, s.revision, 'mm/day'
    return frame


def export_bundle(workspace, include_notes=False):
    accepted = workspace.exportable()
    audit = workspace.record(include_notes)
    reconstruct_audit(workspace.source, audit, require_export=True)
    files = {'daily_rainfall.csv': pd.concat([rainfall_rows(s) for s in accepted]).to_csv(index=False, lineterminator='\n').encode(),
             'shortlist.csv': pd.DataFrame([summary_record(s) for s in accepted]).to_csv(index=False, lineterminator='\n').encode(),
             'audit.json': dumps(audit), 'Hydrologist_Handoff_Brief.md': generate_brief(workspace, accepted).encode(),
             'snapshot/observations.csv': workspace.source.raw, 'snapshot/manifest.json': dumps(workspace.source.manifest),
             'methodology.md': (ROOT / 'docs/methodology.md').read_bytes(),
             'README.txt': b'BASIN rainfall scenarios for expert review. Historical dates are source labels, not forecasts.\nReplay with BASIN 0.2: python scripts/replay_bundle.py path/to/bundle.zip\nSee the handoff brief for verification scope, assumptions and unresolved issues. The reservoir experiment is excluded.\n'}
    manifest = {'schema_version': SCHEMA, 'basin_version': __version__, 'run_id': workspace.id,
                'accepted_ids': [s.id for s in accepted], 'private_notes_included': include_notes,
                'implementation': implementation_identity(), 'verification_scope': {'checks': CHECKS, 'excluded': EXCLUDED},
                'software': {p: importlib.metadata.version(p) for p in ['numpy', 'pandas', 'scikit-learn', 'streamlit']},
                'files': {n: hashlib.sha256(b).hexdigest() for n, b in files.items()}}
    files['bundle_manifest.json'] = dumps(manifest)
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as archive:
        for name, data in files.items(): archive.writestr(name, data)
    return buffer.getvalue()


def _verify(payload):
    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        names = archive.namelist()
        if len(names) != len(set(names)) or set(names) != FILES | {'bundle_manifest.json'}:
            raise ValueError('Bundle file inventory mismatch or duplicate entries')
        if sum(f.file_size for f in archive.infolist()) > 100_000_000:
            raise ValueError('Bundle is too large')
        manifest = json.loads(archive.read('bundle_manifest.json'))
        if manifest['schema_version'] != SCHEMA or manifest['basin_version'] != __version__:
            raise ValueError('Unsupported bundle version; restore the original session and re-export with BASIN 0.2')
        if set(manifest['files']) != FILES:
            raise ValueError('Missing file checksums')
        for name, digest in manifest['files'].items():
            if hashlib.sha256(archive.read(name)).hexdigest() != digest: raise ValueError(f'Checksum mismatch: {name}')
        if manifest['verification_scope'] != {'checks': CHECKS, 'excluded': EXCLUDED}:
            raise ValueError('Verification scope mismatch')
        identity = manifest['implementation']
        if hashlib.sha256(json.dumps(identity['files'], sort_keys=True).encode()).hexdigest() != identity['sha256']:
            raise ValueError('Implementation identity is internally inconsistent')
        source = CachedSource(raw=archive.read('snapshot/observations.csv'), manifest=json.loads(archive.read('snapshot/manifest.json')))
        audit = json.loads(archive.read('audit.json'))
        if audit['schema_version'] != SCHEMA or audit['id'] != manifest['run_id']:
            raise ValueError('Audit schema or run identity mismatch')
        if type(manifest['private_notes_included']) is not bool:
            raise ValueError('Invalid privacy choice')
        if not manifest['private_notes_included'] and public_copy(audit) != audit:
            raise ValueError('Private annotations included despite privacy setting')
        params, reference, scenarios = reconstruct_audit(source, audit, require_export=True)
        by_id = {s.id: s for s in scenarios}
        accepted = [by_id[i] for i in audit['selected'] if by_id[i].status == 'accepted']
        if manifest['accepted_ids'] != [s.id for s in accepted]:
            raise ValueError('Accepted IDs disagree with selected audit records')
        rainfall = pd.read_csv(io.BytesIO(archive.read('daily_rainfall.csv')), parse_dates=['date'], float_precision='round_trip')
        expected = pd.concat([rainfall_rows(s) for s in accepted], ignore_index=True)
        if list(rainfall.columns) != list(expected.columns) or len(rainfall) != len(expected):
            raise ValueError('Rainfall row/column count mismatch')
        for field in ('date', 'station_id', 'scenario_id', 'revision', 'units'):
            if not rainfall[field].equals(expected[field]): raise ValueError(f'Rainfall {field} order or identity mismatch')
        np.testing.assert_allclose(rainfall.precip_mm, expected.precip_mm, rtol=1e-10, atol=1e-10)
        summary = pd.read_csv(io.BytesIO(archive.read('shortlist.csv')), float_precision='round_trip')
        expected_summary = [summary_record(s) for s in accepted]
        if len(summary) != len(accepted) or list(summary.columns) != list(expected_summary[0]):
            raise ValueError('Shortlist summary inventory mismatch')
        for row, wanted in zip(summary.to_dict('records'), expected_summary): compare_values(row, wanted, 'Shortlist summary')
        view = SimpleNamespace(**{k: audit[k] for k in ('id', 'created_at', 'weights', 'evidence', 'evidence_refs', 'conflicts')})
        if archive.read('Hydrologist_Handoff_Brief.md') != generate_brief(view, accepted).encode():
            raise ValueError('Handoff brief differs from audited content')
        return {'verified': True, 'run_id': audit['id'], 'scenarios_replayed': len(accepted),
                'audit_records_replayed': len(scenarios), 'checks': CHECKS, 'excluded': EXCLUDED,
                'implementation_matches_current': identity == implementation_identity()}


def verify_bundle(payload):
    try:
        return _verify(payload)
    except (KeyError, TypeError, IndexError, AttributeError, zipfile.BadZipFile, AssertionError, OverflowError) as error:
        raise ValueError(f'Malformed or inconsistent bundle: {error}') from error
