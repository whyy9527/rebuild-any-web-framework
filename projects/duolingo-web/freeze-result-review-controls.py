"""Freeze the original review close control without inferring an ARIA role."""
import argparse
import json
from pathlib import Path

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[1]
EV = BASE / 'evidence/english-current-walk-v1'


def build():
    parent = json.loads((BASE/'frontend-english-v33.json').read_text())
    contract = json.loads(json.dumps(parent))
    contract.update(revision='english-v34', parent_revision='english-v33',
                    changes=['Original close DIV geometry and enabled state; no invented ARIA button role.'])
    reference = json.loads((EV/'reference.json').read_text())
    for suffix, name in [('open', 'review-open-roles'), ('speech-expanded', 'review-speech-expanded-roles')]:
        key = 'current-practice-review-'+suffix
        source = json.loads((EV/'source'/(name+'.json')).read_text())
        close = next(r for r in source['visible'] if r['test'] == 'close-button')
        assert close['role'] is None and close['tag'] == 'DIV'
        reference['states'][key]['elements']['result-review-close'] = dict(rect=close['rect'], enabled=close['enabled'])
        for kind, fields in [('element_geometry', dict(rect=close['rect'], tolerance_points=0)),
                             ('element_boolean', dict(field='enabled', expected=close['enabled']))]:
            contract['requirements'].append(dict(id=key+'-close-'+kind, state=key, kind=kind,
                element='result-review-close', evidence=[str((EV/'source'/(name+'.json')).relative_to(ROOT))], **fields))
    assert contract['requirements'][:len(parent['requirements'])] == parent['requirements']
    return contract, reference


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--out-dir', required=True)
    a = p.parse_args()
    output = Path(a.out_dir)
    output.mkdir(parents=True, exist_ok=False)
    for name, value in zip(['contract.json', 'reference.json'], build()):
        (output/name).write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n')
