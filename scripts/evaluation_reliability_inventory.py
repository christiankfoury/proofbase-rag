"""ER1 evidence inventory and frozen diagnostic controls. Offline only."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import socket
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'data/evaluation/evaluation-reliability-diagnosis'
OLD = ROOT / 'data/evaluation/conversation-continuation'
RUNS = {'structured-blind-diagnostic': 'diagnostic',
        'structured-blind-v2-diagnostic': 'diagnostic',
        'structured-blind-v2-calibration': 'calibration'}


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + '\n', encoding='utf-8')


def controls(case, packet):
    rows = []
    def add(name, expected, rationale, mutate=None):
        c, a, b = deepcopy(case), deepcopy(packet), deepcopy(packet)
        if mutate:
            mutate(c, a, b)
        rows.append(dict(id=name, provenance='synthetic control; agent-authored diagnostic annotation',
                         source_case=case['id'], rationale=rationale, expected=expected,
                         case=c, first=a, second=b))
    add('identity', 'equivalent', 'Identical complete judgments preserve all dimensions.')
    add('fact-order', 'equivalent', 'Fact IDs, not list position, bind required coverage.',
        lambda c,a,b: b['facts'].reverse())
    add('witness-order', 'equivalent', 'Ordering exact witnesses does not change their union.',
        lambda c,a,b: b['claims'][0]['readings'][0]['source_spans'].reverse())
    add('reason-prose', 'equivalent', 'Free-form justification changes alone are not a verdict change.',
        lambda c,a,b: b.update(behavior_reason='Same complete behavior judgment.'))
    add('meaning-whitespace', 'equivalent', 'Whitespace in interpretation prose is nonsemantic.',
        lambda c,a,b: b['claims'][0]['readings'][0].update(meaning='  '+b['claims'][0]['readings'][0]['meaning']+'  '))
    def broader(c,a,b):
        for k, key in [('source_spans','R1'), ('citation_spans','C1')]:
            b['claims'][0]['readings'][0][k] = [dict(id=key, span=c['inputs']['factual_sources'][0]['text'])]
    add('containing-witness', 'equivalent', 'Same source and meaning; one exact witness contains every narrower witness.', broader)
    def category(c,a,b):
        r=b['claims'][0]['readings'][0]
        r.update(kind='action_order', context_spans=[dict(id='A',span=b['claims'][0]['text'])])
        other=deepcopy(r)
        other.update(kind='presentation_order',plausible=False,meaning='An excluded alternative.',
                     factual_status='unknown',citation_status='unknown',source_spans=[],citation_spans=[])
        # Both packets retain the same excluded meaning; only category assignment differs.
        a['claims'][0]['readings']=deepcopy(b['claims'][0]['readings'])+[deepcopy(other)]
        a['claims'][0]['readings'][0]['kind']='presentation_order'
        a['claims'][0]['readings'][1]['kind']='action_order'
        b['claims'][0]['readings'].append(other)
    add('category-same-meaning', 'equivalent', 'Kinds are taxonomy only when all plausible and excluded meanings match exactly.', category)
    for name, old, new in [('condition','only when','even when'),('modality','may','must'),
                           ('actor','staff','visitors'),('recipient','taxi home','taxi for clients'),
                           ('negation','may','may not'),('scenario-value','38','380')]:
        def change(c,a,b,old=old,new=new):
            r=b['claims'][0]['readings'][0]; r['meaning']=r['meaning'].replace(old,new)
        add(name, 'unresolved', 'Changed interpreted meaning lacks a certified semantic correspondence; never match on aggregate status.', change)
    def status(c,a,b):
        b['claims'][0]['readings'][0].update(factual_status='unknown',citation_status='missing',source_spans=[],citation_spans=[])
    add('real-support-difference','substantively_different','Same claim/meaning has different factual and citation verdicts.',status)
    for i in (0,1):
        add('missing-fact-'+str(i),'substantively_different','Coverage changes on a stable required fact ID.',
            lambda c,a,b,i=i: b['facts'][i].update(status='missing',answer_spans=[]))
    def different_omissions(c,a,b):
        a['facts'][0].update(status='missing',answer_spans=[])
        b['facts'][1].update(status='missing',answer_spans=[])
    add('different-omissions-same-fail','substantively_different','Two failing coverage vectors omit different facts.',different_omissions)
    add('empty-forbidden','equivalent','Existing v2 empty-set projection only; original labels retained.',
        lambda c,a,b: b.update(forbidden_assertion='present'))
    def forbidden(c,a,b):
        c['inputs']['forbidden_assertions']=['An unrelated forbidden promise.']; b['forbidden_assertion']='present'
    add('nonempty-forbidden','substantively_different','Nonempty forbidden sets cannot use empty-set normalization.',forbidden)
    for name, witness in [('invalid-span',dict(id='R1',span='invented')),
                          ('unauthorized-evidence',dict(id='R404',span='invented'))]:
        add(name,'invalid','Exact authorized source witness validation is mandatory.',
            lambda c,a,b,witness=witness: b['claims'][0]['readings'][0].update(source_spans=[witness]))
    add('duplicate-claim','invalid','Duplicates cannot be discarded to produce equivalence.',
        lambda c,a,b: b['claims'].append(deepcopy(b['claims'][0])))
    add('missing-claim','unresolved','No claim correspondence; all_claims_assessed is not a coverage proof.',
        lambda c,a,b: b.update(claims=[]))
    add('malformed','invalid','Malformed output cannot be repaired.',lambda c,a,b: b.pop('facts'))
    def split(c,a,b):
        r=deepcopy(b['claims'][0]); r['text']='up to 38 credits per trip.'; b['claims'].append(r)
    add('split-combined','unresolved','No sound automatic split/merge alignment is declared.',split)
    add('extra-unsupported-claim','unresolved','An extra answer-aligned claim must not disappear.',split)
    def reordered(c,a,b):
        split(c,a,a); split(c,a,b); b['claims'].reverse()
    add('claim-order','equivalent','Complete claim bindings survive list reordering.',reordered)
    add('duplicate-fact','invalid','Required fact IDs must be unique.',
        lambda c,a,b: b['facts'].append(deepcopy(b['facts'][0])))
    add('claim-outside-answer','invalid','Claims must be exact answer spans.',
        lambda c,a,b: b['claims'][0].update(text='Invented assertion absent from answer.'))
    def disjoint(c,a,b):
        a['claims'][0]['readings'][0]['source_spans']=a['claims'][0]['readings'][0]['source_spans'][:1]
        b['claims'][0]['readings'][0]['source_spans']=b['claims'][0]['readings'][0]['source_spans'][1:]
    add('disjoint-witnesses','unresolved','Valid but disjoint source spans cannot prove the same evidential basis.',disjoint)
    return rows


def build():
    from scripts import conversation_ordering_v2 as refs
    from scripts.test_structured_blind_evaluator_v1 import fixture, packet, ambiguous
    cases={s:refs.cases(s)+refs.probes(s) for s in ('diagnostic','calibration')}
    paths=set(); rows=[]
    for run, stage in RUNS.items():
        paths.update((OLD/run).rglob('*.json'))
        manifest=read(OLD/run/'run/manifest.json')
        for case in cases[stage]:
            candidates=[OLD/run/'run'/(case['id']+'.json'),OLD/run/'run'/(case['id']+'-probe.json')]
            p=next((p for p in candidates if p.exists()),None)
            rows.append(dict(run=run,stage=stage,id=case['id'],case=case,
                             status='saved' if p else 'not_executed',
                             reason='Captured before frozen early stop.' if p else 'Stage stopped before this input; no invented observation.',
                             path=p.relative_to(ROOT).as_posix() if p else None,
                             runtime_commit=manifest['runtime_commit']))
    # No holdouts opened. These are already exposed development/control inputs.
    paths.update((OLD/'ordering-contract-v2').glob('*.json'))
    paths.update((OLD/'structured-blind-v1').glob('*.json'))
    paths.update((OLD/'structured-blind-v2').glob('*.json'))
    for run in ('grader-v34-calibration','grader-v35-calibration'):
        paths.update((OLD/run).rglob('*.json'))
    paths.update([OLD/'development-v2.json',OLD/'development-v3.json',OLD/'application-selection-v2.json'])
    # Bind loaded contract/reference implementation dependencies as well.
    import sys
    for module in tuple(sys.modules.values()):
        p=getattr(module,'__file__',None)
        if p and Path(p).resolve().is_relative_to(ROOT/'scripts'):
            paths.add(Path(p).resolve())
    c,g=fixture(); matrix=controls(c,packet(g))
    c,a=ambiguous(); b=deepcopy(a)
    matrix.append(dict(id='ambiguous-identical',provenance='synthetic control',source_case=c['id'],
                       rationale='Identical uncertainty stays uncertain, with no target credit.',expected='equivalent',case=c,first=a,second=b))
    b=deepcopy(a); b['claims'][0]['readings'][1].update(plausible=False,factual_status='unknown',citation_status='unknown',source_spans=[],citation_spans=[])
    matrix.append(dict(id='ambiguity-erased',provenance='synthetic control',source_case=c['id'],
                       rationale='A plausible reading becoming excluded is material.',expected='substantively_different',case=c,first=a,second=b))
    save(OUT/'er1/v1/inventory.json',dict(version='er1.v1',selection='All structured v1/v2 executed diagnostic/calibration cases and probes; all unexecuted slots; full predecessor calibration files for known failure families. No fresh holdouts.',
         files=[dict(path=p.relative_to(ROOT).as_posix(),sha256=sha(p)) for p in sorted(paths) if p.name!='evaluation_reliability_inventory.py'],rows=rows,
         absent_runs=[dict(run='structured-blind-v1-calibration',reason='v1 stopped in diagnostic; no calibration observations')],
         annotation_provenance='Frozen references retained verbatim; new interpretations are agent diagnostic annotations, not human adjudication.'))
    save(OUT/'er1/v1/matrix.json',dict(version='er1.v1',controls=matrix,release_eligible=False,target_credit=False))


def verify():
    inventory=read(OUT/'er1/v1/inventory.json')
    for row in inventory['files']:
        if sha(ROOT/row['path'])!=row['sha256']:
            raise ValueError('Evidence changed: '+row['path'])
    print(f"Verified {len(inventory['files'])} immutable bindings; {len(inventory['rows'])} execution slots")


if __name__=='__main__':
    import sys
    with patch.object(socket.socket,'connect',side_effect=AssertionError('Offline only')):
        if '--build' in sys.argv: build()
        verify()
