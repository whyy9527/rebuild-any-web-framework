"""Deterministic command fixture, testing plumbing rather than LLM capability.

The evaluator executes the candidate independently. The developer consumes
actual replay feedback but is a rule program; it is not a model reproduction.
"""
import json
from pathlib import Path
import subprocess
import sys


REVISED = '''def select(view, rho):
    if view['round'] >= max(1, int(4 * rho)):
        return []
    root = view['nodes'][0]['id']
    leaves = [n for n in view['nodes'] if n['id'] in view['eligible'] and n['id'] != root]
    if any(n['observation'].get('evaluation', {}).get('checks') == [True] * 4 for n in leaves):
        return []
    if not leaves:
        return [root]
    best = max(leaves, key=lambda n: n['score'])
    return ([best['id'], root] if rho >= .75 else [best['id']])[:view['max_parallelism']]
'''


def main():
    request = json.load(sys.stdin)
    mode = sys.argv[1]
    if mode == 'agent':
        workspace = Path(request['workspace'])
        depth = len(request['parent']['generation_history']) + 1
        # Deliberately imperfect first attempt; continuation changes the program.
        code = 'return sum(values)' if depth > 1 else 'return sum(v for v in values if v > 0)'
        (workspace / 'candidate.py').write_text('def total(values):\n    ' + code + '\n')
        return {'generation': {'depth': depth, 'code': code},
                'observation': {'edited': 'candidate.py'}}
    if mode == 'evaluator':
        path = Path(request['workspace']) / 'candidate.py'
        code = '''import json,runpy,sys
f=runpy.run_path(sys.argv[1])['total']
cases=[([],0),([1,2],3),([-1],-1),([2,-3],-1)]
print(json.dumps([f(values)==expected for values,expected in cases]))
'''
        result = subprocess.run([sys.executable, '-I', '-c', code, str(path)],
                                capture_output=True, text=True, timeout=5)
        checks = json.loads(result.stdout) if result.returncode == 0 else [False] * 4
        return {'score': sum(checks) / 4, 'observation': {'checks': checks, 'executed': True}}
    if mode == 'reviser':
        if not request['feedback'] or any(not f['worlds'] for f in request['feedback'] if f['status'] == 'evaluated'):
            raise ValueError('real replay feedback required')
        # This fixture changes policy only when deeper recorded attempts helped.
        deeper_helped = any(n['score'] > .5 and len(n['generation_history']) > 1
                            for f in request['feedback'] if f['status'] == 'evaluated'
                            for world in f['worlds'] for run in world['runs']
                            for step in run['trace'] for n in step['observations'])
        return {'code': REVISED if deeper_helped else request['policy_code']}
    raise ValueError('unknown worker role')


if __name__ == '__main__':
    print(json.dumps(main()))
