"""Freeze actually visited avatar save/return states, preserving v57 unchanged."""
import argparse
import json
from pathlib import Path

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[1]
EVIDENCE = BASE / 'evidence/english-avatar-save-v1'


def build():
    contract = json.loads((BASE / 'frontend-english-v57.json').read_text())
    prior = contract['requirements'][:]
    reference = {'states': {}}
    for file in sorted((EVIDENCE / 'source').glob('*.json')):
        source = json.loads(file.read_text())
        assert source['viewport'] == {'width': 1200, 'height': 732}
        key = 'avatar-save-' + file.stem
        evidence = [str(file.relative_to(ROOT))]
        image = file.with_suffix('.png')
        texts = list(dict.fromkeys(run['text'] for run in source['text_runs']))
        state = {'accessible_text': texts, 'elements': {}}
        reference['states'][key] = state

        def add(suffix, kind, **fields):
            contract['requirements'].append(dict(id=key + '-' + suffix,
                state=key, kind=kind, evidence=evidence[:], **fields))

        if image.exists():
            name = str(image.relative_to(ROOT))
            evidence.append(name)
            state['capture'] = {'path': name, 'content_rect_points': [0, 0, 1200, 732],
                                'window_points': [1200, 732], 'backing_scale': 1}
            add('whole', 'image_pixels', reference_image=name, pixels=[1200, 732])
        else:
            raise ValueError('Missing actual source screenshot: ' + str(image))
        for i, text in enumerate(texts):
            add('text-' + str(i), 'accessible_text', text=text)
        # Retain source order, unnamed controls and ARIA state; no invented semantics.
        for i, action in enumerate(source['actions']):
            if action['rect'][0] < 260:
                continue
            name = 'profile-action-' + str(i)
            state['elements'][name] = {field: action[field] for field in
                                      ['rect', 'role', 'enabled', 'checked'] if field in action}
            add(name + '-geometry', 'element_geometry', element=name,
                rect=action['rect'], tolerance_points=0)
            if action['role'] is not None:
                add(name + '-role', 'element_role', element=name, role=action['role'])
            add(name + '-enabled', 'element_boolean', element=name, field='enabled', expected=action['enabled'])
            if isinstance(action.get('checked'), bool):
                add(name + '-checked', 'element_boolean', element=name, field='checked', expected=action['checked'])
        add('actual-audio', 'pending', description='Actual original/native acoustic equality unverified')
    contract.update(revision='english-v58', parent_revision='english-v57', changes=[
        'Actual Done→exit confirmation, persisted skin1 reload, dirty Back/Discard and original404 return',
        'Canvas15skin colors sampled through actual radio selections; animation equality unverified'])
    assert contract['requirements'][:len(prior)] == prior
    assert len({r['id'] for r in contract['requirements']}) == len(contract['requirements'])
    return contract, reference


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out-dir', required=True)
    output = Path(parser.parse_args().out_dir)
    output.mkdir(parents=True, exist_ok=False)
    for name, value in zip(['contract.json', 'reference.json'], build()):
        (output / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')
