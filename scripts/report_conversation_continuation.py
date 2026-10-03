"""Offline cumulative receipt and application evidence replay across iterations."""
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.conversation_continuation import FOLDER,PREVIOUS,prefix,read,digest,write
from scripts.bounded_redesign_run import request_hash,response_charge
from scripts.bounded_redesign_preflight import prepare


def report():
    spending=prefix();rows=[]
    for manifest_path in sorted(FOLDER.glob('*/run/manifest.json')):
        folder=manifest_path.parent;manifest=read(manifest_path);plan=read(folder.parent/'preflight.json');ledger=read(folder/'api-ledger.json')
        assert manifest['status']=='complete' and not ledger['stopped']
        assert manifest['ledger_sha256']==digest(folder/'api-ledger.json')
        assert manifest['preflight_sha256']==digest(folder.parent/'preflight.json')
        assert ledger['prefix']==plan['prefix']
        for path,h in plan['prefix']['ledger_sha256'].items():assert digest(ROOT/path)==h
        for path,h in plan['bindings'].items():
            blob=subprocess.check_output(['git','show',manifest['runtime_commit']+':'+path],cwd=ROOT)
            # Git stores LF; freeze hashes retain the Windows checkout's bytes.
            normalized=blob.replace(b'\r\n',b'\n')
            representations={hashlib.sha256(value).hexdigest() for value in (blob,normalized,normalized.replace(b'\n',b'\r\n'))}
            if h not in representations:
                # Some historical checkouts contain mixed line endings. Retain
                # exact freeze bytes AND prove their normalized committed content.
                current=(ROOT/path).read_bytes()
                assert hashlib.sha256(current).hexdigest()==h and current.replace(b'\r\n',b'\n')==normalized,path
        suite=read(ROOT/plan.get('suite_path','data/evaluation/bounded-redesign/development.json'))
        expected={(x['case_id'],x['turn']) for x in plan['turns']};seen=set();quotes=0
        for item in manifest['rows']:
            assert item['sha256']==digest(folder/item['path']);result=read(folder/item['path'])
            case=next(c for c in suite['cases'] if c['id']==item['case_id'])
            allowed={s['chunk_id']:s['content'] for s in suite['sources'] if s['chunk_id'] in case['source_ids'] and suite['role'] in s['access_roles']}
            assert {s['chunk_id']:s['content'] for s in result['authorized_evidence']}==allowed
            for turn in result['turns']:
                key=(case['id'],turn['turn']);assert key not in seen;seen.add(key)
                assert turn['question']==case['turns'][turn['turn']]
                answer=turn['final_response'];assert 'BLUE-CROWN-SECRET' not in answer.get('answer','')
                if case['id']=='dev-10':assert not allowed and '720' not in json.dumps(answer)
                for citation in answer.get('citations',[]):
                    assert citation['citation_text'] and citation['citation_text'] in allowed[citation['chunk_id']];quotes+=1
                immediate=read(folder/f"{case['id']}-turn-{turn['turn']}.json")
                assert immediate==dict(turn,authorized_evidence=result['authorized_evidence'])
        assert seen==expected
        amount=Decimal(0)
        for call in ledger['calls']:
            raw=read(folder/call['raw_path']);assert request_hash(raw['request'])==call['request_sha256']
            body,limits=prepare(raw['request']);assert body==raw['request']
            assert all(call[k]==v for k,v in limits.items())
            usage=raw['response']['usage'];assert 0<=usage['prompt_tokens']<=limits['input_bound'] and 0<=usage['completion_tokens']<=limits['output_cap']
            value=response_charge(raw['response'],body['model']);assert value<=Decimal(call['reserved_usd'])
            assert 'policy-private' not in json.dumps(body['messages']) and 'EUR 720' not in json.dumps(body['messages'])
            amount+=value
        assert amount==Decimal(manifest['new_spend_usd'])
        assert amount+Decimal(plan['prefix']['spent_usd'])==Decimal(manifest['cumulative_usd'])
        rows.append(dict(step=folder.parent.name,profile=plan['profile'],calls=len(ledger['calls']),turns=len(seen),
            cost_usd=str(amount),exact_authorized_quotations=quotes,manifest_sha256=digest(manifest_path)))
    result=dict(cumulative_spent_usd=spending['spent_usd'],remaining_usd=str(Decimal('12.50')-Decimal(spending['spent_usd'])),
        unknown_reservations_usd='0',prior_comparison_spend_usd='.1529816',runs=rows,
        note='Receipt/custody/quotation checks only; semantic outcomes require separate source inspection.')
    write(FOLDER/'receipt-summary.json',result);print(json.dumps(result,indent=2))


if __name__=='__main__':report()
