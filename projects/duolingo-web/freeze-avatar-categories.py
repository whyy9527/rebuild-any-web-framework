"""Freeze nine real category states and seven explored lower groups, preserving v58."""
import argparse
import json
from pathlib import Path

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[1]
E = BASE / 'evidence/english-avatar-categories-v1'


def build():
    contract = json.loads((BASE / 'frontend-english-v58.json').read_text())
    prior = contract['requirements'][:]
    reference = {'states': {}}
    groups = json.loads((E / 'renderer-config.json').read_text())['stateChooserTabs']
    aliases = {}
    for folder, pattern, prefix in [('source', 'category-*.json', 'avatar-category-'),
                                     ('lower-groups', 'group-*.json', 'avatar-lower-')]:
        for file in sorted((E / folder).glob(pattern)):
            source = json.loads(file.read_text())
            assert source['viewport'] == {'width': 1200, 'height': 732}
            key = prefix + file.stem.split('-')[-1]
            evidence = [str(file.relative_to(ROOT)), str(file.with_suffix('.png').relative_to(ROOT))]
            assert file.with_suffix('.png').is_file()
            texts = list(dict.fromkeys(t['text'] for t in source['text_runs']))
            state = {'accessible_text': texts, 'elements': {}, 'capture': {
                'path': evidence[1], 'content_rect_points': [0, 0, 1200, 732],
                'window_points': [1200, 732], 'backing_scale': 1}}
            reference['states'][key] = state
            aliases[key] = {}

            def add(suffix, kind, **fields):
                contract['requirements'].append(dict(id=key+'-'+suffix, state=key,
                    kind=kind, evidence=evidence, **fields))

            add('whole', 'image_pixels', reference_image=evidence[1], pixels=[1200, 732])
            for i, text in enumerate(texts):
                add('text-'+str(i), 'accessible_text', text=text)
            # Actual grouped DOM inventory retains clipped options, separately
            # from visible controls. No claim that all options were exercised.
            if folder == 'source':
                category = int(file.stem.split('-')[-1])
                sections = groups[category]['sections']
                assert len(sections) == len(source['radio_groups'])
                for section, group in zip(sections, source['radio_groups']):
                    buttons = section['imageButtons'] if section['buttonType']=='IMAGE' else section['featureButtons']
                    assert section['header']==group['label'] and len(buttons)==len(group['options'])
            for i, action in enumerate(source['actions']):
                if action['rect'][0] < 260:
                    continue
                name = 'category-action-'+str(i)
                state['elements'][name] = {f: action[f] for f in ['rect','role','enabled','checked']}
                add(name+'-geometry', 'element_geometry', element=name, rect=action['rect'], tolerance_points=0)
                if action['role'] is not None:
                    add(name+'-role', 'element_role', element=name, role=action['role'])
                add(name+'-enabled', 'element_boolean', element=name, field='enabled', expected=action['enabled'])
                if isinstance(action.get('checked'), bool):
                    add(name+'-checked', 'element_boolean', element=name, field='checked', expected=action['checked'])
                native = None
                if action['name']=='完成': native='avatar-done'
                if action['role']=='button' and action['rect'][:2]==[280,24]: native='avatar-back'
                if action.get('kind')=='pointer_candidate' and action['rect'][1:]==[82,58,64]:
                    native='avatar-category-'+str(round((action['rect'][0]-672)/58))
                if folder=='source' and action['role']=='radio':
                    for section, group in zip(sections,source['radio_groups']):
                        buttons=section['imageButtons'] if section['buttonType']=='IMAGE' else section['featureButtons']
                        for button, option in zip(buttons,group['options']):
                            if option['rect']==action['rect']:
                                native=('avatar-skin-'+str(15-button['value'])) if button['state']=='SkinTone' else 'avatar-choice-'+button['state']+'-'+str(button['value'])
                if native: aliases[key][name]=native
            add('audio', 'pending', description='Actual source/native acoustic comparison remains unverified')
            add('all-options', 'pending', description='Full grouped inventory retained in source; each option interaction, composition and saved recovery must still be executed')
    contract.update(revision='english-v59', parent_revision='english-v58', changes=[
        'Nine actual category visits and seven selected/revisited lower groups',
        'Full DOM radio groups and scroll/clipping inventory now distinguish present options from visited actions',
        'Original public Rive renderer/config located; no animation or composition pass inferred'])
    assert contract['requirements'][:len(prior)] == prior
    assert len({r['id'] for r in contract['requirements']}) == len(contract['requirements'])
    setup=[{'native_action':n} for n in ['nav-leaderboards','leaderboard-guest-profile','guest-profile-start','avatar-skin-1','avatar-done','avatar-keep']]
    setup += [{'native_action':'nav-leaderboards','operation':'restart'}, {'native_action':'leaderboard-guest-profile'}, {'native_action':'guest-profile-avatar','state':'avatar-category-0','element_aliases':aliases['avatar-category-0']}]
    for i in range(1,9):
        setup.append({'native_action':'avatar-category-'+str(i),'state':'avatar-category-'+str(i),'element_aliases':aliases['avatar-category-'+str(i)]})
    scenario={'journeys':[{'id':'avatar-categories','steps':setup}]}
    return contract, reference, scenario


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--out-dir',required=True)
    out=Path(parser.parse_args().out_dir);out.mkdir(parents=True,exist_ok=False)
    for name,value in zip(['contract.json','reference.json','scenarios.json'],build()):
        (out/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
