"""Freeze actual isolation artwork and controls; retain all v31 requirements."""
import argparse
import json
from pathlib import Path

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[1]
EV = BASE / 'evidence/english-general-practice-v1'


def build():
    contract = json.loads((BASE / 'frontend-english-v31.json').read_text())
    reference = json.loads((EV / 'reference.json').read_text())
    contract.update(revision='english-v32', scope='Isolation current source character and actual speaker/control semantics; v31 unchanged.')
    source = json.loads((EV / 'isolation-before.json').read_text())
    replay = json.loads((EV / 'replay-from-5.json').read_text())['observed'][0]
    assert replay['index'] == 5 and replay['type'] == 'listenIsolation'
    key = 'general-practice-q5'
    elements = reference['states'][key].setdefault('elements', {})
    rows = source['visible']

    def add(element, facts, kinds, evidence):
        elements[element] = facts
        for kind in kinds:
            row = dict(id=key+'-'+element+'-'+kind, state=key, kind=kind,
                       element=element, evidence=[str((EV/evidence).relative_to(ROOT))])
            if kind == 'element_geometry':
                row.update(rect=facts['rect'], tolerance_points=0)
            elif kind == 'element_role':
                row['role'] = facts['role']
            else:
                row.update(field='enabled', expected=facts['enabled'])
            contract['requirements'].append(row)

    canvas = replay['canvases'][0]['rect']
    add('question-character', dict(rect=[canvas[k] for k in ['x', 'y', 'width', 'height']]), ['element_geometry'], 'replay-from-5.json')
    speaker = next(r for r in rows if r['tag'] == 'BUTTON' and r['rect'][2:] == [29, 22])
    add('isolation-prompt', dict(rect=speaker['rect'], role='button', enabled=speaker['enabled']),
        ['element_geometry', 'element_role', 'element_boolean'], 'isolation-before.json')
    for i, row in enumerate(r for r in rows if r['role'] == 'radio'):
        add('option-'+str(i), dict(rect=row['rect'], role='radio', enabled=row['enabled']), ['element_geometry'], 'isolation-before.json')
    decline = next(r for r in rows if r['text'] == '现在不做听力题')
    add('listening-decline', dict(rect=decline['rect'], role='button', enabled=decline['enabled']),
        ['element_geometry', 'element_role', 'element_boolean'], 'isolation-before.json')
    assert contract['requirements'][:1903] == json.loads((BASE / 'frontend-english-v31.json').read_text())['requirements']
    assert len({r['id'] for r in contract['requirements']}) == len(contract['requirements'])
    return contract, reference


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--out-dir', required=True)
    a = p.parse_args()
    output = Path(a.out_dir)
    output.mkdir(parents=True, exist_ok=False)
    for name, value in zip(['contract.json', 'reference.json'], build()):
        (output/name).write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n')
