"""Append the actually executed listening-decline branch to the frontend mold.

The initial sessions response is context, not the post-action question sequence.
Source projection checks receipt consistency; it never certifies Swift.
"""
import argparse
import copy
import json
from pathlib import Path
import re

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[1]
EV = BASE / 'evidence/english-general-listening-decline-v1'


def build():
    def read(name):
        return json.loads((EV / name).read_text())

    contract = copy.deepcopy(json.loads((BASE / 'frontend-english-v29.json').read_text()))
    contract.update(revision='english-v30', scope='Observed listening-decline, inserted and replaced translations; all v29 requirements retained.')
    states, trace = {}, []

    def state(name, snapshot, image, receipt):
        key = 'general-listening-decline-' + name
        image_path = EV / image
        assert image_path.is_file(), image_path
        evidence = [str((EV / receipt).relative_to(ROOT))]
        texts = re.findall(r'(?:heading|button|textbox) "([^"\n]+)"', snapshot)
        texts += re.findall(r'- (?:text|paragraph): ([^\n]+)', snapshot)
        states[key] = dict(snapshot=snapshot, accessible_text=texts, capture=dict(
            path=str(image_path.relative_to(ROOT)), content_rect_points=[0, 0, 1200, 732],
            backing_scale=1, window_points=[1200, 732]))
        contract['requirements'].append(dict(id=key+'-image', state=key, kind='image_pixels',
            reference_image=str(image_path.relative_to(ROOT)), pixels=[1200, 732], evidence=evidence))
        for index, text in enumerate(dict.fromkeys(texts)):
            if text in ['现在不做听力题', '听力题已跳过', '将在 15 分钟后恢复', '现在不做口语题', '麦克风已关闭']:
                contract['requirements'].append(dict(id=key+f'-copy-{index}', state=key,
                    kind='accessible_text', text=text, evidence=evidence))
        return key

    for name in ['tap-before', 'tap-declined', 'after-tap', 'after-inserted',
                 'speech-declined-with-text', 'coffee-milk-feedback-detail', 'challenge-interlude', 'result']:
        receipt = name+'.json'
        row = read(receipt)
        state(name, row['snapshot'], row['screenshot'], receipt)

    for name, prefix in [('inserted', 'inserted'), ('water-tea', 'water-tea'),
                         ('tea-coffee', 'tea-coffee'), ('coffee-milk', 'coffee-milk'),
                         ('no-coffee', 'no-coffee'), ('no-milk', 'no-milk'),
                         ('goodbye', 'goodbye'), ('hot-tea', 'hot-tea'),
                         ('ice-water', 'ice-water'), ('no-water', 'no-water')]:
        receipt = name+'-answer.json'
        row = read(receipt)
        assert row['rejected'] is False, receipt
        key = state(name, row['before'], prefix+'-before.png', receipt)
        state(name+'-feedback', row['feedback'], prefix+'-feedback.png', receipt)
        trace.append(dict(id=key, receipt=receipt, accepted=True, prompts=row.get('prompts'),
                          input=row.get('input'), clicks=row.get('clicks')))

    prefix = read('replay-to-tap.json')
    assert prefix['failure'] is None and prefix['stopped']['index'] == 6
    assert prefix['stopped']['type'] == 'listenTap'
    graded = [row for row in prefix['observed'] if row.get('feedback')]
    assert [row['index'] for row in graded] == list(range(6))
    assert all(row['identity']['matches'] for row in graded)
    assert len({row['id'] for row in contract['requirements']}) == len(contract['requirements'])
    return contract, dict(states=states), dict(
        route='/practice', session_type=read('session.json')['session']['type'],
        prefix_receipt='replay-to-tap.json', prefix_graded_count=len(graded),
        listening_action='decline listenTap; continue to water and coffee translation',
        speech_action='decline speak; continue to water and tea translation',
        subsequent_graded=trace, total_graded=len(graded)+len(trace),
        limitations=['One actual session, not adaptive selection or a reset algorithm.',
                     'Source projection is not native verification.',
                     '15 minute recovery was displayed, not independently timed.',
                     'No original or candidate acoustic equality measured in this branch.'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out-dir', required=True)
    args = parser.parse_args()
    values = build()
    output = Path(args.out_dir)
    output.mkdir(parents=True, exist_ok=False)
    for name, value in zip(['contract.json', 'reference.json', 'trace.json'], values):
        (output / name).write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n')
    print(json.dumps(dict(requirements=len(values[0]['requirements']), states=len(values[1]['states']),
                          graded=values[2]['total_graded'])))
