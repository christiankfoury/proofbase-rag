"""Offline structured interpretations and blind comparison; no provider client.

Request plans precede judgments. Expected verdicts never enter request plans.
Agreement is a candidate result, not qualification or permission to activate.
"""
from copy import deepcopy
from decimal import Decimal
from types import SimpleNamespace

from scripts import quality_eval_contract_v35 as legacy
from scripts import quality_eval_transport_v35 as transport
from scripts.conversation_blind_review_design import INPUT_KEYS
from scripts.fresh_eval_grader import matches_schema

VERSION = 'structured-blind.v1-offline'
KEYS = (*legacy.DIMENSIONS, 'forbidden_assertion')
STRUCTURED = """
Return structured interpretations instead of one final support verdict per claim.
Keep the complete original claim text. For a claim without an ordering reading,
return one literal reading. For any potential action-versus-presentation ordering,
return BOTH action_order and presentation_order readings, including excluded ones.
Describe each meaning and whether the WHOLE question/history/answer permits it.
Plausible means not resolved away by context; uncertainty must not become exclusion.
Excluded readings require exact context witnesses and a concise explanation.
Context IDs are Q for question, A for answer, H0, H1, ... for history content.
Context witnesses identify meaning only; they NEVER prove policy or grant access.

For EACH plausible reading, separately judge complete factual/citation support
using the unchanged evidence rules and exact witnesses. Excluded readings have
unknown/unknown statuses and empty source/citation witnesses. Do not choose one
plausible reading because it is easier to support. Code, not a final model label,
will resolve materially different support across plausible readings to unknown.
All other substantive assertions still need their own complete assessment.
The caller supplies no other judge's answer, reference label, or candidate review.
"""


def obj(properties):
    return dict(type='object', additionalProperties=False,
                required=list(properties), properties=properties)


def claims_schema():
    original = legacy.schema()['properties']['claims']['items']['properties']
    text = dict(type='string')
    reading = obj(dict(
        kind=dict(type='string', enum=['literal', 'action_order', 'presentation_order']),
        meaning=text, plausible=dict(type='boolean'), context_reason=text,
        context_spans=dict(type='array', items=obj(dict(id=text, span=text))),
        **{k: deepcopy(original[k]) for k in
           ('factual_status', 'citation_status', 'source_spans', 'citation_spans', 'reason')}))
    return obj(dict(claims=dict(type='array', items=obj(dict(
        text=text, readings=dict(type='array', items=reading)))),
        all_claims_assessed=dict(type='boolean')))


def request_plan(inputs):
    if set(inputs) - INPUT_KEYS:
        raise ValueError('Only original evidence inputs are permitted')
    result = []
    for judge in ('a', 'b'):
        for purpose, body in transport.initial_requests(deepcopy(inputs)):
            if purpose == 'claims':
                body['messages'][0]['content'] = legacy.CLAIM_PROMPT + STRUCTURED
                body['response_format']['json_schema']['schema'] = claims_schema()
            # Coverage body is byte-for-byte equivalent to the frozen V35 body.
            result.append(dict(judge=judge, purpose=purpose, body=body))
    return result


def full_reservation(inputs):
    return sum((transport.reserve(r['body'])['reserved_usd']
                for r in request_plan(inputs)), Decimal(0))


def replay_packets(inputs, receipts):
    """Read already-received raw envelopes; one distinct response per planned call.

    This is structural replay, not a spend-ledger/custody certificate. A future
    runner must additionally bind every receipt to its journal and frozen plan.
    """
    plan = request_plan(inputs)
    names = {r['judge'] + '.' + r['purpose'] for r in plan}
    if set(receipts) != names:
        raise ValueError('Exactly four blind receipts required')
    packets, response_ids = {'a': {}, 'b': {}}, set()
    for item in plan:
        raw = receipts[item['judge'] + '.' + item['purpose']]
        if raw['status'] != 'received' or raw['request'] != item['body']:
            raise ValueError('Unsettled or changed request')
        response = raw['response']
        identifier = response.get('id')
        if not isinstance(identifier, str) or not identifier or identifier in response_ids:
            raise ValueError('Duplicate/missing response identity; blind draws cannot be copied')
        if response.get('model') != item['body']['model']:
            raise ValueError('Unexpected model')
        response_ids.add(identifier)
        choices = [SimpleNamespace(finish_reason=c['finish_reason'],
                    message=SimpleNamespace(**c['message'])) for c in response['choices']]
        part = transport.parsed(SimpleNamespace(choices=choices),
                                item['body']['response_format']['json_schema']['schema'])
        packets[item['judge']].update(part)
    return packets['a'], packets['b']


def _context(inputs):
    return dict(Q=inputs['question'], A=inputs['answer'], **{
        'H'+str(i): turn['content']
        for i, turn in enumerate(inputs['history_not_evidence'])})


def project(inputs, packet):
    """Validate every reading before deterministic projection; never repair a packet."""
    full = deepcopy(legacy.schema())
    full['properties']['claims'] = claims_schema()['properties']['claims']
    if not matches_schema(packet, full):
        return None, ['structured_schema']
    grade = {k: deepcopy(v) for k, v in packet.items() if k != 'claims'}
    grade['claims'] = []
    errors, context, seen = [], _context(inputs), set()
    for claim in packet['claims']:
        if claim['text'] in seen:
            errors.append('duplicate_claim')
        seen.add(claim['text'])
        readings = claim['readings']
        kinds = sorted(r['kind'] for r in readings)
        if kinds not in (['literal'], ['action_order', 'presentation_order']):
            errors.append('reading_coverage')
        plausible = [r for r in readings if r['plausible']]
        if not plausible:
            errors.append('no_plausible_reading')
        for reading in readings:
            if not reading['meaning'].strip() or not reading['context_reason'].strip():
                errors.append('empty_interpretation_reason')
            spans = reading['context_spans']
            if any(w['id'] not in context or not w['span'].strip()
                   or w['span'] not in context[w['id']] for w in spans):
                errors.append('context_witness_invalid')
            if reading['kind'] != 'literal' and not spans:
                errors.append('context_witness_required')
            if not reading['plausible'] and (
                    reading['factual_status'] != 'unknown' or reading['citation_status'] != 'unknown'
                    or reading['source_spans'] or reading['citation_spans']):
                errors.append('excluded_reading_has_verdict')
            if reading['factual_status'] == 'unknown' and reading['source_spans']:
                errors.append('unknown_has_source_witness')
            if reading['citation_status'] != 'supported' and reading['citation_spans']:
                errors.append('unsupported_has_citation_witness')
            # The inherited validator checks authorized IDs, exact spans, label
            # compatibility, all fact IDs and all behavior/speech-act invariants.
            single = deepcopy(grade)
            single['claims'] = [dict(text=claim['text'], **{
                k: deepcopy(reading[k]) for k in ('factual_status', 'citation_status',
                                                'source_spans', 'citation_spans', 'reason')})]
            errors.extend(legacy.validate(single, inputs))
        if not plausible:
            continue
        labels = {(r['factual_status'], r['citation_status']) for r in plausible}
        chosen = plausible[0]
        projected = dict(text=claim['text'], **{
            k: deepcopy(chosen[k]) for k in ('factual_status', 'citation_status',
                                          'source_spans', 'citation_spans', 'reason')})
        if len(labels) > 1:
            projected.update(factual_status='unknown', citation_status='unknown',
                             source_spans=[], citation_spans=[],
                             reason='Multiple plausible readings differ in support; interpretation unresolved.')
        elif len(plausible) > 1:
            # Both readings must have been valid; preserve all evidence provenance.
            for key in ('source_spans', 'citation_spans'):
                projected[key] = [dict(id=i, span=s) for i, s in sorted({
                    (w['id'], w['span']) for r in plausible for w in r[key]})]
        grade['claims'].append(projected)
    errors.extend(legacy.validate(grade, inputs))
    return (None if errors else grade), sorted(set(errors))


def _claims(grade):
    return sorted((c['text'], c['factual_status'], c['citation_status']) for c in grade['claims'])


def _interpretations(packet):
    return sorted((c['text'], tuple(sorted((r['kind'], r['plausible'],
                   r['factual_status'], r['citation_status']) for r in c['readings'])))
                  for c in packet['claims'])


def differences(first, second):
    """Compare intermediate labels even when aggregate dimensions already fail."""
    affected = set()
    if _claims(first) != _claims(second):
        affected.update(('factual_support', 'citation_support'))
    if sorted((f['fact_id'], f['status']) for f in first['facts']) != sorted(
            (f['fact_id'], f['status']) for f in second['facts']):
        affected.update(('completeness', 'response_behavior'))
    if first['actual_behavior'] != second['actual_behavior']:
        affected.add('response_behavior')
    if first['relevance']['status'] != second['relevance']['status']:
        affected.add('relevance')
    if first['forbidden_assertion'] != second['forbidden_assertion']:
        affected.add('forbidden_assertion')
    return sorted(affected)


def compare(inputs, payload, evidence, safety_flags, first, second):
    """No gold labels, model review flags, majority voting or candidate rewriting."""
    grades, checks, errors = [], [], []
    for packet in (first, second):
        grade, invalid = project(inputs, packet)
        check = legacy.dimensions(inputs, grade, payload, evidence, safety_flags)
        errors.append(sorted(set(invalid + check['grader_errors'])))
        grades.append(grade)
        checks.append(check)
    affected = []
    labels = {key: 'unresolved' for key in KEYS}
    if not any(errors):
        affected = differences(*grades)
        if _interpretations(first) != _interpretations(second):
            affected = sorted(set(affected) | {'factual_support', 'citation_support'})
        labels = legacy.candidate_judgments(inputs, grades[0])
        other = legacy.candidate_judgments(inputs, grades[1])
        affected = sorted(set(affected) | {k for k in KEYS if labels[k] != other[k]})
        for key in affected:
            labels[key] = 'unresolved'
    # Preserve deterministic safety/quotation failures even on invalid/disputed
    # semantic judgments. No semantic vote can remove these failures.
    quote = checks[0]
    if quote['unmatched_citations']:
        labels['citation_support'] = 'fail'
    hard_fail = bool(safety_flags or quote['unmatched_citations'])
    failure = hard_fail or 'fail' in labels.values() or labels['forbidden_assertion'] == 'present'
    unresolved = bool(any(errors) or affected or 'unresolved' in labels.values())
    overall = 'fail' if failure else 'unresolved' if unresolved else 'pass'
    return dict(version=VERSION, status='invalid' if any(errors) else
                'disagreement' if affected else 'agreement_only',
                dimensions=dict(labels, quotation_fidelity=quote['quotation_fidelity'], overall=overall),
                grader_errors=errors, disputed_dimensions=affected,
                nonexact_quotes=quote['nonexact_quotes'], unmatched_citations=quote['unmatched_citations'],
                response_type_match=quote['response_type_match'],
                recorded_safety_flags=list(safety_flags), has_unresolved_judgment=unresolved,
                candidate_pass=overall == 'pass' and not quote['nonexact_quotes'] and quote['response_type_match'],
                target_credit=False,
                release_eligible=False, source_review_required=True,
                projected_grades=grades)


def probe_review(inputs, payload, evidence, safety_flags, first, second, candidate):
    """Candidate arrives only AFTER blind outputs; never enters request_plan."""
    result = compare(inputs, payload, evidence, safety_flags, first, second)
    verdicts = {key: 'unknown' for key in KEYS}
    if result['status'] == 'agreement_only':
        check = legacy.dimensions(inputs, candidate, payload, evidence, safety_flags)
        if check['grader_errors']:
            verdicts = {key: 'dispute' for key in KEYS}
        else:
            affected = differences(result['projected_grades'][0], candidate)
            verdicts = {key: 'dispute' if key in affected else 'agree' for key in KEYS}
    return dict(verdicts, reason='Deterministic comparison to blind judgments; no human adjudication.',
                blind_status=result['status'], release_eligible=False)
