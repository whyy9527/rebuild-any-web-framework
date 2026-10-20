"""Append actual result-review frontend requirements without changing v32."""
import argparse
import json
from pathlib import Path

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[1]
EV = BASE / 'evidence/english-current-walk-v1'


def build():
    parent = json.loads((BASE / 'frontend-english-v32.json').read_text())
    contract = json.loads(json.dumps(parent))
    contract.update(revision='english-v33', parent_revision='english-v32',
                    scope='Actual current-instance result review; retain all v32 requirements.',
                    changes=['Observed 17 review cards, including declined speech, and expanded speech answer.'])
    reference = json.loads((BASE / 'evidence/english-isolation-presentation-v1/reference.json').read_text())
    for suffix, stem in [('open', 'review-open-roles'), ('speech-expanded', 'review-speech-expanded-roles')]:
        source = json.loads((EV / 'source' / (stem+'.json')).read_text())
        state_key = 'current-practice-review-'+suffix
        cards = [r for r in source['visible'] if r['tag'] == 'DIV' and r['role'] == 'button']
        assert len(cards) == 17
        state = dict(snapshot=source['snapshot'], accessible_text=[], elements={},
                     capture=dict(path=str((EV/'source'/(stem+'.png')).relative_to(ROOT)),
                                  content_rect_points=[0, 0, 1200, 732], backing_scale=1,
                                  window_points=[1200, 732]))
        reference['states'][state_key] = state
        evidence = [str((EV/'source'/(stem+'.json')).relative_to(ROOT))]
        def add(label, kind, **fields):
            contract['requirements'].append(dict(id=state_key+'-'+label+'-'+kind,
                state=state_key, kind=kind, evidence=evidence, **fields))
        for i, card in enumerate(cards):
            element = 'review-card-'+str(i)
            state['elements'][element] = dict(rect=card['rect'], role=card['role'], enabled=card['enabled'])
            add(element, 'element_geometry', element=element, rect=card['rect'], tolerance_points=0)
            add(element, 'element_role', element=element, role=card['role'])
            add(element, 'element_boolean', element=element, field='enabled', expected=card['enabled'])
        # Freeze actual visible text runs, not animation digits in the result underneath.
        texts = ['查看你的成绩单！', '点击下面的小方块来浏览答案吧！']
        if suffix == 'speech-expanded':
            texts += ['你的答案：', '正确答案：', 'Hot, please.']
        for i, text in enumerate(texts):
            assert any(r['text'] == text for r in source['text_runs']), text
            state['accessible_text'].append(text)
            add('text-'+str(i), 'accessible_text', text=text)
        add('whole-image', 'image_pixels', reference_image=state['capture']['path'], pixels=[1200, 732])
    assert contract['requirements'][:len(parent['requirements'])] == parent['requirements']
    assert len({r['id'] for r in contract['requirements']}) == len(contract['requirements'])
    return contract, reference


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out-dir', required=True)
    args = parser.parse_args()
    output = Path(args.out_dir)
    output.mkdir(parents=True, exist_ok=False)
    for name, value in zip(['contract.json', 'reference.json'], build()):
        (output/name).write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n')
