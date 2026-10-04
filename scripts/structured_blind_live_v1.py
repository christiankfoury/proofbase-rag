"""Frozen integration adapter; blind semantics remain in the offline evaluator."""
from pathlib import Path
from decimal import Decimal
from scripts import structured_blind_evaluator_v1 as evaluator
from scripts import quality_eval_transport_v35 as previous
from scripts.bounded_redesign_run import read, write, digest

VERSION = evaluator.VERSION
DIMENSIONS = evaluator.legacy.DIMENSIONS
CAPS = {'claims': 8192, 'coverage': 4096}
reserve, BudgetStop, exclusive_lock = previous.reserve, previous.BudgetStop, previous.exclusive_lock


def initial_requests(inputs):
    return [(r['judge']+'-'+r['purpose'], r['body']) for r in evaluator.request_plan(inputs)]


def case_bound(inputs):
    return evaluator.full_reservation(inputs)


def replay(inputs, folder):
    receipts = {}
    for name, body in initial_requests(inputs):
        path = Path(folder) / (name+'.json')
        if not path.exists(): raise ValueError('Incomplete blind response set')
        receipts[name.replace('-', '.')] = read(path)
    return evaluator.replay_packets(inputs, receipts)


def grade_case(create, inputs, ledger, folder, reused=None):
    folder = Path(folder)
    for name, body in initial_requests(inputs):
        path = folder / (name+'.json')
        if name == 'a-coverage' and reused:
            original = ledger.root / reused['raw_path']
            if digest(original) != reused['raw_sha256'] or path.exists():
                raise ValueError('Reused receipt changed or destination already exists')
            raw = read(original)
            if raw['request'] != body or raw['status'] != 'received':
                raise ValueError('Reused request differs')
            write(path, raw)
        else:
            response = ledger.call(create, body, path)
            # Stop immediately on malformed/short output, with no resubmission.
            previous.parsed(response, body['response_format']['json_schema']['schema'])
    return replay(inputs, folder)


def dimensions(inputs, first, payload, evidence, safety_flags, second=None):
    result = evaluator.compare(inputs, payload, evidence, safety_flags, first, second)
    return dict(result['dimensions'],
        grader_errors=[f'judge-{i}:{e}' for i, errors in enumerate(result['grader_errors']) for e in errors],
        disputed_dimensions=result['disputed_dimensions'],
        review_status=result['status'], nonexact_quotes=result['nonexact_quotes'],
        unmatched_citations=result['unmatched_citations'],
        recorded_safety_flags=result['recorded_safety_flags'],
        response_type_match=result['response_type_match'],
        has_unresolved_judgment=result['has_unresolved_judgment'],
        # A provisional row count only. Live measurement additionally requires
        # qualification, sealed fresh suites, source inspection and release gates.
        target_credit=result['candidate_pass'])
