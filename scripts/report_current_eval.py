"""Verify and publish fresh saved evidence without application or model calls."""
import argparse
from collections import Counter
import json
from pathlib import Path
import subprocess
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.current_eval_protocol import FOLDER, verify_custody, digest
from scripts.current_dimension_grader import dimensions, grade_response, VERSION, MODEL
from scripts.current_eval_budget import Ledger
from scripts.reanalyze_saved_answers import build_inputs, DIMS


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def replay_grader(row, inputs):
    from types import SimpleNamespace
    from openai.types.chat import ChatCompletion
    calls = iter(row['raw_grader_responses'])
    def create(**kwargs):
        saved = next(calls)
        if saved['request'] != kwargs:
            raise ValueError('Grader request differs from frozen code/input')
        return ChatCompletion.model_validate(saved['response'])
    grade = None
    try:
        grade = grade_response(SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create))), inputs)
    except ValueError as exc:
        if str(exc) == 'Grader request differs from frozen code/input':
            raise
        if not row.get('grading_error'):
            raise
    if next(calls, None) is not None or grade != row['grade']:
        raise ValueError('Grader outputs do not replay')


def report():
    freeze, suite = verify_custody(require_current=False)
    if digest(FOLDER/'calibration-attempt-1.json') != freeze['calibration_sha256']:
        raise ValueError('Calibration evidence changed')
    old = json.loads(subprocess.check_output(['git','show',f"{freeze['commit']}:data/evaluation/current-runtime-v3/api-ledger.json"], cwd=ROOT).decode('utf-8'))
    ledger = Ledger(FOLDER/'api-ledger.json')
    if ledger.data['calls'][:len(old['calls'])] != old['calls']:
        raise ValueError('Development budget prefix changed')
    manifest = read(FOLDER/'run/manifest.json')
    if manifest['freeze'] != freeze['commit'] or manifest['suite_sha256'] != digest(FOLDER/'holdout.json'):
        raise ValueError('Run custody mismatch')
    rows = []
    for case in suite['cases']:
        path = FOLDER/'run'/f"{case['case_id']}.json"
        if case['case_id'] not in manifest['rows']:
            continue
        if digest(path) != manifest['rows'][case['case_id']]:
            raise ValueError('Response record hash changed')
        row = read(path)
        inputs = build_inputs(case, row)
        if inputs != row['grader_inputs']:
            raise ValueError('Actual grader input differs from canonical UTF-8 evidence')
        replay_grader(row, inputs)
        result = dimensions(inputs, row['grade'], row['raw_response'], row['authorized_evidence'], row['safety_flags'])
        if result != row['dimensions']:
            raise ValueError('Saved dimension judgment changed')
        rows.append({'case_id':case['case_id'], 'category':case['category'], 'expected_behavior':case['expected_behavior'], 'dimensions':result, 'response_type':row['raw_response'].get('response_type'), 'http_status':row['http_status']})
    if len(rows) != manifest['completed_cases']:
        raise ValueError('Completed case denominator mismatch')
    summary = {'kind':'fresh_current_runtime_dimensions', 'version':VERSION, 'model':MODEL,
        'runtime_commit':freeze['commit'], 'suite_version':suite['version'],
        'status':manifest['status'], 'expected_cases':60, 'completed_cases':len(rows),
        'category_counts':dict(Counter(case['category'] for case in suite['cases'])),
        'difficulty_counts':dict(Counter(case['difficulty'] for case in suite['cases'])),
        'expected_behavior_counts':dict(Counter(case['expected_behavior'] for case in suite['cases'])),
        'dimensions':{key:{status:sum(row['dimensions'][key] == status for row in rows) for status in ['pass','fail','unresolved','not_applicable']} for key in DIMS},
        'invalid_grades':sum(bool(row['dimensions']['grader_errors']) for row in rows),
        'response_type_mismatch_cases':[row['case_id'] for row in rows if not row['dimensions']['response_type_match']],
        'safety_flag_cases':[row['case_id'] for row in rows if row['dimensions']['recorded_safety_flags']],
        'http_statuses':dict(Counter(str(row['http_status']) for row in rows)),
        'response_types':dict(Counter(row['response_type'] for row in rows)),
        'cumulative_cost_usd':ledger.spent, 'holdout_cost_usd':ledger.spent-manifest['initial_cost_usd'],
        'budget_limit_usd':2.0, 'human_review':'not_completed',
        'audit_warning':'Source inspection found semantic grader errors: a false factual-error finding, missed omissions, citation penalties on pure refusals, and confusion between clarification, not-found and access refusal. Counts are diagnostic model labels, not an approved release gate. See the separate agent review; raw judgments remain unchanged.',
        'limitation':'Model judgments on 60 agent-authored synthetic cases, not human-verified accuracy. Distinct suite and evaluator; no controlled before/after claim. Invalid grades unresolved; quotation formatting separate.', 'cases':rows}
    return summary, suite


def markdown(summary, suite):
    lines = ['# Phase 68 fresh runtime results', '',
        f"Status: **{summary['status']}**; {summary['completed_cases']}/60 cases. Runtime `{summary['runtime_commit'][:7]}`; evaluator `{VERSION}` / `{MODEL}`.", '',
        summary['limitation'], '', summary['audit_warning'], '',
        'Expected behaviors: ' + ', '.join(f'{key} {value}' for key,value in sorted(summary['expected_behavior_counts'].items())) + '.', '',
        'Author-assigned difficulty: ' + ', '.join(f'{key} {value}' for key,value in sorted(summary['difficulty_counts'].items())) + '. These labels are not externally calibrated.', '',
        '| Dimension | Model pass | Model fail | Unresolved | Not applicable |',
        '|---|---:|---:|---:|---:|']
    for key, counts in summary['dimensions'].items():
        lines.append(f"| {key.replace('_',' ')} | {counts.get('pass',0)} | {counts.get('fail',0)} | {counts.get('unresolved',0)} | {counts.get('not_applicable',0)} |")
    lines.extend(['', f"Schema/reference-invalid grades: {summary['invalid_grades']}. This does not count semantic disagreements described in the agent review. Cases with recorded permission/scope or HTTP safety flags: {len(summary['safety_flag_cases'])}.", '',
        'Response-type metadata differs from the expected label in: ' + ', '.join(summary['response_type_mismatch_cases']) + '. A metadata mismatch alone is not a factual-error judgment; inspect the actual response meaning.', '',
        f"Estimated cumulative API token cost: USD {summary['cumulative_cost_usd']:.6f}; this holdout adds USD {summary['holdout_cost_usd']:.6f}; approved cumulative cap USD 2.00.", '',
        'A pass is a model judgment under the dimension rubric. Unknown claims and invalid grades remain unresolved. No population accuracy, independent human labeling, production safety, or deterministic model-output claim is made.', '',
        'Reproduce saved-evidence verification with `python scripts/report_current_eval.py --check`. The execution script refuses to rerun a started suite. A new live measurement requires a new freeze and new suite.', '',
        'See [source inspection and grader disagreements](agent-review.md), [methodology and known development limitation](preflight.md), [case evidence](case-review.md), [sealed dataset](../../data/evaluation/current-runtime-v3/holdout.json), [freeze](../../data/evaluation/current-runtime-v3/freeze.json), and [raw run manifest](../../data/evaluation/current-runtime-v3/run/manifest.json).', ''])
    packet = ['# Phase 68 case evidence', '', 'Model judgments and source evidence for inspection. Human adjudication has not been completed. Original saved responses are immutable.', '']
    by_id = {r['case_id']:r for r in summary['cases']}
    for case in suite['cases']:
        cid = case['case_id']
        packet += [f"## {cid} — {case['category']}", '', f"Role: {case['user_role']}; expected: {case['expected_behavior']}; difficulty: {case['difficulty']}", '', f"Question: {case['question']}", '', f"Rationale: {case['rationale']}", '']
        if case.get('previous_turns'):
            packet += ['History (context only):', '']
            packet += [f"- {turn['role']}: {turn['content']}" for turn in case['previous_turns']]
            packet += ['']
        for fact in case['required_facts']:
            packet += [f"- {fact['fact_id']}: {fact['text']} — [source](../../{fact['source_path']}). Quote: {fact['source_quote']}"]
        packet += ['', 'Forbidden assertions: ' + json.dumps(case.get('forbidden_assertions',[]),ensure_ascii=False), '']
        if cid in by_id:
            row = read(FOLDER/'run'/f'{cid}.json')
            packet += [f"Response: {row['raw_response'].get('answer','')}", '', 'Citations returned:', '']
            citations = row['raw_response'].get('citations',[])
            packet += [f"- {c.get('document_id')} / {c.get('section_heading')}: {c.get('citation_text','')}" for c in citations] if citations else ['None.']
            packet += ['', 'Dimensions: ' + '; '.join(f"{key}: {row['dimensions'][key]}" for key in DIMS), '', f"[Full response, retrieved evidence, citations and raw grader calls](../../data/evaluation/current-runtime-v3/run/{cid}.json)", '']
        else:
            packet += ['Not completed; no verdict.', '']
    return '\n'.join(lines), '\n'.join(packet)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--check',action='store_true')
    args = ap.parse_args()
    summary,suite = report()
    results,packet = markdown(summary,suite)
    artifacts = {FOLDER/'public-report.json':json.dumps(summary,ensure_ascii=False,indent=2,sort_keys=True)+'\n', ROOT/'docs/phase-68/results.md':results, ROOT/'docs/phase-68/case-review.md':packet}
    for path,text in artifacts.items():
        if args.check:
            if not path.exists() or path.read_text(encoding='utf-8') != text:
                raise ValueError(f'Published artifact differs: {path.name}')
        else:
            path.write_text(text,encoding='utf-8',newline='\n')
    print('Fresh dimension artifacts verified' if args.check else 'Fresh dimension artifacts published')


if __name__ == '__main__':
    main()
