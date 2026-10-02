"""Offline receipt/source-integrity replay. No quality score or model grading."""
from collections import Counter
from decimal import Decimal
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.application_reliability_live import FOLDER, read, digest, reservation, request_hash, response_charge
from apps.api.app.permissions.access_control import role_can_access


def source_diagnostics(folder=FOLDER):
    """Reconstruct rejected payloads and compare the saved quote with pre-R3 code.

    Pure local inspection: inject a capture-only client, never issue an API call.
    """
    from dataclasses import fields
    from types import SimpleNamespace
    import subprocess
    from apps.api.app.retrieval.types import RetrievedChunk
    from apps.api.app.reasoning.request_assessment import RequestAssessment
    from apps.api.app.reasoning.evidence_assessment import _semantic_assessment, _required_source_plan
    from apps.api.app.citations.citation_formatter import citation_payload
    folder = Path(folder)
    def chunks(row):
        allowed = {f.name for f in fields(RetrievedChunk)}
        evidence = {e['chunk_id']:e for e in row['authorized_evidence']}
        return [RetrievedChunk(**{k:v for k,v in dict(c,content=evidence[c['chunk_id']]['content']).items() if k in allowed})
                for c in row['raw_response']['retrieved_chunks']]
    class Captured(BaseException):
        pass
    blocked = []
    for segment, cid in [('run','diag-07'),('remaining','diag-11'),('final','diag-12')]:
        row = read(folder/segment/(cid+'.json'))
        captured = []
        def capture(**body):
            body['max_completion_tokens'] = 2048
            captured.append(body)
            raise Captured()
        client = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=capture)))
        try:
            _semantic_assessment(row['request']['question'],
                request_assessment=RequestAssessment.model_validate(row['raw_response']['request_assessment']),
                authorized_chunks=chunks(row), source_plan=_required_source_plan(row['request']['question']),
                route='hybrid_semantic', client=client, emit_telemetry=False)
        except Captured:
            pass
        assert len(captured) == 1
        bound = len(json.dumps(captured[0],ensure_ascii=False).encode())+2048
        assert bound > 16384
        blocked.append({'case_id':cid,'reconstructed_request':captured[0],
                        'byte_based_input_bound':bound,'allowed_input_bound':16384,
                        'actual_provider_tokens':None,'provider_submission':False})
    # The old implementation is read from Git without changing the checkout.
    old_source = subprocess.check_output(['git','show','d203b4c2:apps/api/app/citations/citation_formatter.py'],cwd=ROOT,text=True)
    old = {}
    exec(compile(old_source,'pre-R3-citation-formatter','exec'),old)
    row = read(folder/'remaining/diag-10.json')
    raw = read(folder/'remaining/raw/call-015.json')
    candidate = json.loads(raw['response']['choices'][0]['message']['content'])
    quote = candidate['citations'][0]
    chunk = next(c for c in chunks(row) if c.chunk_id == quote['chunk_id'])
    before = old['citation_payload'](chunk,citation_text=quote['citation_text'])
    after = citation_payload(chunk,citation_text=quote['citation_text'])
    assert before['citation_text'] not in chunk.content
    assert after['citation_text'] in chunk.content and after['citation_type'] == 'fallback'
    assert after['citation_text'] == row['raw_response']['citations'][0]['citation_text']
    return {'network_calls':0,'blocked_requests':blocked,
            'citation_counterfactual':{'case_id':'diag-10','old_commit':'d203b4c2',
                'raw_model_excerpt':quote['citation_text'],'before':before,'after':after,
                'scope':'Same captured model output, old/current formatter only; not an overall quality comparison'}}


def replay(folder=FOLDER):
    folder = Path(folder)
    run = folder/'run'
    authorization, prepared = read(folder/'authorization.json'), read(folder/'preflight.json')
    assert authorization['preflight_sha256'] == digest(folder/'preflight.json')
    assert prepared['suite_sha256'] == digest(folder/'cases.json')
    assert prepared['runner_sha256'] == digest(ROOT/'scripts/application_reliability_live.py')
    assert all(digest(ROOT/p) == sha for p, sha in prepared['runtime_files_sha256'].items())
    cases = read(folder/'cases.json')['cases']
    first_ledger, first_manifest = read(run/'api-ledger.json'), read(run/'manifest.json')
    remaining = folder/'remaining'
    last_ledger, last_manifest = read(remaining/'api-ledger.json'), read(remaining/'manifest.json')
    continuation = read(folder/'remaining-preflight.json')
    assert continuation['original_manifest_sha256'] == digest(run/'manifest.json')
    assert continuation['original_ledger_sha256'] == digest(run/'api-ledger.json')
    assert continuation['continuation_runner_sha256'] == digest(folder/'remaining-runner-initial.py')
    assert set(first_manifest['rows']).isdisjoint(last_manifest['rows'])
    assert continuation['case_ids'][:4] == list(last_manifest['rows'])
    assert first_ledger['stop_reason'] == 'Chat token bound exceeded' and not first_ledger['unknown_outcome']
    assert last_manifest['status'] == 'interrupted' and last_ledger['stop_reason'] == 'Chat token bound exceeded'
    assert not last_ledger['unknown_outcome']
    final = folder/'final'
    final_manifest, final_ledger = read(final/'manifest.json'), read(final/'api-ledger.json')
    final_plan = read(folder/'final-preflight.json')
    assert final_plan['original_manifest_sha256'] == digest(remaining/'manifest.json')
    assert final_plan['original_ledger_sha256'] == digest(remaining/'api-ledger.json')
    assert final_plan['continuation_runner_sha256'] == digest(ROOT/'scripts/application_reliability_remaining.py')
    assert final_plan['case_ids'] == ['diag-12'] == list(final_manifest['rows'])
    assert final_manifest['status'] == 'interrupted' and final_ledger['stop_reason'] == 'Chat token bound exceeded'
    assert not final_ledger['unknown_outcome']
    ledger_rows = [(run, '', i, row) for i,row in enumerate(first_ledger['calls'])]
    ledger_rows += [(remaining, 'remaining-', i, row) for i,row in enumerate(last_ledger['calls'])]
    ledger_rows += [(final, 'final-', i, row) for i,row in enumerate(final_ledger['calls'])]
    manifests = [(run,first_manifest),(remaining,last_manifest),(final,final_manifest)]
    final_journal = read(final/'additional-spend.json')
    assert all(final_journal['entries'][k] == r for k,r in read(remaining/'additional-spend.json')['entries'].items())
    first_journal = read(run/'additional-spend.json')
    assert all(final_journal['entries'][k] == r for k,r in first_journal['entries'].items())
    prior = prepared['initial_journal']
    assert final_journal['policy_sha256'] == prior['policy_sha256']
    assert all(final_journal['entries'][k] == row for k,row in prior['entries'].items())
    spent = Decimal(0)
    counts, stages = Counter(), Counter()
    per_case = Counter()
    identities = set()
    for segment,prefix,i,row in ledger_rows:
        path = segment/row['raw_path']
        assert row['call_index'] == i and row['raw_sha256'] == digest(path)
        raw = read(path)
        assert request_hash(raw['request']) == row['request_sha256']
        bound, cap, reserved = reservation(raw['request'], row['operation'])
        assert bound == row['input_bound'] and cap == row['output_cap'] and reserved == Decimal(row['reserved_usd'])
        assert row['status'] == 'completed', 'Uncertain outcomes need separate inspection; no complete report'
        charge = response_charge(raw['response'], raw['request']['model'])
        assert charge == Decimal(row['charged_usd']) <= reserved
        usage = raw['response']['usage']
        assert 0 <= usage['prompt_tokens'] == row['input_tokens'] <= bound
        assert 0 <= usage.get('completion_tokens',0) == row['output_tokens'] <= cap
        identity = prefix + row['additional_spend_identity']
        identities.add(identity)
        shared = final_journal['entries'][identity]
        assert shared['status'] == 'settled' and Decimal(shared['accounted_usd']) == charge
        assert shared['result_sha256'] == digest(path) and shared['evidence_sha256'] == row['request_sha256']
        counts[row['operation']] += 1
        per_case[(row['case_id'],row['operation'])] += 1
        schema = raw['request'].get('response_format',{}).get('json_schema',{}).get('name')
        stage = schema or row['operation']
        stages[stage] += 1
        spent += charge
    assert set(final_journal['entries']) - set(prior['entries']) == identities
    assert spent <= Decimal('1') and len(ledger_rows) <= 124 and counts['chat'] <= 84 and counts['embedding'] <= 40
    assert all(count <= (7 if operation == 'chat' else 3) for (_,operation),count in per_case.items())
    assert sum(Decimal(m['charged_usd']) for _,m in manifests) == spent
    assert Decimal(final_manifest['total_diagnostic_usd']) == spent
    remaining_usd = str(Decimal('3.79479490')-spent)
    rows = []
    for case in cases:
        segment, manifest = next((seg,m) for seg,m in manifests if case['case_id'] in m['rows'])
        path = segment/(case['case_id']+'.json')
        assert manifest['rows'][case['case_id']] == digest(path)
        row = read(path)
        answer = row['raw_response']
        assert row['http_status'] == 200 and not row['safety_flags']
        assert row['request']['question'] == case['question']
        evidence = {e['chunk_id']:e for e in row['authorized_evidence']}
        assert set(evidence) == {c['chunk_id'] for c in answer['retrieved_chunks']}
        for source in case['sources']:
            assert digest(ROOT/source['path']) == source['sha256']
        for e in evidence.values():
            assert role_can_access(e['access_roles'], case['user_role'])
            assert e['project_id'] == case['project_id']
            assert e['tenant_id'] == prepared['environment']['settings']['default_demo_tenant_id']
            assert not case.get('department_id') or e['department_id'] == case['department_id']
        quote_findings = []
        for citation in answer['citations']:
            source = evidence[citation['chunk_id']]
            assert citation['document_id'] == source['document_id']
            if citation.get('citation_text') and citation['citation_text'] not in source['content']:
                quote_findings.append(citation['chunk_id'])
        rows.append({'case_id':case['case_id'], 'expected_behavior':case['expected_behavior'],
                     'actual_behavior':answer['response_type'], 'latency_ms':row['latency_ms'],
                     'call_count':sum(count for (cid,_),count in per_case.items() if cid == case['case_id']),
                     'noncontiguous_citation_excerpts':quote_findings,
                     'multi_doc_used':answer['multi_doc_used'],
                     'measurement_status':'blocked_by_local_input_bound' if case['case_id'] in {'diag-07','diag-11','diag-12'} else 'captured'})
    assert len(rows) == 12
    return {'scope':'12-case live development diagnostic; agent source inspection required; no overall score',
            'calls':dict(counts), 'stages':dict(stages), 'charged_usd':str(spent),
            'remaining_usd':remaining_usd, 'application_http_ms':sum(r['latency_ms'] for r in rows),
            'provider_call_ms':sum(r['latency_ms'] for _,_,_,r in ledger_rows), 'rows':rows}


if __name__ == '__main__':
    import argparse
    from scripts.application_reliability_live import write
    parser = argparse.ArgumentParser()
    parser.add_argument('--record', action='store_true')
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    summary = replay()
    if args.record or args.check:
        details = source_diagnostics()
        if args.record:
            write(FOLDER/'receipt-summary.json',summary)
            write(FOLDER/'offline-source-diagnostics.json',details)
        if args.check:
            assert read(FOLDER/'receipt-summary.json') == summary
            assert read(FOLDER/'offline-source-diagnostics.json') == details
        print('Receipt accounting, source custody and local diagnostics replay passed; zero API calls')
    else:
        print(json.dumps(summary, indent=2))
