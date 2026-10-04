"""Offline successor: empty forbidden-reference sets are decided by code.

The original packet and all other judgments remain evidence. This is a separately
versioned projection, never a rewrite of v1 results or qualification evidence.
"""
from copy import deepcopy
from scripts import structured_blind_evaluator_v1 as previous

VERSION = 'structured-blind.v2-offline'
KEYS, legacy = previous.KEYS, previous.legacy
request_plan = previous.request_plan
replay_packets = previous.replay_packets
full_reservation = previous.full_reservation


def _project_packet(inputs, packet):
    # Validate the complete original first. Do not repair malformed output,
    # invented witnesses, missing claims or any nonempty forbidden-reference set.
    _, errors = previous.project(inputs, packet)
    projected = deepcopy(packet)
    if not errors and inputs.get('forbidden_assertions') == []:
        projected['forbidden_assertion'] = 'absent'
    return projected


def project(inputs, packet):
    return previous.project(inputs, _project_packet(inputs, packet))


def compare(inputs, payload, evidence, safety_flags, first, second):
    result = previous.compare(inputs, payload, evidence, safety_flags,
                              _project_packet(inputs, first), _project_packet(inputs, second))
    result.update(version=VERSION, empty_forbidden_set=inputs.get('forbidden_assertions') == [],
                  observed_forbidden_labels=[p.get('forbidden_assertion') if isinstance(p, dict)
                                             else None for p in (first, second)])
    return result


def probe_review(inputs, payload, evidence, safety_flags, first, second, candidate):
    result = compare(inputs, payload, evidence, safety_flags, first, second)
    verdicts = {key: 'unknown' for key in KEYS}
    if result['status'] == 'agreement_only':
        check = legacy.dimensions(inputs, candidate, payload, evidence, safety_flags)
        if check['grader_errors']:
            verdicts = {key: 'dispute' for key in KEYS}
        else:
            affected = previous.differences(result['projected_grades'][0], candidate)
            verdicts = {key: 'dispute' if key in affected else 'agree' for key in KEYS}
    return dict(verdicts, reason='Deterministic comparison to blind judgments; no human adjudication.',
                blind_status=result['status'], release_eligible=False)
