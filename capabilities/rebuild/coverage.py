"""Join observed action inventory to journeys and actual frontend results.

An unmodeled action remains a gap, even when every existing assertion passes.
This reports known inventory only and does not declare exploration complete.
"""
import argparse
import json
from pathlib import Path
from capabilities.rebuild.contracts import local_file


def coverage(inventory, contract, validation):
    results = {row['id']: row['status'] for row in validation['rows']}
    requirements = contract['requirements']
    rows = []
    for state, actions in inventory['states'].items():
        if len({action['id'] for action in actions}) != len(actions):
            raise ValueError('Duplicate action identities in source state')
        for action in actions:
            journeys = [j for j in inventory['journeys'] if j['from'] == state and j['action'] == action['id']]
            ids = {r['id'] for j in journeys for r in requirements if r['state'] in j['states']}
            statuses = {key: results.get(key, 'not_run') for key in sorted(ids)}
            status = ('unmodeled' if not journeys or not ids else
                      'fail' if 'fail' in statuses.values() else
                      'unavailable' if 'unavailable' in statuses.values() else
                      'not_run' if 'not_run' in statuses.values() else 'pass')
            rows.append({'state': state, 'action': action, 'journeys': [j['id'] for j in journeys],
                         'status': status, 'requirements': statuses})
    return {'kind': 'frontend_action_coverage', 'rows': rows,
            'completion': 'unknown; only observed controls, never full-app completeness',
            'counts': {status: sum(r['status'] == status for r in rows)
                       for status in ['pass', 'fail', 'not_run', 'unavailable', 'unmodeled']}}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ['inventory', 'contract', 'validation', 'out']: p.add_argument('--'+name, required=True)
    a = p.parse_args(); root = Path.cwd()
    read = lambda name: json.loads(local_file(root, name).read_text())
    result = coverage(read(a.inventory), read(a.contract), read(a.validation))
    with (root / a.out).open('x') as stream: json.dump(result, stream, ensure_ascii=False, indent=2); stream.write('\n')
    print(json.dumps(result['counts']))


if __name__ == '__main__': main()
