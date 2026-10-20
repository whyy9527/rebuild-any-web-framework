"""Add source control geometry and enabled states without relaxing v30 images."""
import argparse
import json
from pathlib import Path

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[1]
EV = BASE / 'evidence/english-general-listening-decline-v1'


def build():
    contract = json.loads((BASE / 'frontend-english-v30.json').read_text())
    reference = json.loads((EV / 'reference.json').read_text())
    contract.update(revision='english-v31', scope='Listening control enabled/roles/geometry; all v30 requirements retained.')
    for name in ['tap-before', 'tap-declined']:
        state = 'general-listening-decline-'+name
        receipt = EV / (name+'.json')
        rows = [r for r in json.loads(receipt.read_text())['visible'] if r['tag']=='BUTTON']
        elements = reference['states'][state].setdefault('elements', {})

        def add(element, row, kinds):
            elements[element] = dict(role='button', enabled=row['enabled'], rect=row['rect'])
            for kind in kinds:
                requirement = dict(id=state+'-'+element+'-'+kind, state=state, kind=kind, element=element, evidence=[str(receipt.relative_to(ROOT))])
                if kind == 'element_geometry':
                    requirement.update(rect=row['rect'], tolerance_points=0)
                elif kind == 'element_role':
                    requirement['role'] = 'button'
                else:
                    requirement.update(field='enabled', expected=row['enabled'])
                contract['requirements'].append(requirement)

        for i, word in enumerate(['and', 'good morning', 'water', 'coffee']):
            add('word-bank-word-'+str(i), next(r for r in rows if r.get('text')==word), ['element_boolean'])
        for key, width in [('pronounce', 100), ('pronounce-slow', 70)]:
            add(key, next(r for r in rows if r['rect'][2] == width and r['icons']), ['element_geometry'])
        label, key = ('现在不做听力题', 'listening-decline') if name=='tap-before' else ('继续', 'listening-continue')
        add(key, next(r for r in rows if r.get('text')==label), ['element_role', 'element_boolean', 'element_geometry'])
    assert len({r['id'] for r in contract['requirements']}) == len(contract['requirements'])
    return contract, reference


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out-dir', required=True)
    args = parser.parse_args()
    output = Path(args.out_dir)
    output.mkdir(parents=True, exist_ok=False)
    for name, value in zip(['contract.json', 'reference.json'], build()):
        (output / name).write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n')
