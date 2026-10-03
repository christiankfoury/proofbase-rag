"""Expanded source-routing development control; original tasks unchanged."""
import sys
from scripts import conversation_continuation as runner
runner.SUITE=runner.FOLDER/'development-v3.json'
if __name__=='__main__':
    if sys.argv[1]=='prepare':runner.prepare(sys.argv[2],sys.argv[3],sys.argv[4:])
    elif sys.argv[1]=='run':runner.run(sys.argv[2])
    else:raise SystemExit('Use prepare or run')
