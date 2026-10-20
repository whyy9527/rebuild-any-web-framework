"""Expose unvisited actions from real observations, rather than a fixed checklist.

This is an exploration frontier, not a Dream-RSI simulator or evidence of gains.
An action disappears only after a recorded outcome. An unavailable action stays
visible. Strategy comparison and history replay are subsequent work.
"""
import argparse
import json
from pathlib import Path

from capabilities.rebuild.contracts import local_file


def frontier(root, history):
    root = Path(root).resolve()
    states = {state['id']: state for state in history['states']}
    def operations(action):
        values = action.get('operations', ['activate'])
        if not isinstance(values, list) or not values or any(not isinstance(v, str) or not v for v in values) or len(set(values)) != len(values):
            raise ValueError('Nonempty unique probe operations required')
        return values
    resolved = set()
    attempts = {}
    for transition in history['transitions']:
        state = states[transition['from']]
        action = transition['action']
        if action not in {item['id'] for item in state['actions']}:
            raise ValueError('Transition action was not observed in its source state')
        local_file(root, transition['evidence'])
        observed_action = next(item for item in state['actions'] if item['id'] == action)
        modes = operations(observed_action)
        operation = transition.get('operation', 'activate') if 'operations' in observed_action else 'activate'
        if operation not in modes:
            raise ValueError('Transition operation was not declared for its source action')
        key = (state['id'], action, operation)
        attempts[key] = attempts.get(key, 0) + 1
        if transition['outcome'] == 'observed':
            if transition['to'] not in states:
                raise ValueError('Observed destination state missing')
            resolved.add(key)
        elif transition['outcome'] != 'unavailable':
            raise ValueError('Record an actual observed or unavailable outcome')
    pending = []
    for state in history['states']:
        local_file(root, state['evidence'])
        for action in state['actions']:
            for operation in operations(action):
                key = (state['id'], action['id'], operation)
                if key not in resolved:
                    row = {'state': state['id'], 'action': action,
                           'attempts': attempts.get(key, 0), 'evidence': state['evidence']}
                    if 'operations' in action:
                        row['operation'] = operation
                    pending.append(row)
    # Fewer attempts first; preserve observed order rather than inventing gains.
    pending.sort(key=lambda row: row['attempts'])
    return {'kind': 'observed_exploration_frontier', 'pending': pending,
            'resolved_actions': len(resolved),
            'completion': 'unknown; an empty recorded frontier does not prove the whole app explored',
            'policy': 'unvisited-first, observation order; not RSI self-improvement'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--workspace', default='.')
    parser.add_argument('--history', required=True)
    parser.add_argument('--out', required=True)
    args = parser.parse_args()
    root = Path(args.workspace).resolve()
    result = frontier(root, json.loads(local_file(root, args.history).read_text()))
    with (root / args.out).open('x') as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
    print(json.dumps({'pending': len(result['pending']), 'resolved': result['resolved_actions']}))


if __name__ == '__main__':
    main()
