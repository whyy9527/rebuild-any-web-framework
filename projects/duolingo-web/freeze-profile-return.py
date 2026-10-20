"""Freeze actual saved-profile and home-section routes; retain all v60 requirements."""
import argparse
import json
from pathlib import Path
BASE=Path(__file__).resolve().parent
ROOT=BASE.parents[1]
E=BASE/'evidence/english-profile-return-v1'
def build(with_closure=False):
    c=json.loads((BASE/('frontend-english-v61.json' if with_closure else 'frontend-english-v60.json')).read_text());prior=c['requirements'][:]
    reference=json.loads((E/'reference.json').read_text()) if with_closure else {'states':{}};aliases={}
    if with_closure:
        for journey in json.loads((BASE/'profile-return-scenarios-v1.json').read_text())['journeys']:
            for row in journey['steps']:
                if 'state' in row:aliases[row['state']]=row['element_aliases']
    stems=['languages-after-escape-visible','languages-close-button','enrollment-return'] if with_closure else ['clean-back','edit-from-pencil','home','home-return','languages','profile','section-test-first','section-test-intro','sections','sections-return']
    for stem in (stems if with_closure else sorted(stems,key=lambda name:name+'.json')):
        f=E/'source'/(stem+'.json')
        s=json.loads(f.read_text());assert s['viewport']=={'width':1200,'height':732}
        key='profile-return-'+f.stem;ev=[str(f.relative_to(ROOT)),str(f.with_suffix('.png').relative_to(ROOT))]
        state={'accessible_text':list(dict.fromkeys(t['text'] for t in s['text_runs'])),'elements':{},'capture':{'path':ev[1],'content_rect_points':[0,0,1200,732],'window_points':[1200,732],'backing_scale':1}}
        reference['states'][key]=state;aliases[key]={}
        def add(suffix,kind,**kw):c['requirements'].append(dict(id=key+'-'+suffix,state=key,kind=kind,evidence=ev,**kw))
        add('whole','image_pixels',reference_image=ev[1],pixels=[1200,732])
        for i,t in enumerate(state['accessible_text']):add('text-'+str(i),'accessible_text',text=t)
        for i,a in enumerate(s['actions']):
            if a['rect'][0]<260 and s['path']!='/errors/404.html':continue
            name='return-action-'+str(i);state['elements'][name]={k:a[k] for k in ['rect','role','enabled','checked']}
            add(name+'-geometry','element_geometry',element=name,rect=a['rect'],tolerance_points=0)
            if a['role'] is not None:add(name+'-role','element_role',element=name,role=a['role'])
            add(name+'-enabled','element_boolean',element=name,field='enabled',expected=a['enabled'])
            if type(a['checked']) is bool:add(name+'-checked','element_boolean',element=name,field='checked',expected=a['checked'])
            native={'显示全部':'guest-profile-achievements','所有语言':'guest-profile-languages','返回':'sections-return','继续':'sections-continue'}.get(a['name'])
            if a['href']=='/sections':native='open-sections'
            if f.stem in ['profile','languages','languages-after-escape-visible','languages-close-button']:
                if a['rect']==[696,40,48,48]:native='guest-profile-edit'
                if a['rect']==[410,24,220,224]:native='guest-profile-avatar'
                if a['rect']==[721,276,39,43.9140625]:native='guest-profile-languages'
                if a['name'].startswith('英语（'):native='guest-profile-language-en-zh'
                if a['rect']==[380,280,32,32]:native='guest-profile-languages-close'
            if f.stem=='edit-from-pencil':
                if a['rect'][2:]==[24,32]:native='avatar-back'
                if a['name']=='完成':native='avatar-done'
                if a['role']=='radio':
                    options=s['radio_groups'][0]['options']
                    for index,o in enumerate(options):
                        if o['rect']==a['rect']:native='avatar-skin-'+str(index)
            if f.stem=='clean-back':native={'duolingo.com':'guest-error-home','Twitter':'guest-error-twitter','Facebook':'guest-error-facebook'}.get(a['name'],'guest-error-logo')
            if native:aliases[key][name]=native
        if f.stem in ['profile','languages','languages-after-escape-visible','languages-close-button']:
            canvas=next(m for m in s['media'] if m['tag']=='CANVAS');name='profile-avatar-canvas';state['elements'][name]={'rect':canvas['rect']};aliases[key][name]='guest-profile-avatar-renderer';add(name,'element_geometry',element=name,rect=canvas['rect'],tolerance_points=0)
        add('audio','pending',description='Actual acoustic equality remains unverified')
    if with_closure:
        for key,state in reference['states'].items():
            f=E/'source'/(key.removeprefix('profile-return-')+'.json');source=json.loads(f.read_text())
            state['interactions']={'guest_languages_present':any(t['text']=='所有语言' for t in source['text_runs']),'guest_error_present':source['path']=='/errors/404.html','home_course_present':source['path']=='/learn' and any('第 1 阶段' in t['text'] for t in source['text_runs'])}
            for field,value in state['interactions'].items():
                c['requirements'].append(dict(id=key+'-actual-'+field,state=key,kind='interaction_boolean',field=field,expected=value,evidence=[str(f.relative_to(ROOT))]))
    def step(action,stem=None,**kw):
        d={'native_action':action,**kw}
        if stem:d.update(state='profile-return-'+stem,element_aliases=aliases['profile-return-'+stem])
        return d
    scenarios={'journeys':[
        {'id':'saved-profile-return','steps':[step('nav-leaderboards'),step('leaderboard-guest-profile','profile'),step('guest-profile-languages','languages'),step('guest-profile-languages',operation='escape'),step('guest-profile-edit','edit-from-pencil'),step('avatar-back','clean-back'),step('guest-error-home','home-return')]},
        {'id':'home-section-entry','steps':[step('nav-learn','home'),step('open-sections','sections')]}
    ],'limits':['Prepared native preferences from prior actual save; source prepared by actual selections, not server reset','Stage2 intro/first question/return captured but not yet native-executed','Inventory is not executed coverage']}
    if with_closure:
        scenarios['journeys'][0]['steps']=[step('nav-leaderboards'),step('leaderboard-guest-profile','profile'),step('guest-profile-languages','languages'),step('guest-profile-languages','languages-after-escape-visible',operation='escape'),step('guest-profile-languages-close','languages-close-button'),step('guest-profile-languages'),step('guest-profile-language-en-zh','enrollment-return'),step('nav-leaderboards'),step('leaderboard-guest-profile'),step('guest-profile-edit','edit-from-pencil'),step('avatar-back','clean-back'),step('guest-error-home','home-return')]
    c.update(revision='english-v61',parent_revision='english-v60',changes=['Actual saved composition rendered on independent profile, country-language modal, pencil and clean-back/error/home','Previously missing home section route, stage2 test intro/first question/quit and stage1 Continue return'])
    if with_closure:c.update(revision='english-v62',parent_revision='english-v61',changes=['Repeated original Escape remained visible; actual X dismissal and enrollment return frozen separately','Actual modal/error/home presence checked after actions; keep original failed Escape assumption and all v61 requirements'])
    assert c['requirements'][:len(prior)]==prior
    assert len({r['id'] for r in c['requirements']})==len(c['requirements'])
    return c,reference,scenarios
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out-dir',required=True);p.add_argument('--with-closure',action='store_true');a=p.parse_args();o=Path(a.out_dir);o.mkdir(parents=True,exist_ok=False)
    for n,d in zip(['contract.json','reference.json','scenarios.json'],build(a.with_closure)):(o/n).write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
