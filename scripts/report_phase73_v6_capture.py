"""Read-only v6 capture inventory; never grades or authorizes execution."""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.report_phase73_v5_capture import snapshot as retained_snapshot, digest, read

FOLDER = ROOT / 'data/evaluation/current-runtime-v6'


def snapshot(folder):
    result = retained_snapshot(folder)
    result['version'] = 'phase73-v6-capture-publication.v1'
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    result = snapshot(FOLDER)
    path = FOLDER / 'capture-publication.json'
    if args.check:
        if read(path) != result:
            raise SystemExit('Capture inventory or summary differs')
        print('All v6 artifacts, unfinished captures and response denominators verified offline')
    else:
        path.write_text(json.dumps(result, indent=2, sort_keys=True) + '\n', encoding='utf-8')
        print(f"Saved {result['captured_cases']} captures; {result['completed_cases']} complete rows")
