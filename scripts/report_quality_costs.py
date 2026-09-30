"""Read-only cached-input cost audit. Writing never changes historical evidence."""
import argparse
import json
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.quality_cost_control import report_history, FOLDER
from scripts.quality_completion_durable import write_json_atomic

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--write', action='store_true')
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    report = report_history()
    if args.check:
        if report != json.loads((FOLDER / 'historical-cost-report.json').read_bytes()):
            raise ValueError('Derived cost report differs from raw evidence')
        print('Saved cost report matches immutable raw usage; no network calls')
        raise SystemExit(0)
    if args.write:
        write_json_atomic(FOLDER / 'historical-cost-report.json', report)
    print(json.dumps(report, indent=2))
