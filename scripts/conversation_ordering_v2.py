"""Versioned development references and offline grading comparison; no executor.

The old 24-case suite remains immutable. This explicit successor keeps every
input and probe and changes only the disputed reference under contract v2.
"""
from copy import deepcopy
from scripts import conversation_grader_v11 as legacy
from scripts import quality_eval_contract_v35 as contract
from scripts.bounded_redesign_run import read, digest
from scripts.quality_confirmation_reference_checks import check_references

VERSION = 'procedural-ordering.v2'
PATH = legacy.FOLDER / 'ordering-contract-v2' / 'references.json'
DISPUTED = 'answer-injection-award-pass'


def suite():
    value = read(PATH)
    if value['version'] != VERSION or value['grader_version'] != contract.VERSION:
        raise ValueError('Reference/contract version mismatch')
    for path, expected_hash in value['source_bindings'].items():
        if digest(legacy.ROOT / path) != expected_hash:
            raise ValueError('Historical reference evidence changed: ' + path)
    originals = legacy.cases('calibration')
    cases = value['cases']
    if len(cases) != 32 or len({c['id'] for c in cases}) != 32:
        raise ValueError('All 24 original and eight ordering controls required')
    if [c['id'] for c in cases[:24]] != [c['id'] for c in originals]:
        raise ValueError('Original calibration coverage/order changed')
    for old, new in zip(originals, cases[:24]):
        expected = deepcopy(old)
        if old['id'] == DISPUTED:
            expected['expected'].update(factual_support='unresolved', citation_support='unresolved')
            # The rationale is versioned in the amendment, not the old case.
        if new != expected:
            raise ValueError('Undeclared original case/reference change: ' + old['id'])
    if value['review_probes'] != legacy.probes('calibration'):
        raise ValueError('Original reviewer probes changed')
    check_references(value)
    return value


def cases(stage):
    if stage == 'calibration':
        return suite()['cases']
    if stage == 'diagnostic':
        return legacy.cases(stage)
    raise ValueError('Unknown qualification stage')


def probes(stage):
    if stage == 'calibration':
        return suite()['review_probes']
    if stage == 'diagnostic':
        return legacy.probes(stage)
    raise ValueError('Unknown qualification stage')


def judged(case, grade, review, error=None):
    dims = contract.dimensions(case['inputs'], grade, case['payload'], case['evidence'], case['safety_flags'], review)
    mismatch = legacy.existing.compare(case, grade, dims)
    # Dimension-level agreement alone must not hide missing coverage or substitute
    # citation-missing for interpretation-unknown in the amended case.
    expectations = suite()['intermediate_expectations'].get(case['id'])
    if expectations:
        facts = {f['fact_id']: f['status'] for f in grade.get('facts', [])} if grade else {}
        claims = [{k: c[k] for k in ('text', 'factual_status', 'citation_status')}
                  for c in grade.get('claims', [])] if grade else []
        actual = dict(facts=facts, claims=claims)
        if actual != expectations:
            mismatch['intermediate_labels'] = dict(expected=expectations, actual=actual)
        if grade and any(c['source_spans'] or c['citation_spans'] for c in grade['claims']):
            mismatch['uncertainty_witnesses'] = 'The amended unknown claim must not invent positive witnesses.'
    return dict(grade=grade, review=review, error=error, dimensions=dims, mismatches=mismatch,
                matched=not error and not mismatch and not dims['grader_errors'] and not dims['disputed_dimensions'])
