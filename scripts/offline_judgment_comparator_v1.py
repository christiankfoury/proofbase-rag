"""Conservative comparison.v1. No provider client, scoring or release integration."""
from collections import Counter
from copy import deepcopy
import json
import socket
from unittest.mock import patch
from scripts import structured_blind_evaluator_v2 as frozen
from scripts.evaluation_reliability_inventory import ROOT, OUT, read, save, verify, sha

VERSION = 'comparison.v1'


def words(value):
    return ' '.join(value.split())


def witnesses_equal(first, second):
    """Exact witnesses already validated; containment cannot cross source IDs."""
    def covered(left, right):
        return all(any(i == j and (s in t or t in s) for j,t in right) for i,s in left)
    a={(w['id'],w['span']) for w in first}
    b={(w['id'],w['span']) for w in second}
    return covered(a,b) and covered(b,a)


def validate(case, packet):
    inputs=case['inputs']
    try:
        errors=[]
        for field, key in [('factual_sources','source_id'),('cited_sources','citation_id'),('required_facts','fact_id')]:
            ids=[x[key] for x in inputs[field]]
            if len(ids)!=len(set(ids)): errors.append('duplicate_input_binding')
        source_ids={s['source_id'] for s in inputs['factual_sources']}
        if any(s['source_id'] not in source_ids for s in inputs['cited_sources']):
            errors.append('unbound_cited_source')
        grade, invalid=frozen.project(inputs,packet)
        errors.extend(invalid)
        if grade is not None:
            facts=[f['fact_id'] for f in grade['facts']]
            if len(facts)!=len(set(facts)): errors.append('duplicate_fact')
            for c in packet['claims']:
                if not c['text'].strip() or c['text'] not in inputs['answer']:
                    errors.append('claim_not_answer_span')
                meanings=[words(r['meaning']) for r in c['readings']]
                if len(meanings)!=len(set(meanings)): errors.append('duplicate_meaning')
        return grade,sorted(set(errors))
    except (KeyError,TypeError,ValueError,AttributeError):
        return None,['malformed_input_or_packet']


def compare(case, first, second):
    """Retain originals; normalize bindings only; never certify entailment."""
    a,ae=validate(case,first); b,be=validate(case,second)
    trace=[]; different=[]; unresolved=[]
    result=dict(version=VERSION,release_eligible=False,target_credit=False,
                originals=[deepcopy(first),deepcopy(second)],errors=[ae,be],
                normalizations=trace,differences=different,unresolved=unresolved)
    if ae or be:
        return dict(result,outcome='unresolved_invalid',status='invalid')
    checks=frozen.legacy.dimensions(case['inputs'],a,case['payload'],case['evidence'],case['safety_flags'])
    result['deterministic_checks']={k:deepcopy(checks[k]) for k in
        ('quotation_fidelity','nonexact_quotes','unmatched_citations','response_type_match')}
    if case['inputs']['forbidden_assertions']==[]:
        trace.append(dict(rule='empty_forbidden_set',original=[first['forbidden_assertion'],second['forbidden_assertion']],projected='absent'))
    for field in ('actual_behavior','forbidden_assertion'):
        if a[field]!=b[field]: different.append(field)
    if a['relevance']['status']!=b['relevance']['status']: different.append('relevance')
    facts=[{f['fact_id']:f for f in g['facts']} for g in (a,b)]
    if facts[0].keys()!=facts[1].keys():
        unresolved.append('fact_correspondence')
    else:
        for key in sorted(facts[0]):
            x,y=facts[0][key],facts[1][key]
            if x['status']!=y['status']: different.append('fact:'+key)
            elif not witnesses_equal([dict(id='A',span=s) for s in x['answer_spans']],
                                     [dict(id='A',span=s) for s in y['answer_spans']]):
                unresolved.append('fact_witness:'+key)
            elif x['answer_spans']!=y['answer_spans']:
                trace.append(dict(rule='fact_witness_containment_or_order',fact_id=key,before=[x['answer_spans'],y['answer_spans']]))
    claims=[{c['text']:c for c in p['claims']} for p in (first,second)]
    if claims[0].keys()!=claims[1].keys(): unresolved.append('claim_correspondence')
    for key in sorted(claims[0].keys() & claims[1].keys()):
        x,y=claims[0][key],claims[1][key]
        readings=[{words(r['meaning']):r for r in c['readings']} for c in (x,y)]
        if readings[0].keys()!=readings[1].keys():
            unresolved.append('meaning_correspondence:'+key)
            continue
        for meaning in sorted(readings[0]):
            left,right=readings[0][meaning],readings[1][meaning]
            for field in ('plausible','factual_status','citation_status'):
                if left[field]!=right[field]: different.append(field+':'+key+':'+meaning)
            for field in ('context_spans','source_spans','citation_spans'):
                if not witnesses_equal(left[field],right[field]): unresolved.append(field+':'+key+':'+meaning)
                elif left[field]!=right[field]: trace.append(dict(rule='validated_witness_containment_or_order',claim=key,meaning=meaning,field=field,before=[left[field],right[field]]))
            if left['kind']!=right['kind']:
                trace.append(dict(rule='category_same_complete_meaning',claim=key,meaning=meaning,before=[left['kind'],right['kind']]))
            if left['meaning']!=right['meaning']:
                trace.append(dict(rule='meaning_whitespace',claim=key,before=[left['meaning'],right['meaning']],after=meaning))
    # Ordering is explicit in the trace; originals retain reason prose/witnesses.
    trace.append(dict(rule='stable_claim_and_fact_order',claim_keys=sorted(claims[0]),fact_keys=sorted(facts[0]),
                      ignored_fields=['reason','context_reason','behavior_reason','relevance.reason']))
    status='substantively_different' if different else 'unresolved' if unresolved else 'equivalent'
    return dict(result,outcome='unresolved_invalid' if status=='unresolved' else status,status=status,
                recorded_safety_flags=deepcopy(case['safety_flags']))


def compact(result):
    return {k:v for k,v in result.items() if k!='originals'}


def outcome(status):
    return 'unresolved_invalid' if status in ('unresolved','invalid') else status


def report():
    verify()
    matrix=read(OUT/'er1/v1/matrix.json')['controls']; controls=[]
    for row in matrix:
        result=compare(row['case'],row['first'],row['second'])
        case=row['case']
        baseline=frozen.compare(case['inputs'],case['payload'],case['evidence'],case['safety_flags'],row['first'],row['second'])
        controls.append(dict(id=row['id'],expected=row['expected'],matched=result['outcome']==outcome(row['expected']),
                             subtype_matched=result['status']==row['expected'],
                             baseline_status=baseline['status'],
                             source='er1/v1/matrix.json',comparison=compact(result)))
    inventory=read(OUT/'er1/v1/inventory.json'); replay=[]
    for row in inventory['rows']:
        if not row['path']: continue
        saved=read(ROOT/row['path']); case=row['case']
        # Probe review is a verdict ABOUT the supplied candidate, not judge B.
        second_key='second' if 'second' in saved else 'review'
        result=compare(case,saved['grade'],saved[second_key])
        baseline=frozen.compare(case['inputs'],case['payload'],case['evidence'],case['safety_flags'],saved['grade'],saved[second_key])
        replay.append(dict(run=row['run'],id=row['id'],path=row['path'],sha256=sha(ROOT/row['path']),
                           packet_fields=['grade',second_key],
                           baseline_status=baseline['status'],baseline_dimensions=baseline['dimensions'],
                           comparison=compact(result)))
    return dict(version=VERSION,release_eligible=False,target_credit=False,
                input_bindings={p:sha(OUT/p) for p in ['er1/v1/inventory.json','er1/v1/matrix.json']},
                controls=controls,controls_by_expected=dict(Counter(r['expected'] for r in controls)),
                false_matches=sum(r['expected']!='equivalent' and r['comparison']['status']=='equivalent' for r in controls),
                missed_matches=sum(r['expected']=='equivalent' and r['comparison']['status']!='equivalent' for r in controls),
                replay=replay,replay_counts=dict(Counter(r['comparison']['status'] for r in replay)),
                replay_labeled_accuracy=None,reason='No independent gold equivalence labels for saved pairs; counts are diagnostic outcomes only.',
                missing_slots=sum(not r['path'] for r in inventory['rows']),new_model_calls=0,new_cost_usd='0')


if __name__=='__main__':
    import sys
    with patch.object(socket.socket,'connect',side_effect=AssertionError('Offline only')):
        result=report(); path=OUT/'er2/v1/report.json'
        if '--write' in sys.argv: save(path,result)
        else:
            if read(path)!=result: raise ValueError('Replay differs from saved report')
        print(json.dumps({k:v for k,v in result.items() if k not in {'controls','replay'}},indent=2))
