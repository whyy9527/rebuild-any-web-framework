"""Freeze executed /practice states, retaining the parent frontend contract.

The captured API list is not the executed trajectory. Only receipts with actual
feedback enter this trace; inserted/replacement challenges have their own IDs.
"""
import argparse
import copy
import json
from pathlib import Path
import re

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[1]
EV = BASE / 'evidence/english-general-practice-v1'


def read(name):
    return json.loads((EV / name).read_text())


def build():
    contract = copy.deepcopy(json.loads((BASE / 'frontend-english-v27.json').read_text()))
    contract.update(revision='english-v28', scope='Actual independent GLOBAL_PRACTICE trajectory, modes, adaptive replacements, wrong review and heart reward; v27 requirements unchanged.')
    states, trace = {}, []
    requirements = contract['requirements']

    def add_state(name, snapshot, image, evidence, heading_level=None):
        key = 'general-practice-' + name
        image_path = EV / Path(image).name
        assert image_path.is_file(), image_path
        texts = re.findall(r'(?:heading|button|textbox) "([^"\n]+)"', snapshot)
        texts += re.findall(r'- (?:text|paragraph): ([^\n]+)', snapshot)
        states[key] = dict(accessible_text=texts, snapshot=snapshot, elements={}, capture=dict(
            path=str(image_path.relative_to(ROOT)), content_rect_points=[0, 0, 1200, 732],
            backing_scale=1, window_points=[1200, 732]))
        refs = [str((EV / evidence).relative_to(ROOT))]
        requirements.append(dict(id=key+'-image', state=key, kind='image_pixels', reference_image=str(image_path.relative_to(ROOT)), pixels=[1200, 732], evidence=refs))
        if heading_level:
            heading = re.search(r'heading "([^"\n]+)" \[level='+str(heading_level)+r'\]', snapshot).group(1)
            requirements.append(dict(id=key+'-heading', state=key, kind='accessible_text', text=heading, evidence=refs))
        return key

    rows = {}
    for filename in ['replay.json', 'replay-from-5.json', 'replay-from-6.json', 'replay-from-8-after-inserted.json', 'replay-from-11.json']:
        for row in read(filename)['observed']:
            if row.get('feedback'):
                assert row['identity']['matches']
                assert not re.search(r'heading "(?:正确答案：|Correct answer:)"', row['feedback'])
                assert row['index'] not in rows
                rows[row['index']] = (row, filename)
    assert sorted(rows) == [0, 1, 2, 3, 4, 5, 6, 8, 9, 11, 12]
    for i, (row, filename) in sorted(rows.items()):
        key = add_state(f'q{i}', row['before'], row['screenshot_before'], filename, 1)
        add_state(f'q{i}-feedback', row['feedback'], row['screenshot_feedback'], filename, 2)
        actions = row['actions'] or [dict(pair=p) for p in row.get('pair_audio_order', [])]
        trace.append(dict(id=key, api_index=i, source_type=row['type'], actions=actions, receipt=filename, accepted=True))
        if i == 0:
            for j, rect in enumerate(row['left_rects']):
                states[key]['elements'][f'pair-left-{j}'] = dict(rect=[rect[v] for v in ['x', 'y', 'width', 'height']])
            for j, text in enumerate(row['right_text']):
                pair = next(p for p in row['pair_audio_order'] if p['translation'] == text)
                rect = row['right_rects'][j]
                states[key]['elements'][f'pair-right-{pair["left_index"]}'] = dict(rect=[rect[v] for v in ['x', 'y', 'width', 'height']])
            for element, facts in states[key]['elements'].items():
                requirements.append(dict(id=key+'-'+element, state=key, kind='element_geometry', element=element, rect=facts['rect'], tolerance_points=0, evidence=[str((EV/filename).relative_to(ROOT))]))

    for name, filename, prefix, accepted in [
        ('inserted', 'inserted-answer.json', 'inserted', True),
        ('q10', 'complete-answer.json', 'complete', True),
        ('replacement13', 'replacement-answer.json', 'replacement', True),
        ('replacement14', 'replacement14-answer.json', 'replacement14', True),
        ('replacement15', 'replacement15-wrong.json', 'replacement15-wrong', False),
        ('review', 'review-answer.json', 'review', True),
    ]:
        row = read(filename)
        assert row['rejected'] is (not accepted)
        key = add_state(name, row['before'], prefix+'-before.png', filename, 1)
        add_state(name+'-feedback', row['feedback'], prefix+'-feedback.png', filename, 2)
        trace.append(dict(id=key, receipt=filename, accepted=accepted, input=row.get('input'), clicks=row.get('clicks'), prompts=row['prompts']))

    for name, filename in [('keyboard', 'listentap-keyboard-before.json'), ('speech', 'speech-before.json'),
                           ('review-intro', 'review-intro.json'), ('result', 'settlement-ready.json'),
                           ('heart-reward', 'after-settlement.json'), ('profile', 'profile-before.json')]:
        row = read(filename)
        key = add_state(name, row['snapshot'], row['screenshot'], filename)
        if name == 'keyboard':
            textbox = next(v for v in row['visible'] if v['tag'] in ['TEXTAREA', 'INPUT'])
            states[key]['elements']['answer-input'] = dict(rect=textbox['rect'], enabled=textbox['enabled'])
            requirements.append(dict(id=key+'-input', state=key, kind='element_geometry', element='answer-input', rect=textbox['rect'], tolerance_points=0, evidence=[str((EV/filename).relative_to(ROOT))]))
    for name, text in [('speech','现在不做口语题'), ('review-intro','一起来复习一下之前你不太熟练的部分吧！'),
                       ('heart-reward','你又获取了一颗红心！ 学习新单元需要红心！'), ('result','重新练习'), ('profile','稍后再说')]:
        key = 'general-practice-'+name
        # Broad text nodes remain whole in the reference AX snapshot.
        assert text in states[key]['accessible_text'], (key, states[key]['accessible_text'])
        requirements.append(dict(id=key+'-copy', state=key, kind='accessible_text', text=text,
                                 evidence=[str((EV / {'speech':'speech-before.json','review-intro':'review-intro.json','heart-reward':'after-settlement.json','result':'settlement-ready.json','profile':'profile-before.json'}[name]).relative_to(ROOT))]))
    assert len({r['id'] for r in requirements}) == len(requirements)
    order = [f'q{i}' for i in range(7)] + ['inserted', 'q8', 'q9', 'q10', 'q11', 'q12', 'replacement13', 'replacement14', 'replacement15', 'review']
    by_id = {r['id']: r for r in trace}
    assert set(by_id) == {'general-practice-'+name for name in order}
    trace = [by_id['general-practice-'+name] for name in order]
    return contract, dict(states=states), dict(route='/practice', session_type=read('session.json')['session']['type'],
        accepted_receipts=sum(x['accepted'] for x in trace), rejected_receipts=sum(not x['accepted'] for x in trace),
        receipts=trace, ordering='Actual executed graded trajectory; speech-decline occurs between q6 and inserted. Challenge interlude precedes replacement13; review interlude precedes review.',
        speech_decline_receipt='speech-decline.json',
        limitations=['One actual session, not the adaptive selection algorithm.', 'Media play invocations do not prove acoustic output.',
                     'complete-before.png and replacement-before.png were overwritten by later pre-answer captures of the same respective states; earlier DOM-to-frame timing unavailable. Original JSON retained; replay q10 frame retained separately.',
                     'Original name and last API translations were replaced; their UI remains unobserved.'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out-dir', required=True)
    args = parser.parse_args()
    values = build()
    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=False)
    for name, value in zip(['contract.json', 'reference.json', 'trace.json'], values):
        (out / name).write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n')
    print(json.dumps(dict(requirements=len(values[0]['requirements']), states=len(values[1]['states']))))
