"""Publish readable dimension reports from immutable saved judgments; no model calls."""
import argparse
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.reanalyze_saved_answers import OUT,FOLDER,DIMS,build_inputs,code_hashes
from scripts.dimension_grader import dimensions
from scripts.fresh_eval_protocol import digest,verify_custody
from scripts.fresh_eval_budget import Ledger
from collections import Counter
from scripts.reliable_evaluation_run import write_json_atomic
LABELS={'factual_support':'Factual support in available evidence','completeness':'Required-fact coverage','relevance':'Relevance to the question','citation_support':'Support in cited chunks','quotation_fidelity':'Contiguous quotation formatting','response_behavior':'Meaning of response behavior'}


def read_json(path):
    return json.loads(path.read_text(encoding='utf-8'))


def comparable_dimensions(saved, canonical_inputs, payload, evidence, safety):
    original=dimensions(saved['inputs'],saved.get('grade'),payload,evidence,safety)
    if original!=saved['dimensions']:raise ValueError('Saved dimension verdict changed')
    result=dict(original)
    mismatches=[k for k in canonical_inputs if canonical_inputs[k]!=saved['inputs'].get(k)]
    if mismatches:
        # Only the observed, reversible UTF-8-as-Windows-1252 answer mismatch is classified.
        # Never normalize it away or accept its semantic judgments as original-answer results.
        try:known=canonical_inputs['answer'].encode('utf-8').decode('cp1252')==saved['inputs']['answer']
        except UnicodeError:known=False
        if mismatches!=['answer'] or not known:raise ValueError('Unexpected model input mismatch')
        for k in DIMS:
            if k!='quotation_fidelity':result[k]='unresolved'
        result['forbidden_assertion']='unresolved'
        result['input_integrity']='utf8_decoded_as_cp1252'
    else:result['input_integrity']='exact'
    return result


def replay():
    _,suite=verify_custody(require_current=False)
    manifest=read_json(OUT/'manifest.json');freeze=read_json(OUT/'freeze.json')
    if freeze['code_hashes']!=code_hashes() or freeze['calibration_sha256']!=digest(OUT/'calibration.json'):raise ValueError('Frozen evaluator changed')
    for name,key in [('holdout.json','source_suite_sha256'),('public-report.json','original_report_sha256'),('api-ledger.json','original_ledger_sha256')]:
        if digest(FOLDER/name)!=manifest[key]:raise ValueError('Original evidence changed')
    previous=read_json(FOLDER/'api-ledger.json');ledger=read_json(OUT/'api-ledger.json')
    if ledger['calls'][:len(previous['calls'])]!=previous['calls'] or ledger['limit_usd']!=.75:raise ValueError('Budget history changed')
    rows=[]
    for c in suite['cases']:
        cid=c['case_id'];path=OUT/'rows'/f'{cid}.json';source=FOLDER/'run-v2'/path.name
        if digest(source)!=manifest['source_records'][cid]:raise ValueError('Original response changed')
        if not path.exists():continue
        saved=read_json(path);original=read_json(source)
        if saved['case_id']!=cid or saved['source_sha256']!=digest(source):raise ValueError('Row custody mismatch')
        canonical=build_inputs(c,original)
        d=comparable_dimensions(saved,canonical,original['raw_response'],original['authorized_evidence'],original['safety_flags'])
        rows.append({'case_id':cid,'original_passed':original['passed'],'dimensions':d,'record_sha256':digest(path)})
    spent=sum(c['charged_usd'] for c in ledger['calls'])
    return {'version':manifest['version'],'kind':'saved_response_evaluator_reanalysis','cases_expected':60,'cases_processed':len(rows),'complete':len(rows)==60,
        'original_protocol_passes':33,'original_protocol_total':60,'human_review':'not_completed',
        'dimensions':{k:dict(Counter(r['dimensions'][k] for r in rows)) for k in DIMS},
        'invalid_grades':sum(bool(r['dimensions']['grader_errors']) for r in rows),
        'input_mismatch_cases':[r['case_id'] for r in rows if r['dimensions']['input_integrity']!='exact'],
        'cumulative_cost_usd':spent,'reanalysis_cost_usd':spent-manifest['original_cost_usd'],'cases':rows,
        'limitation':'Separate model judgments, not human accuracy or runtime improvement. Four known input-encoding mismatches remain unresolved; no composite rate.'}


def products():
    report=replay()
    summary={k:v for k,v in report.items() if k!='cases'}
    summary['suitable_for_release_gate']=False
    summary['audit_warning']='Agent inspection found false positives and a missed omission. Model labels are diagnostic, not confirmed error counts.'
    summary['dimensions']={k:{status:report['dimensions'][k].get(status,0) for status in ['pass','fail','unresolved','not_applicable']} for k in DIMS}
    suite=read_json(FOLDER/'holdout.json');cases={c['case_id']:c for c in suite['cases']}
    lines=['# Saved-answer reanalysis by dimension','','This reanalyzes the same Phase 65 responses. It is **not a new application run**, human review, or an improvement measurement. The original 33/60 (55.0%) protocol result is unchanged. There is deliberately no composite pass rate.','',f"Processed: {report['cases_processed']}/60. Invalid grader outputs: {report['invalid_grades']}. Unresolved means the evaluator could not establish a judgment; it is neither a pass nor a proven factual error.",'','| Dimension | Pass | Fail | Unresolved | Not applicable |','|---|---:|---:|---:|---:|']
    for k,v in summary['dimensions'].items():lines.append(f"| {LABELS[k]} | {v['pass']} | {v['fail']} | {v['unresolved']} | {v['not_applicable']} |")
    lines+=['','Factual-support failure means the model judged at least one assertion contradicted by the available authorized evidence. Unsupported additions without contradictory evidence remain unresolved. A factually supported answer can still answer the wrong question or omit required facts. Pure non-answers have no factual claims to assess. Citation support uses full cited chunks, while quotation formatting checks the displayed excerpt separately. These are model judgments, not human labels.','','## Cases flagged by the model (not confirmed errors)','']
    for k in DIMS:
        ids=[r['case_id'] for r in report['cases'] if r['dimensions'][k]=='fail']
        lines.append(f"- {LABELS[k]} failures: "+(', '.join(f'[{cid}](case-review.md#{cid})' for cid in ids) or 'none recorded')+'.')
    unresolved=[r['case_id'] for r in report['cases'] if any(r['dimensions'][k]=='unresolved' for k in DIMS)]
    lines+=['- Unresolved in one or more dimensions: '+(', '.join(unresolved) or 'none')+'.','',
        '## Semantic audit warning','',
        '**This reanalysis is not reliable enough for release gating or a factual-error headline.** Agent inspection disputes the lone model factual-failure label (fresh-010), a completeness pass (fresh-012), a citation failure on a pure refusal (fresh-026), and behavior failures for appropriate non-answers (fresh-045 and fresh-060). The wrong-topic finding in fresh-019 is confirmed by source/context inspection. These examples are not exhaustive. The raw model labels remain unchanged; do not treat their counts as confirmed errors. See [agent findings](../../data/evaluation/dimension-reanalysis-v1/agent-review.json).','',
        '## Custody and limitations','',
        'The first aggregation failed on Windows because JSON was read with the platform default encoding. UTF-8 byte comparison found four mismatched model inputs (fresh-048, 051, 052, 053). Those saved judgments remain immutable but their semantic dimensions are unresolved. No retries were made. The new offline publisher reads explicit UTF-8 and validates the exact known mismatch; any other input difference fails verification.','',
        '[Per-case questions, expected facts, actual answers and judgments](case-review.md) | [Design and calibration history](design.md) | [Original result](../phase-65/results.md) | [Machine-readable reanalysis](../../data/evaluation/dimension-reanalysis-v1/report.json)','',
        f"Evaluator: `{report['version']}`. Final visible calibration passed 12/12 after four preserved failed attempts; this is development calibration, not held-out grader accuracy. The evaluator was frozen before reanalysis. It has already been informed by the original failures, so this exposed suite cannot establish evaluator generalization.",'',
        'Claim verification cannot see the question or expected facts. It checks all answer assertions against authorized saved chunks and verified role-authorized reference quotes. A separate call compares answer meaning with required facts and conversation context. Gold quotes cannot establish citation support. Neither call sees the old grades. The available evidence is not an exhaustive world model; lack of support does not establish falsity.','',
        'The user accepted prior agent observations, but no individual human decisions were supplied. That agreement is not recorded as completed human adjudication. Model judgments and the original review fields remain separate.','',
        f"Cumulative API token-cost estimate: ${report['cumulative_cost_usd']:.6f}; this phase including calibration: ${report['reanalysis_cost_usd']:.6f}. The original $0.75 shared ceiling remains enforced. No new application queries or embeddings were made.",'',
        'Offline checks: `python scripts/report_dimension_reanalysis.py --check` (explicit UTF-8 and input-integrity accounting). These reproduce hashes, input boundaries, grading contracts and totals, not semantic truth. Original checks remain `python scripts/report_fresh_eval.py --check` and its `--archive` variant. No selective retries or original-row edits are permitted.','']
    packet=['# Per-case saved-answer review','','Agent/model reanalysis only. Original answers and expected labels are unchanged. Status **fail** applies to the named dimension only. **Unresolved** is not a finding that the answer is false. For source evidence, open each saved reanalysis row; source IDs R/G refer to factual evidence, and C IDs to actual cited chunks.','']
    for result in report['cases']:
        cid=result['case_id'];case=cases[cid];saved=read_json(OUT/'rows'/f'{cid}.json');d=result['dimensions'];g=saved.get('grade') or {}
        packet += [f'## {cid}','',f"**Question:** {case['question']}",'']
        for t in case.get('previous_turns',[]):packet += [f"Prior {t['role']}: {t['content']}",'']
        packet += ['**Expected information:**','']
        packet += [f"- {f['text']} [Source](../../{f['source_path']})" for f in case['required_facts']] or [f"Expected behavior: {case['expected_behavior']}."]
        packet += ['',f"**Actual system answer:** {read_json(FOLDER/'run-v2'/f'{cid}.json')['raw_response']['answer']}",'','| Dimension | Judgment |','|---|---|']
        packet += [f'| {LABELS[k]} | {d[k]} |' for k in DIMS]
        packet += ['',f"Original protocol: {'pass' if result['original_passed'] else 'fail'}. Response metadata matches expectation: {d['response_type_match']}. Grader errors: {', '.join(d['grader_errors']) or 'none'}. Input integrity: {d['input_integrity']}.",'']
        if cid in {r['case_id'] for r in read_json(OUT/'agent-review.json')['cases']}:
            review=next(r for r in read_json(OUT/'agent-review.json')['cases'] if r['case_id']==cid)
            packet += [f"**Separate agent inspection:** {review['finding']}. {review['reason']}",'']
        if d['input_integrity']!='exact':packet += ['**Encoding issue:** the model received a misdecoded apostrophe. Its judgments below are preserved for inspection but excluded from semantic results.','']
        for claim in g.get('claims',[]):
            packet += [f"- Claim: {claim['text']} â€” {claim['kind']}; factual: {claim['factual_status']}; cited support: {claim['citation_status']}. {claim['reason']}"]
        for fact in g.get('facts',[]):packet += [f"- Required fact {fact['fact_id']}: {fact['status']}. {fact['reason']}"]
        for key in ['relevance','behavior']:
            if key in g:packet += [f"- {key}: {g[key]['reason']}"]
        packet += ['',f'[Original response](../../data/evaluation/fresh-current/run-v2/{cid}.json) | [Reanalysis inputs, sources and judgments](../../data/evaluation/dimension-reanalysis-v1/rows/{cid}.json)','']
    return summary,'\n'.join(line.rstrip() for line in lines),'\n'.join(line.rstrip() for line in packet)


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--check',action='store_true');args=ap.parse_args()
    summary,report,packet=products()
    machine=replay()
    targets={ROOT/'docs/phase-66/results.md':report,ROOT/'docs/phase-66/case-review.md':packet}
    if args.check:
        assert read_json(OUT/'report.json')==machine
        assert read_json(OUT/'public-summary.json')==summary
        for p,text in targets.items():assert p.read_text(encoding='utf-8')==text,str(p)
        print('Readable reanalysis report and dashboard summary match saved judgments')
    else:
        write_json_atomic(OUT/'report.json',machine)
        write_json_atomic(OUT/'public-summary.json',summary)
        for p,text in targets.items():p.write_text(text,encoding='utf-8')

if __name__=='__main__':main()
