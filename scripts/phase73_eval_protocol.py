"""Custody gates for the post-validation, post-freeze Phase 73 holdout."""
import hashlib
import json
import subprocess
from pathlib import Path

from scripts.current_eval_protocol import validate_suite, committed_inventory, COUNTS, USERS, PROJECT
from scripts.current_eval_protocol import FROZEN as PREVIOUS_FILES
from scripts.quality_confirmation_standard_v18 import CODE
from scripts.quality_completion_ledger import digest, FOLDER as QUALITY
from scripts.phase73_eval_budget import FOLDER, bounds

ROOT = Path(__file__).resolve().parents[1]
FROZEN = sorted(set(PREVIOUS_FILES + ['scripts/'+n for n in CODE] + [
    'scripts/phase73_eval_protocol.py', 'scripts/phase73_eval_budget.py',
    'scripts/phase73_eval_environment.py', 'scripts/phase73_eval_capture.py',
    'scripts/phase73_eval_run.py', 'scripts/report_phase73_eval.py',
    'scripts/test_phase73_eval.py', 'scripts/phase73_eval_history.py', 'scripts/test_phase73_eval_history.py',
    'scripts/quality_cost_control.py', 'scripts/quality_batch_transport.py',
    'scripts/quality_batch_grading.py', 'scripts/test_quality_cost_control.py',
    'data/evaluation/quality-cost-control-v1/policy-standard.json',
    'scripts/check_phase73_overlap.py', 'docs/phase-73/authoring-contract.md',
    'docs/phase-73/validation-contract.md']))


def file_inventory():
    paths = subprocess.check_output(['git','ls-files','--',*FROZEN],cwd=ROOT,text=True).splitlines()
    return {p:hashlib.sha256((ROOT/p).read_bytes().replace(b'\r\n',b'\n')).hexdigest() for p in sorted(paths)}


def evaluator_ready():
    from scripts.quality_confirmation_standard_v18 import readiness
    return readiness()


def validate_gold_scope(suite, environment):
    from apps.api.app.permissions.access_control import role_can_access
    tenant = environment['settings']['default_demo_tenant_id']
    for case in suite['cases']:
        for fact in case['required_facts']:
            matches = [row for row in environment['gold_source_scope']
                       if row['source_path'] == fact['source_path'].replace('\\', '/')
                       and row['tenant_id'] == tenant and row['project_id'] == case['project_id']]
            if (len(matches) != 1 or not role_can_access(matches[0]['access_roles'], case['user_role'])
                    or case.get('department_id') and matches[0]['department_id'] != case['department_id']):
                raise ValueError('Gold source is outside frozen authorized scope: ' + case['case_id'])


def verify_custody(*, require_current=True):
    freeze = json.loads((FOLDER/'freeze.json').read_bytes())
    if freeze['files'] != (file_inventory() if require_current else committed_inventory(freeze)):
        raise ValueError('Frozen source/corpus changed')
    if not require_current:
        for name, expected in freeze['files'].items():
            if name.startswith(('scripts/','apps/api/app/permissions/','data/synthetic-documents/')):
                current = hashlib.sha256((ROOT/name).read_bytes().replace(b'\r\n',b'\n')).hexdigest()
                if current != expected:
                    raise ValueError('Replay dependency differs from frozen source')
    if freeze['bounds'] != bounds() or freeze['evaluator_readiness_sha256'] != evaluator_ready():
        raise ValueError('Evaluator readiness or declared bounds changed')
    for name, expected in freeze['artifacts_sha256'].items():
        path = (ROOT/name).resolve()
        if not path.is_relative_to(ROOT) or digest(path) != expected:
            raise ValueError('Frozen evidence changed')
    seal = json.loads((FOLDER/'seal.json').read_bytes())
    for key,name in [('freeze_sha256','freeze.json'),('suite_sha256','holdout.json'),
                     ('validation_sha256','author-validation.json'),('overlap_sha256','overlap.json')]:
        if seal[key] != digest(FOLDER/name):
            raise ValueError('Holdout seal changed')
    suite = json.loads((FOLDER/'holdout.json').read_bytes())
    validation = json.loads((FOLDER/'author-validation.json').read_bytes())
    cases = suite.get('cases',[])
    if (suite.get('authored_after_freeze') != freeze['commit']
        or validation.get('status') != 'approved' or validation.get('case_count') != 60
        or validation.get('human_adjudication') is not False
        or validation.get('suite_sha256') != seal['suite_sha256']
        or validation.get('freeze_sha256') != seal['freeze_sha256']
        or validation.get('unresolved_findings') != []
        or len(validation.get('case_reviews',[])) != 60
        or {r['case_id'] for r in validation['case_reviews']} != {c['case_id'] for c in cases}
        or any(r.get('accept') is not True for r in validation['case_reviews'])):
        raise ValueError('Independent pre-execution validation failed')
    if {r['case_id']:r['expected_behavior'] for r in validation['case_reviews']} != {c['case_id']:c['expected_behavior'] for c in cases}:
        raise ValueError('Independent behavior references disagree')
    overlap = json.loads((FOLDER/'overlap.json').read_bytes())
    if overlap['hits']:
        raise ValueError('Historical lexical overlap remains unresolved')
    errors = validate_suite(suite)
    if {c.get('case_id') for c in cases} != {f'fresh-{i:03d}' for i in range(1,61)}:
        errors.append('exact_case_ids')
    if errors:
        raise ValueError(str(errors))
    # Exercise the real gold-input validation before the first application call.
    # This catches invalid roles/quotes that would otherwise stop mid-measurement.
    from scripts.reanalyze_saved_answers import build_inputs
    for case in cases:
        build_inputs(case, {'raw_response': {}, 'authorized_evidence': []})
    validate_gold_scope(suite, freeze['environment'])
    return freeze,suite
