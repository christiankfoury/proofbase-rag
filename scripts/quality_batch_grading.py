"""Two-wave batch grading using the frozen v18 requests and reducer unchanged.

This creates evidence, not readiness approval. A caller must supply newly sealed
cases, authorize plan hashes, submit/collect each wave, and review all results.
"""
from pathlib import Path
import json
from scripts.quality_batch_transport import prepare, verify, read, digest, write
from scripts.quality_eval_transport_v18 import initial_requests, review_request
from scripts.quality_eval_contract_v18 import dimensions
from scripts.report_quality_calibration_v12 import replay_raw


def inputs_only(cases):
    if not 1 <= len(cases) <= 60 or len({c['id'] for c in cases}) != len(cases):
        raise ValueError('Expected unique, bounded cases')
    return [{'id': c['id'], 'inputs': c['inputs'], 'payload': c['payload'],
             'evidence': c['evidence'], 'safety_flags': c['safety_flags']} for c in cases]


def prepare_initial(folder, cases, bindings):
    folder = Path(folder)
    # Deliberately discard reference labels: neither grader wave sees expectations.
    cases = inputs_only(cases)
    if folder.exists():
        raise ValueError('Grading attempt exists; no retry')
    requests = [{'custom_id': c['id'] + '-' + purpose, 'body': body}
                for c in cases for purpose, body in initial_requests(c['inputs'])]
    plan = prepare(folder / 'initial', requests, bindings)
    # Input dictionary order affects the frozen transport's JSON message string.
    # Preserve it exactly instead of using the sorted-key manifest writer.
    with (folder / 'cases.json').open('x', encoding='utf-8', newline='\n') as handle:
        json.dump({'cases': cases}, handle, ensure_ascii=False, indent=2)
        handle.write('\n')
    write(folder / 'grading.json', {'cases_sha256': digest(folder / 'cases.json'),
          'initial_plan_sha256': digest(folder / 'initial/plan.json'), 'bindings': bindings,
          'human_adjudication': False})
    return plan


def checked(folder, wave):
    meta = read(folder / 'grading.json')
    if digest(folder / 'cases.json') != meta['cases_sha256'] or digest(folder / 'initial/plan.json') != meta['initial_plan_sha256']:
        raise ValueError('Grading inputs changed')
    _, state, _ = verify(folder / wave)
    if state['status'] != 'complete' or state['result_sha256'] != digest(folder / wave / 'result.json'):
        raise ValueError('Batch wave is incomplete or changed')
    result = read(folder / wave / 'result.json')
    for name, expected in result['raw_files_sha256'].items():
        if digest(folder / wave / name) != expected:
            raise ValueError('Raw Batch output changed')
    # Parsed response files must correspond exactly to their provider row.
    rows = {r['custom_id']: r for r in (json.loads(line) for line in (folder / wave / 'output.jsonl').read_bytes().splitlines())}
    for cid, row in rows.items():
        saved = read(folder / wave / 'responses' / (cid + '.json'))
        if saved['response'] != row['response']['body']:
            raise ValueError('Extracted response differs from original provider output')
    return meta, read(folder / 'cases.json')['cases']


def claims_and_coverage(folder, case):
    parts = {}
    for purpose, body in initial_requests(case['inputs']):
        parts.update(replay_raw(folder / 'initial/responses' / (case['id'] + '-' + purpose + '.json'), body))
    return parts


def prepare_review(folder):
    folder = Path(folder)
    meta, cases = checked(folder, 'initial')
    requests = [{'custom_id': c['id'] + '-review', 'body': review_request(c['inputs'], claims_and_coverage(folder, c))} for c in cases]
    # No review is issued for invalid/missing initial output. Preserve the failed stage.
    result = prepare(folder / 'review', requests, meta['bindings'])
    meta['review_plan_sha256'] = digest(folder / 'review/plan.json')
    meta['initial_result_sha256'] = digest(folder / 'initial/result.json')
    write(folder / 'grading.json', meta)
    return result


def replay(folder):
    folder = Path(folder)
    meta, cases = checked(folder, 'initial')
    checked(folder, 'review')
    if meta['review_plan_sha256'] != digest(folder / 'review/plan.json') or meta['initial_result_sha256'] != digest(folder / 'initial/result.json'):
        raise ValueError('Review wave dependency changed')
    rows = []
    for case in cases:
        grade = claims_and_coverage(folder, case)
        review = replay_raw(folder / 'review/responses' / (case['id'] + '-review.json'), review_request(case['inputs'], grade))
        result = dimensions(case['inputs'], grade, case['payload'], case['evidence'], case['safety_flags'], review)
        rows.append({'id': case['id'], 'grade': grade, 'review': review, 'dimensions': result})
    return {'rows': rows, 'count': len(rows), 'human_adjudication': False,
            'source_inspection_required': True, 'readiness_approved': False}
