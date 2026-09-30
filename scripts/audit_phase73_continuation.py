"""Offline continuation audit; never settles an unknown call or issues requests."""
import argparse
from decimal import Decimal
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts import report_phase73_interruption as original
from scripts.quality_cost_standard import SpendJournal
from scripts.quality_completion_durable import write_json_atomic

FOLDER = ROOT / 'data/evaluation/phase73-continuation-v1'
CONTROLS = FOLDER / 'development-controls.json'


def audit_shared_journal(snapshot, current):
    # This audit binds this continuation checkpoint, not arbitrary future spend.
    if current != snapshot:
        raise ValueError('Shared journal differs from the interrupted snapshot')
    unknown = [r for r in current['entries'].values() if r['status'] != 'settled']
    if (len(unknown) != 1 or unknown[0]['status'] != 'unknown'
            or unknown[0]['accounted_usd'] != unknown[0]['reserved_usd']):
        raise ValueError('Expected one fully retained unknown reservation')
    return sum((Decimal(r['accounted_usd']) for r in current['entries'].values()), Decimal(0))


def check_controls(data):
    """Check provenance/structure only. This is NOT semantic model validation."""
    if data['kind'] != 'source_reviewed_development_controls' or data['executed'] is not False:
        raise ValueError('Development controls cannot claim execution')
    ids = set()
    for case in data['cases']:
        if case['id'] in ids or not case['question'] or not case['answer'] or not case['reason']:
            raise ValueError('Invalid development control')
        ids.add(case['id'])
        source = (ROOT / case['source_path']).resolve()
        if (not source.is_relative_to((ROOT / 'data/synthetic-documents').resolve())
                or not case['source_quote'] or case['source_quote'] not in source.read_text(encoding='utf-8')):
            raise ValueError('Development source quote does not match corpus')
        if (case['expected_factual_support'] not in {'pass', 'unresolved'}
                or case['expected_completeness'] not in {'pass', 'fail'}
                or not case['required_fact']):
            raise ValueError('Invalid development expectation')
    if len(ids) != 6:
        raise ValueError('Expected six separately composed controls')
    return len(ids)


def audit():
    evidence = original.replay()
    if evidence != original.read(original.FOLDER / 'public-report.json'):
        raise ValueError('Original published report differs from raw replay')
    ledger = original.read(original.FOLDER / 'run/api-ledger.json')
    row = ledger['calls'][-1]
    raw_path = original.FOLDER / row['raw_path']
    raw = original.read(raw_path)
    snapshot_path = original.FOLDER / 'run/additional-spend.json'
    snapshot = original.read(snapshot_path)
    total = audit_shared_journal(snapshot, SpendJournal().load())
    if total != Decimal(evidence['additional_spend_usd']):
        raise ValueError('Shared accounting disagrees with historical replay')
    controls = original.read(CONTROLS)
    count = check_controls(controls)
    ceiling = Decimal(evidence['additional_ceiling_usd'])
    # No settlement is inferred from a full reservation or the passage of time.
    return {
        'version': 'phase73-continuation-audit.v1',
        'status': 'blocked_unknown_provider_outcome',
        'provider_outcome': 'unknown', 'paid_execution_allowed': False,
        'original_suite_resume_allowed': False, 'original_score_adjusted': False,
        'new_api_calls': 0, 'new_api_cost_usd': '0',
        'additional_ceiling_usd': str(ceiling),
        'additional_accounted_usd': str(total),
        'additional_remaining_usd': str(ceiling - total),
        'unknown_reservation_usd': row['reserved_usd'],
        'unknown_call_index': row['call_index'],
        'unknown_request_sha256': row['request_sha256'],
        'unknown_shared_identity': row['additional_spend_identity'],
        'request_model': raw['request']['model'],
        'request_store_enabled': raw['request'].get('store') is True,
        'response_available': raw.get('response') is not None,
        'completion_id_available': bool((raw.get('response') or {}).get('id')),
        'saved_exception_type': raw['exception_type'],
        'shared_journal_entries': len(snapshot['entries']),
        'original_cumulative_calls': evidence['cumulative_calls'],
        'original_cumulative_conservative_usd': evidence['cumulative_cost_usd'],
        'source_review_findings': {
            'SR-006': 'claim_boundary_uncertainty_requires_development_validation',
            'SR-007': 'reference_broader_than_question_original_grade_retained',
            'SR-011': 'reference_broader_than_question_and_modality_mismatch_ungraded',
        },
        'development_controls': count,
        'development_controls_executed': False,
        'source_quote_check_only': True,
        'evidence_sha256': {
            p.relative_to(ROOT).as_posix(): original.digest(p) for p in [
                original.FOLDER / 'interruption-seal.json',
                original.FOLDER / 'public-report.json',
                original.FOLDER / 'run/api-ledger.json', raw_path, snapshot_path,
                ROOT / 'docs/phase-73/source-review.md', CONTROLS,
            ]
        },
        'recovery_requirement': 'Provider outcome/usage evidence or an explicit policy decision accepting a still-unknown outcome with its full reservation retained; never a silent flag clear.',
    }


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    result = audit()
    path = FOLDER / 'audit.json'
    if args.check:
        if original.read(path) != result:
            raise ValueError('Continuation audit differs from preserved evidence')
    else:
        write_json_atomic(path, result)
    print('Continuation blocked: unknown provider outcome; full reservation retained; '
          f"USD {result['additional_remaining_usd']} remaining; zero new API calls")
