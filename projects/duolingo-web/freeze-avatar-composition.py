"""Compile the actual multi-property selection/save/reload observations; retain v59."""
import argparse
import json
from pathlib import Path
BASE=Path(__file__).resolve().parent
ROOT=BASE.parents[1]
E=BASE/'evidence/english-avatar-composition-v1'


def build():
    contract=json.loads((BASE/'frontend-english-v59.json').read_text());prior=contract['requirements'][:]
    config=json.loads((BASE/'evidence/english-avatar-categories-v1/renderer-config.json').read_text())['stateChooserTabs']
    reference={'states':{}};aliases={}
    cases=[(f'selected-{i}',c) for i,c in enumerate([1,3,4,8])]+[('saved',8),('reloaded-ready',0)]+[(f'restored-{i}',i) for i in range(9)]
    for stem,category in cases:
        file=E/(stem+'.json');s=json.loads(file.read_text());assert s['viewport']=={'width':1200,'height':732}
        key='avatar-composition-'+stem;ev=[str(file.relative_to(ROOT)),str(file.with_suffix('.png').relative_to(ROOT))];assert file.with_suffix('.png').exists()
        state={'accessible_text':list(dict.fromkeys(t['text'] for t in s['text_runs'])),'elements':{},'capture':{'path':ev[1],'content_rect_points':[0,0,1200,732],'window_points':[1200,732],'backing_scale':1}}
        reference['states'][key]=state;aliases[key]={}
        def add(suffix,kind,**fields):contract['requirements'].append(dict(id=key+'-'+suffix,state=key,kind=kind,evidence=ev,**fields))
        add('whole','image_pixels',reference_image=ev[1],pixels=[1200,732])
        for i,t in enumerate(state['accessible_text']):add('text-'+str(i),'accessible_text',text=t)
        sections=config[category]['sections'];assert len(sections)==len(s['radio_groups'])
        for i,a in enumerate(s['actions']):
            if a['rect'][0]<260:continue
            name='composition-action-'+str(i);state['elements'][name]={f:a[f] for f in ['rect','role','enabled','checked']}
            add(name+'-geometry','element_geometry',element=name,rect=a['rect'],tolerance_points=0)
            if a['role'] is not None:add(name+'-role','element_role',element=name,role=a['role'])
            add(name+'-enabled','element_boolean',element=name,field='enabled',expected=a['enabled'])
            if isinstance(a.get('checked'),bool):add(name+'-checked','element_boolean',element=name,field='checked',expected=a['checked'])
            native={'完成':'avatar-done','继续编辑虚拟头像':'avatar-keep','放弃编辑虚拟头像':'avatar-discard'}.get(a['name'])
            if a['role']=='button' and a['name']=='' and a['rect'][2:]==[24,32]:native='avatar-back'
            if a.get('kind')=='pointer_candidate' and a['rect'][2:]==[58,64]:native='avatar-category-'+str(round((a['rect'][0]-672)/58))
            if a['role']=='radio':
                for section,group in zip(sections,s['radio_groups']):
                    buttons=section['imageButtons'] if section['buttonType']=='IMAGE' else section['featureButtons'];assert len(buttons)==len(group['options'])
                    for b,o in zip(buttons,group['options']):
                        if o['rect']==a['rect']:native='avatar-skin-'+str(15-b['value']) if b['state']=='SkinTone' else 'avatar-choice-'+b['state']+'-'+str(b['value'])
            if native:aliases[key][name]=native
        add('audio','pending',description='Actual source/native acoustic equality unverified')
    contract.update(revision='english-v60',parent_revision='english-v59',changes=['Actual Body3/MainHair59/Nose Piercing1/BackgroundColor2 selection and combined save/reload','Nine restored groups frozen from UI, including original selection geometry after scroll'])
    assert contract['requirements'][:len(prior)]==prior
    assert len({r['id'] for r in contract['requirements']})==len(contract['requirements'])
    # Reproduce the recorded old saved skin1 before applying the new combination.
    steps=[dict(s) for s in json.loads((BASE/'avatar-categories-scenarios-v1.json').read_text())['journeys'][0]['steps']]
    for s in steps:s.pop('state',None);s.pop('element_aliases',None)
    def press(native,stem=None,**extra):
        row={'native_action':native,**extra}
        if stem:row.update(state='avatar-composition-'+stem,element_aliases=aliases['avatar-composition-'+stem])
        steps.append(row)
    press('avatar-category-1');press('avatar-choice-Body-3','selected-0')
    press('avatar-category-3');press('avatar-choice-MainHair-59','selected-1')
    press('avatar-category-4');press('avatar-options',operation='scroll',scroll_pixels=-1152,scroll_anchor='avatar-choice-Nose Piercing-1');press('avatar-choice-Nose Piercing-1','selected-2')
    press('avatar-category-8');press('avatar-choice-BackgroundColor-2','selected-3')
    press('avatar-preview',operation='scroll',scroll_pixels=-500,scroll_anchor='avatar-done');press('avatar-done','saved');press('avatar-keep')
    press('nav-leaderboards',operation='restart');press('leaderboard-guest-profile');press('guest-profile-avatar','reloaded-ready')
    for i in range(9):press('avatar-category-'+str(i),'restored-'+str(i))
    return contract,reference,{'journeys':[{'id':'avatar-composition','steps':steps}]}

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out-dir',required=True);out=Path(p.parse_args().out_dir);out.mkdir(parents=True,exist_ok=False)
    for name,value in zip(['contract.json','reference.json','scenarios.json'],build()):(out/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
