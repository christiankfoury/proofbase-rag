"""Offline receipt/custody accounting only; semantic verdicts require source inspection."""
from decimal import Decimal
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.policy_fact_candidate_diagnostic import FOLDER, read, digest, prepare, INITIAL, CEILING
from scripts.phase73_v6_budget import response_charge, request_hash
from scripts.quality_cost_phase73_v2 import live_policy


def report():
    plan = read(FOLDER/'preflight.json'); manifest = read(FOLDER/'run/manifest.json')
    ledger = read(FOLDER/'run/api-ledger.json'); journal = read(FOLDER/'run/additional-spend.json')
    assert manifest['preflight_sha256'] == digest(FOLDER/'preflight.json')
    assert all(digest(ROOT/p) == h for p,h in plan['bindings'].items())
    assert all(journal['entries'].get(k) == v for k,v in plan['initial_journal']['entries'].items())
    suite = read(FOLDER/'cases.json'); ids = [c['id'] for c in suite['cases']]
    assert ledger['attempted_cases'] == ids[:len(ledger['attempted_cases'])]
    assert len(ledger['calls']) <= 24 and len(ledger['attempted_cases']) <= 6
    identities, seen, costs, stages = set(), set(), {}, {}
    for call in ledger['calls']:
        assert call['case_id'] in ledger['attempted_cases']
        key = call['case_id'], call['stage']; assert key not in seen; seen.add(key)
        path = FOLDER/'run'/call['raw_path']; raw = read(path)
        assert digest(path) == call['raw_sha256']
        body, (bound, cap, reserve) = prepare(raw['request'])
        assert body == raw['request'] and request_hash(body) == call['request_sha256']
        assert (bound, cap, reserve) == (call['input_bound'], call['output_cap'], Decimal(call['reserved_usd']))
        if call['status'] == 'completed':
            assert raw['status'] == 'received'
            charge = response_charge(raw['response'], body['model'])
            assert charge == Decimal(call['charged_usd']) <= reserve
            usage = raw['response']['usage']
            assert 0 <= usage['prompt_tokens'] <= bound and 0 <= usage['completion_tokens'] <= cap
        else:
            assert call['status'] == 'unknown' and ledger['stopped'] and ledger['unknown_outcome']
            charge = reserve
        entry = journal['entries'][call['identity']]
        assert Decimal(entry['accounted_usd']) == charge
        identities.add(call['identity']); costs[call['case_id']] = costs.get(call['case_id'], Decimal(0)) + charge
        stages[call['stage']] = stages.get(call['stage'], 0) + 1
    assert set(journal['entries']) - set(plan['initial_journal']['entries']) == identities
    total = sum(costs.values(), Decimal(0)); assert total == Decimal(manifest['charged_usd']) <= CEILING
    _, ceiling = live_policy()
    assert ceiling-sum((Decimal(e['accounted_usd']) for e in journal['entries'].values()),Decimal(0)) == INITIAL-total
    assert Decimal(manifest['remaining_usd']) == INITIAL-total
    assert [r['case_id'] for r in manifest['rows']] == ids[:len(manifest['rows'])]
    rows = []
    from scripts.policy_fact_candidate_support import authorized_sources
    from dataclasses import asdict
    for meta in manifest['rows']:
        path = FOLDER/'run'/(meta['case_id']+'.json'); assert digest(path) == meta['sha256']
        row = read(path); case = next(c for c in suite['cases'] if c['id'] == meta['case_id'])
        sources = authorized_sources(suite, case)
        assert row['question'] == case['question'] and row['authorized_evidence'] == [asdict(s) for s in sources]
        source_by_id = {s.chunk_id:s for s in sources}
        for citation in row['final_response']['citations']:
            source = source_by_id[citation['chunk_id']]
            assert citation['document_id'] == source.document_id and citation['citation_text'] in source.content
        rows.append(dict(case_id=case['id'], response_type=row['final_response']['response_type'], charged_usd=str(costs.get(case['id'],0))))
    if manifest['status'] == 'complete':
        assert len(rows) == 6 and not ledger['stopped'] and not ledger['unknown_outcome']
    return dict(kind='Receipt accounting and custody; no semantic score', status=manifest['status'],
        calls=len(ledger['calls']), by_stage=stages, charged_usd=str(total), remaining_usd=str(INITIAL-total), cases=rows)


if __name__ == '__main__': print(json.dumps(report(), indent=2))
