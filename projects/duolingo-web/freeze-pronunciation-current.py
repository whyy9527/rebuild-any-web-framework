"""Add a current zero-phoneme-progress fixture; do not infer adaptive selection."""
import argparse,json
from pathlib import Path
from capabilities.rebuild.discovery import frontier
B=Path('projects/duolingo-web');E=B/'evidence/english-pronunciation-current-v1'
p=argparse.ArgumentParser();p.add_argument('--out-dir',required=True);out=Path(p.parse_args().out_dir);out.mkdir(parents=True,exist_ok=False)
def read(p):return json.loads(p.read_text())
c=read(B/'frontend-english-v73.json');prior=c['requirements'][:];aliases={};h=read(B/'evidence/english-guide-probes-v1/history.json')
for state,name in [('pronunciation-current-entry','entry'),('pronunciation-current-first','first-question')]:
 path=E/'source'/(name+'.json');s=read(path);ev=[str(path),str(path.with_suffix('.png'))];aliases[state]={}
 def add(suffix,kind,**kw):c['requirements'].append(dict(id=state+'-'+suffix,state=state,kind=kind,evidence=ev,**kw))
 add('whole','image_pixels',reference_image=ev[1],pixels=[1200,732],reference_capture=s['capture_geometry'])
 for j,t in enumerate(dict.fromkeys(t['text'] for t in s['text_runs'])):add('text-'+str(j),'accessible_text',text=t)
 choices=0
 for j,a in enumerate(s['actions']):
  key=f'{state}-action-{j}';native={'开始 +10 经验':'pronunciation-start','学习':'nav-learn','发音':'nav-pronunciation','排行榜':'nav-leaderboards','特别任务':'nav-quests','个人档案':'nav-profile','更多':'nav-more','跳过':'skip','检查':'check'}.get(a['name'])
  if state.endswith('first'):
   if a['test']=='quit-button':native='exit'
   elif a['role']=='radio':native='option-p0-o'+str(choices);choices+=1
   elif a['name']=='' and a['role']=='button':native='practice-play-0'
  if native:aliases[state][key]=native
  add('geometry-'+str(j),'element_geometry',element=key,rect=a['rect'],tolerance_points=0)
  if a['role'] is not None:add('role-'+str(j),'element_role',element=key,role=a['role'])
  add('enabled-'+str(j),'element_boolean',element=key,field='enabled',expected=a['enabled'])
 add('audio','pending',description='Observed media.play resource identity does not prove acoustic equality, complete sound effects or adaptive next-session selection')
 h['states'].append(dict(id=state,evidence=str(path),actions=s['actions']))
s=read(E/'source/entry.json');start=[a for a in s['actions'] if a['name']=='开始 +10 经验'];assert len(start)==1 and start[0]['role']=='link' and start[0]['rect'][2:]==[264,48]
h['transitions'].append({'from':'pronunciation-current-entry','to':'pronunciation-current-first','action':start[0]['id'],'outcome':'observed','evidence':str(E/'source/start.raw.txt')})
h['limitations']+=['Current pronunciation fixture has zero phoneme progress and actual dock/deck first; not a fourth sequential session or new adaptive-selection discovery']
assert c['requirements'][:len(prior)]==prior
c.update(revision='english-v74',parent_revision='english-v73',changes=['Revisit existing pronunciation entry from current guest zero-phoneme fixture','Actual source start is264x48 link; native pointer navigation and shared frontend contract verify without inferring adaptive selection'])
for name,data in [('contract.json',c),('aliases.json',aliases),('history.json',h),('frontier.json',frontier(Path.cwd(),h))]: (out/name).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(dict(prior=len(prior),requirements=len(c['requirements']),states=len(h['states']),edges=len(h['transitions']))))
