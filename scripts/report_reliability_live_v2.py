"""Replay receipts and source custody offline; never calculate a quality score."""
from collections import Counter
import hashlib
from decimal import Decimal
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.application_reliability_live_v2 import FOLDER, read, digest, write
from scripts.reliability_payload_budget import reservation
from scripts.phase73_v6_budget import response_charge, request_hash
from apps.api.app.permissions.access_control import role_can_access


def replay():
    prepared, suite = read(FOLDER/'preflight.json'), read(FOLDER/'cases.json')
    assert prepared['suite_sha256'] == digest(FOLDER/'cases.json')
    assert prepared['runner_sha256'] == digest(ROOT/'scripts/application_reliability_live_v2.py')
    assert prepared['estimator_sha256'] == digest(ROOT/'scripts/reliability_payload_budget.py')
    assert prepared['pricing_sha256'] == digest(FOLDER/'pricing.json')
    for path, expected in prepared['runtime_files_sha256'].items():
        assert digest(ROOT/path) == expected, f'Runtime changed: {path}'
    run = FOLDER/'run'
    ledger, manifest = read(run/'api-ledger.json'), read(run/'manifest.json')
    assert manifest['status'] == 'complete' and not ledger['stopped'] and not ledger['unknown_outcome']
    assert ledger['case_ids'] == [c['case_id'] for c in suite['cases']]
    assert len(suite['cases']) == 6 and len(manifest['rows']) == 6
    provenance = {p['chunk_id']:p for p in read(FOLDER/'egress-provenance.json')['proof']}
    previous, final = prepared['initial_journal'], read(run/'additional-spend.json')
    assert final['policy_sha256'] == previous['policy_sha256']
    assert all(final['entries'][k] == value for k,value in previous['entries'].items())
    counts, per_case, stages = Counter(), Counter(), Counter()
    identities, spent, rows, serialization_deltas = set(), Decimal(0), [], []
    for i, call in enumerate(ledger['calls']):
        path = run/call['raw_path']
        raw = read(path)
        assert call['call_index'] == i and call['status'] == 'completed'
        assert digest(path) == call['raw_sha256'] and request_hash(raw['request']) == call['request_sha256']
        bound, cap, reserved = reservation(raw['request'], call['operation'])
        # Atomic JSON persistence sorts keys. Tokenization of the recorded object
        # differs slightly from its original ordering; retain both observations.
        # Independently audit the recorded reservation formula and actual usage.
        assert cap == call['output_cap']
        limit, rate = (16384, Decimal('.40')) if call['operation'] == 'chat' else (8192, Decimal('.02'))
        assert 2048 <= call['input_bound'] <= limit and bound <= limit
        reserved = (call['input_bound'] * rate + cap * Decimal('1.60')) / 1_000_000
        assert reserved == Decimal(call['reserved_usd'])
        if bound != call['input_bound']:
            serialization_deltas.append(dict(call_index=i, recorded_bound=call['input_bound'], sorted_json_replay_bound=bound))
        charge = response_charge(raw['response'], raw['request']['model'])
        assert charge == Decimal(call['charged_usd']) <= reserved
        usage = raw['response']['usage']
        assert 0 <= usage['prompt_tokens'] == call['input_tokens'] <= min(bound, call['input_bound'])
        assert 0 <= usage.get('completion_tokens',0) == call['output_tokens'] <= cap
        if call['operation'] == 'chat':
            assert raw['request']['service_tier'] == 'default'
        identity = call['additional_spend_identity']; identities.add(identity)
        shared = final['entries'][identity]
        assert shared['status'] == 'settled' and Decimal(shared['accounted_usd']) == charge
        assert shared['result_sha256'] == digest(path) and shared['evidence_sha256'] == call['request_sha256']
        counts[call['operation']] += 1; per_case[(call['case_id'], call['operation'])] += 1
        stages[raw['request'].get('response_format',{}).get('json_schema',{}).get('name',call['operation'])] += 1
        spent += charge
    assert set(final['entries']) - set(previous['entries']) == identities
    assert spent == Decimal(manifest['charged_usd']) <= Decimal('.50')
    assert len(ledger['calls']) <= 60 and counts['chat'] <= 42 and counts['embedding'] <= 18
    assert all(n <= (7 if operation == 'chat' else 3) for (_,operation), n in per_case.items())
    for case in suite['cases']:
        path = run/(case['case_id']+'.json'); row = read(path)
        assert digest(path) == manifest['rows'][case['case_id']]
        assert row['http_status'] == 200 and row['status'] == 'complete' and not row['safety_flags']
        assert row['request']['question'] == case['question']
        answer = row['raw_response']; evidence = {e['chunk_id']:e for e in row['authorized_evidence']}
        assert set(evidence) == {c['chunk_id'] for c in answer['retrieved_chunks']}
        for source in case['sources']:
            assert digest(ROOT/source['path']) == source['sha256']
        for e in evidence.values():
            assert hashlib.sha256(e['content'].encode()).hexdigest() == provenance[e['chunk_id']]['content_sha256']
            assert role_can_access(e['access_roles'], case['user_role'])
            assert e['project_id'] == case['project_id']
            assert e['tenant_id'] == prepared['environment']['settings']['default_demo_tenant_id']
        for citation in answer['citations']:
            e = evidence[citation['chunk_id']]
            assert citation['document_id'] == e['document_id']
            assert citation['citation_text'] in e['content']
        calls = [c for c in ledger['calls'] if c['case_id'] == case['case_id']]
        rows.append(dict(case_id=case['case_id'], response_type=answer['response_type'],
            calls=len(calls), cost_usd=str(sum((Decimal(c['charged_usd']) for c in calls),Decimal(0))),
            latency_ms=row['latency_ms'], multi_doc_used=answer['multi_doc_used']))
    remaining = Decimal(prepared['initial_remainder_usd']) - spent
    assert remaining == Decimal(manifest['remaining_usd'])
    comparison = read(FOLDER/'excerpt-counterfactual.json')
    equipment = read(run/'check-04.json')
    citation = equipment['raw_response']['citations'][0]
    assert comparison['after']['citation_text'] == citation['citation_text']
    assert 'payroll' not in comparison['before']['citation_text'].lower()
    assert 'This policy does not authorize payroll deductions by itself.' in citation['citation_text']
    return dict(scope='Six-case live development diagnostic; agent source inspection, no overall score',
        runtime_commit=prepared['runtime_commit'], calls=dict(counts), stages=dict(stages), charged_usd=str(spent),
        remaining_usd=str(remaining), application_ms=sum(r['latency_ms'] for r in rows),
        provider_ms=sum(c['latency_ms'] for c in ledger['calls']), rows=rows,
        serialization_bound_deltas=serialization_deltas,
        reservation_replay_note='Sorted receipt JSON changes estimates by 1 or 3 tokens in this run. Recorded reservation arithmetic and actual usage independently verified; original serialized body ordering was not retained.')


if __name__ == '__main__':
    result = replay()
    if '--record' in sys.argv: write(FOLDER/'receipt-summary.json',result)
    if '--check' in sys.argv: assert read(FOLDER/'receipt-summary.json') == result
    print(json.dumps(result,indent=2))
