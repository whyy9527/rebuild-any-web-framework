"""Execute a draft scenario against the online UI; not a frozen-batch receipt.

Uses the shared assertion implementation, without creating a candidate target or
claiming that the cross-platform adapter/configuration is ready.
"""
import argparse
import json
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from capabilities.rebuild.contracts import call, differences
from runtime.runner import input_manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--scenario', required=True)
    parser.add_argument('--out', required=True)
    args = parser.parse_args()
    project = Path('projects/duolingo-web')
    out = ROOT / args.out
    if out.exists() or not out.resolve().is_relative_to(ROOT):
        raise SystemExit('Choose a new output inside the repository')
    spec = json.loads((ROOT / project / 'spec.draft.json').read_text())
    fixture = json.loads((ROOT / spec['fixture']).read_text())
    behavior = next(b for b in spec['behaviors'] if b['id'] == args.scenario)
    if behavior['discovery'] == 'unknown':
        raise SystemExit('Cannot execute an unknown behavior')
    paths = [str(project / p) for p in ['spec.draft.json', 'fixture.json', 'original-adapter.mjs', 'package.json', 'package-lock.json', 'probe-reference.py']]
    inputs = input_manifest(ROOT, paths)
    target = {'command': ['node', str(project / 'original-adapter.mjs')]}
    report = {'kind': 'reference_feasibility', 'target_kind': 'original_online', 'layer': 'browser_ui',
              'scenario_id': args.scenario, 'inputs': inputs, 'started_at': time.time(), 'operations': []}

    def run(operation, **fields):
        receipt, response = call(ROOT, target, {'operation': operation, 'fixture': fixture, **fields}, 180)
        report['operations'].append({'operation': operation, 'receipt': receipt, 'response': response})
        return receipt, response

    try:
        for operation in ['start', 'reset']:
            receipt, response = run(operation)
            if receipt['status'] != 'pass' or not response or differences(fixture['initial_state'], response.get('state')):
                report['status'] = 'unavailable'
                break
        else:
            receipt, response = run('scenario', scenario_id=behavior['id'], precondition=behavior['precondition'],
                                actions=[s['action'] for s in behavior['steps']])
            problems = []
            if response:
                problems += differences(behavior['precondition'], response.get('precondition_state'), 'precondition')
                observations = response.get('observations', [])
                if response.get('scenario_id') != behavior['id'] or len(observations) != len(behavior['steps']):
                    problems.append('Scenario identity or executed step count mismatch')
                else:
                    for index, (step, observation) in enumerate(zip(behavior['steps'], observations)):
                        if observation.get('step') != index:
                            problems.append('Observation step mismatch')
                        problems += differences(step['expect'], observation.get('state'), 'step[' + str(index) + ']')
            report['differences'] = problems
            report['status'] = receipt['status'] if response is None else 'fail' if problems else 'pass'
    finally:
        receipt, response = run('reset')
        if receipt['status'] != 'pass' or not response or differences(fixture['initial_state'], response.get('state')):
            report['status'] = 'unavailable'
        receipt, _ = run('stop')
        if receipt['status'] != 'pass':
            report['status'] = 'unavailable'
        report['integrity'] = 'verified' if input_manifest(ROOT, paths) == inputs else 'changed'
        if report['integrity'] != 'verified':
            report['status'] = 'invalid'
        report['finished_at'] = time.time()
        out.parent.mkdir(parents=True, exist_ok=True)
        with out.open('x') as stream:
            stream.write(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
        print(json.dumps({'scenario': args.scenario, 'status': report['status'], 'out': args.out}))
    return 0 if report['status'] == 'pass' else 1


if __name__ == '__main__':
    sys.exit(main())
