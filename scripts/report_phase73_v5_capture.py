"""Offline custody/count supplement for complete and unfinished v5 captures.

This does not grade answers or authorize execution. Run the frozen v5 report
check separately for evaluator, authorization and complete cost replay.
"""
import argparse
from collections import Counter
import hashlib
import json
import math
from pathlib import Path
import statistics

ROOT = Path(__file__).resolve().parents[1]
FOLDER = ROOT / 'data/evaluation/current-runtime-v5'


def read(path):
    return json.loads(path.read_bytes())


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def snapshot(folder):
    suite = read(folder / 'holdout.json')
    manifest = read(folder / 'run/manifest.json')
    if manifest['status'] not in {'complete', 'interrupted'}:
        raise ValueError('Only a finished attempt can be inventoried')
    if manifest['suite_sha256'] != digest(folder / 'holdout.json'):
        raise ValueError('Suite binding differs')
    cases = {c['case_id']: c for c in suite['cases']}
    if len(cases) != len(suite['cases']) or manifest['expected_cases'] != len(cases):
        raise ValueError('Case denominator differs')
    inventory = {}
    for path in sorted((folder / 'run').rglob('*.json')):
        if not path.resolve().is_relative_to(folder.resolve()):
            raise ValueError('Unsafe artifact path')
        inventory[path.relative_to(folder).as_posix()] = digest(path)
    started, captured, latencies, rows = set(), set(), [], {}
    for path in sorted((folder / 'run').glob('fresh-*.json')):
        row = read(path)
        cid = row['case_id']
        if cid not in cases or path.stem != cid or cid in started:
            raise ValueError('Unknown, duplicate or misnamed capture')
        started.add(cid)
        rows[cid] = row
        if 'raw_response' not in row:
            continue
        case = cases[cid]
        if not isinstance(row['raw_response'], dict):
            raise ValueError('Invalid saved response')
        request = row['request']
        for key in ['question', 'project_id', 'department_id']:
            if request.get(key) != case.get(key):
                raise ValueError('Captured request differs from sealed scope/question')
        latency = row['latency_ms']
        if not isinstance(latency, (int, float)) or not math.isfinite(latency) or latency < 0:
            raise ValueError('Invalid capture latency')
        latencies.append(latency)
        captured.add(cid)
    completed = set(manifest['rows'])
    if not completed <= captured or len(completed) != manifest['completed_cases']:
        raise ValueError('Completed/captured denominator mismatch')
    for cid, expected in manifest['rows'].items():
        if digest(folder / 'run' / (cid + '.json')) != expected or rows[cid]['status'] != 'complete':
            raise ValueError('Completed row binding differs')
    latencies.sort()
    supporting = {path.name: digest(path) for path in sorted(folder.glob('*.json'))
                  if path.name != 'capture-publication.json'}
    return {
        'version': 'phase73-v5-capture-publication.v1',
        'suite_sha256': digest(folder / 'holdout.json'),
        'run_artifacts_sha256': inventory,
        'supporting_artifacts_sha256': supporting,
        'expected_cases': len(cases), 'completed_cases': len(completed),
        'captured_cases': len(captured), 'started_cases': len(started),
        'ungraded_captured_cases': sorted(captured - completed),
        'started_without_response': sorted(started - captured),
        'unexecuted_cases': sorted(set(cases) - started),
        'completed_categories': dict(Counter(cases[c]['category'] for c in sorted(completed))),
        'captured_categories': dict(Counter(cases[c]['category'] for c in sorted(captured))),
        'latency_ms': {
            'count': len(latencies),
            'median': statistics.median(latencies) if latencies else None,
            'p95': latencies[math.ceil(.95 * len(latencies)) - 1] if latencies else None,
            'scope': 'all saved application responses; excludes grading and fixture indexing',
        },
        'limitation': 'Integrity and capture counts only; no grading, execution authority or full-suite qualification.',
    }


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    result = snapshot(FOLDER)
    path = FOLDER / 'capture-publication.json'
    if args.check:
        if read(path) != result:
            raise SystemExit('Capture inventory or summary differs')
        print('All run artifacts, unfinished captures and response denominators verified offline')
    else:
        path.write_text(json.dumps(result, indent=2, sort_keys=True) + '\n', encoding='utf-8')
        print(f"Saved {result['captured_cases']} captures; {result['completed_cases']} complete rows")
