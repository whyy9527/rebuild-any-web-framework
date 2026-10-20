"""Append actual model-selected calendar states; keep every v76 requirement."""
import argparse, json
from pathlib import Path
from capabilities.rebuild.discovery import frontier

p=argparse.ArgumentParser();p.add_argument('--out-dir',required=True);out=Path(p.parse_args().out_dir);out.mkdir(parents=True,exist_ok=False)
B=Path('projects/duolingo-web');E=B/'evidence/english-streak-followup-v1'
read=lambda path:json.loads(path.read_text())
c=read(B/'frontend-english-v76.json');prior=c['requirements'][:]
h=read(B/'evidence/english-home-stat-branches-v1/history.json');aliases={}
for state,name in [('streak-hover','streak-root'),('streak-calendar','details-scoped-root'),('streak-bottom','deployment06/step1-after'),('streak-next','deployment06/step2-after')]:
    path=E/'source'/(name+'.json');s=read(path);assert s['capture_state_consistent']
    ev=[str(path),str(path.with_suffix('.png'))];aliases[state]={}
    for action in s['actions']:
        if action['role']=='button':action['operations']=['hover','click','Enter']
        elif action.get('test')=='close-button':action['operations']=['click']
    history_actions=s['actions'][:]
    if state!='streak-hover':
        panel=next(x for x in s['scroll_regions'] if x['rect']==[360,48,480,636])
        history_actions.append(dict(id='scroll:streak-calendar',name='连胜日历滚动面板',rect=panel['rect'],operations=['wheel'],evidence_origin='Actual scroll_regions entry in this state, not a semantic button'))
    h['states'].append(dict(id=state,evidence=str(path),actions=history_actions))
    def add(suffix,kind,**kw):c['requirements'].append(dict(id=state+'-'+suffix,state=state,kind=kind,evidence=ev,**kw))
    add('whole','image_pixels',reference_image=ev[1],pixels=[1200,732],reference_capture=dict(s['capture_geometry'],state_consistent=True))
    for i,t in enumerate(dict.fromkeys(x['text'] for x in s['text_runs'])):add('text-'+str(i),'accessible_text',text=t)
    unnamed=0
    for i,a in enumerate(s['actions']):
        key=state+'-action-'+str(i);native={'10':'stat-course','1':'stat-streak','155':'stat-gems','5':'stat-hearts','查看更多':'streak-details'}.get(a['name'])
        if a.get('test')=='close-button':native='streak-close'
        if a['role']=='button' and a['name']=='' and a['rect'][0] in [394,792]:
            native='streak-prev' if a['rect'][0]==394 else 'streak-next'
            assert unnamed<2;unnamed+=1
        if native:aliases[state][key]=native
        add('geometry-'+str(i),'element_geometry',element=key,rect=a['rect'],tolerance_points=0)
        if a['role']:add('role-'+str(i),'element_role',element=key,role=a['role'])
        add('enabled-'+str(i),'element_boolean',element=key,field='enabled',expected=a['enabled'])
    add('audio','pending',description='Source transitions not captured as aligned audio; equality and silence unknown')
    if state=='streak-hover':add('animation','pending',description='Original flame SVG frame captured; animation trajectory and timing not matched')
states={s['id']:s for s in h['states']}
for start,end,label,op,receipt in [('streak-hover','streak-calendar','查看更多','click','details-action.raw.txt'),('streak-calendar','streak-bottom','连胜日历滚动面板','wheel','deployment06/step1-action.raw.txt'),('streak-calendar','streak-next','','Enter','deployment06/step2-action.raw.txt')]:
    action=next(x for x in states[start]['actions'] if x['name']==label and (label!='' or x['rect'][0]==792))
    h['transitions'].append(dict(**{'from':start,'to':end},action=action['id'],operation=op,outcome='observed',evidence=str(E/'source'/receipt)))
c.update(revision='english-v77',parent_revision='english-v76',changes=['Actual original streak hover and calendar','Real model feedback deploys wheel then keyboard next month; lower goal/club and sticky header discovered','Full-image comparisons keep virtualized backdrop; no mask or causal gain claim'])
assert c['requirements'][:len(prior)]==prior
assert len({r['id'] for r in c['requirements']})==len(c['requirements'])
for name,d in [('contract.json',c),('aliases.json',aliases),('history.json',h),('frontier.json',frontier(Path.cwd(),h))]:
    (out/name).write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(dict(requirements=len(c['requirements']),states=len(h['states']),edges=len(h['transitions']))))
