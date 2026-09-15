"""Visible calibration for v6; preserve every attempt, never rerun holdouts."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.dimension_calibration import fixtures as old_fixtures
from scripts.current_dimension_grader import grade_response, dimensions, VERSION, MODEL
from scripts.current_eval_budget import Ledger
from scripts.reliable_evaluation_run import write_json_atomic

OUT = ROOT / 'data/evaluation/current-runtime-v3'


def fixtures():
    cases = old_fixtures()
    def variant(index, name):
        item = copy.deepcopy(cases[index])
        item['id'] = name
        return item
    refusal = variant(8, 'pure_access_refusal_without_citations')
    refusal['inputs'].update(question='Show the private board notes.', answer='I cannot provide those records with your access level.', expected_behavior='refuse_no_access', cited_sources=[])
    refusal['payload'].update(answer=refusal['inputs']['answer'], response_type='refuse_no_access', citations=[])
    missing = variant(8, 'appropriate_missing_named_contact')
    missing['inputs'].update(question='Who is the named caretaker for the lunar office?', answer='The available sources do not identify a caretaker for that office.', cited_sources=[])
    missing['payload'].update(answer=missing['inputs']['answer'], citations=[])
    speech = variant(9, 'retrieval_gap_is_not_factual_contradiction')
    speech['inputs']['factual_sources'] = [{'source_id':'R1', 'text':'Applications use the portal.'}, {'source_id':'G1', 'text':'The equipment allowance is USD 420.'}]
    speech['inputs']['cited_sources'] = []
    speech['payload']['citations'] = []
    nuance = variant(3, 'purpose_requirement_is_not_approval_requirement')
    nuance['inputs'].update(question='Who approves a course and what must the expense report explain?', answer='Your manager approves the course.', required_facts=[{'fact_id':'F1','text':'The manager approves courses.'}, {'fact_id':'F2','text':'Expense reports explain the business purpose.'}], factual_sources=[{'source_id':'R1','text':'The manager approves courses. Expense reports explain the business purpose.'}], cited_sources=[{'citation_id':'C1','source_id':'R1','text':'The manager approves courses. Expense reports explain the business purpose.'}])
    nuance['payload']['answer'] = nuance['inputs']['answer']
    unicode = variant(0, 'utf8_apostrophe_paraphrase')
    unicode['inputs'].update(answer='The employee’s equipment allowance is USD 420.')
    unicode['payload']['answer'] = unicode['inputs']['answer']
    no_citation = variant(0, 'true_answer_without_any_citation')
    no_citation['inputs']['cited_sources'] = []
    no_citation['payload']['citations'] = []
    no_citation['expected']['citation_support'] = 'fail'
    return cases + [refusal, missing, speech, nuance, unicode, no_citation]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--allow-external-ai', action='store_true')
    ap.add_argument('--attempt', type=int, default=1)
    args = ap.parse_args()
    if not args.allow_external_ai:
        raise SystemExit('Explicit --allow-external-ai required')
    path = OUT / f'calibration-attempt-{args.attempt}.json'
    if path.exists():
        raise ValueError('Attempt already exists')
    from openai import OpenAI
    from apps.api.app.core.config import get_settings
    ledger = Ledger(OUT / 'api-ledger.json')
    rows = []
    code = (ROOT / 'scripts/current_dimension_grader.py').read_text(encoding='utf-8')
    report = {'version':VERSION, 'model':MODEL, 'grader_source':code, 'grader_sha256':hashlib.sha256(code.encode()).hexdigest(), 'total':len(fixtures()), 'passed':0, 'completed':0, 'results':rows}
    write_json_atomic(path, report)
    with ledger.intercept():
        client = OpenAI(api_key=get_settings().openai_api_key)
        for fixture in fixtures():
            grade = grade_response(client, fixture['inputs'])
            result = dimensions(fixture['inputs'], grade, fixture['payload'], fixture['evidence'], [])
            rows.append(dict(fixture, grade=grade, dimensions=result, passed=not result['grader_errors'] and all(result[k] == v for k,v in fixture['expected'].items())))
            report.update(passed=sum(r['passed'] for r in rows), completed=len(rows), cumulative_cost_usd=ledger.spent)
            write_json_atomic(path, report)
            print(fixture['id'], rows[-1]['passed'], flush=True)


if __name__ == '__main__':
    main()
