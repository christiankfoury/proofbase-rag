"""Development readiness adapter for a separately frozen v23 confirmation."""
from scripts import quality_development_v23 as development
from scripts.quality_eval_contract_v23 import VERSION
from scripts.quality_eval_transport_v23 import case_bound
from scripts.quality_cost_control import read, digest

ROOT, FOLDER = development.ROOT, development.FOLDER
CODE = development.CODE
from scripts.quality_cost_phase73_v2 import AUTHORIZATION as APPROVAL
from scripts.quality_confirmation_v20 import original
GATE = FOLDER / 'calibration-v23-readiness.json'
REVIEW = ROOT / 'docs/phase-73/v23-calibration-source-review.md'
compare = development.compare


def readiness():
    diagnostic, full = development.replay('diagnostic'), development.replay('calibration')
    gate = read(GATE)
    if (diagnostic['status'] != 'complete' or diagnostic['matched'] != 8 or diagnostic['matching_probes'] != 3
            or full['status'] != 'complete' or full['count'] != 24 or full['matched'] != 24
            or full['matching_probes'] != 3 or full != read(FOLDER/'v23-calibration-report.json')
            or gate.get('status') != 'approved' or gate.get('human_adjudication') is not False
            or gate.get('unresolved_semantic_findings') != 0
            or gate.get('diagnostic_gate_sha256') != digest(development.DIAGNOSTIC_GATE)
            or gate.get('report_sha256') != digest(FOLDER/'v23-calibration-report.json')
            or gate.get('source_review_sha256') != digest(REVIEW)):
        raise ValueError('V23 development readiness failed')
    return digest(GATE)
