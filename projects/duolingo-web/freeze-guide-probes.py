"""Append measured guide and keyboard observations; never rewrite old requirements."""
import argparse,json
from pathlib import Path
from capabilities.rebuild.discovery import frontier
B=Path('projects/duolingo-web');E=B/'evidence/english-guide-probes-v1';ROOT=Path.cwd()
p=argparse.ArgumentParser();p.add_argument('--out-dir',required=True);out=Path(p.parse_args().out_dir);out.mkdir(parents=True,exist_ok=False)
def read(p):return json.loads(p.read_text())
c=read(B/'frontend-english-v72.json');prior=c['requirements'][:];aliases={};reference={'states':{}}
for state in ['guide-root','guide-keyboard']:
 path=E/'source'/(state+'.json');s=read(path);ev=[str(path),str(path.with_suffix('.png'))];geometry=s['capture_geometry'];assert geometry['window_points']==[1200,732]
 texts=list(dict.fromkeys(t['text'] for t in s['text_runs']));reference['states'][state]={'accessible_text':texts,'elements':{},'capture':dict(path=ev[1],**geometry)};aliases[state]={}
 def add(suffix,kind,**kw):c['requirements'].append(dict(id=state+'-'+suffix,state=state,kind=kind,evidence=ev,**kw))
 add('whole','image_pixels',reference_image=ev[1],pixels=[1200,732],reference_capture=geometry)
 for j,t in enumerate(texts):add('text-'+str(j),'accessible_text',text=t)
 speech=0
 for j,a in enumerate(s['actions']):
  key=f'{state}-action-{j}';reference['states'][state]['elements'][key]={k:a[k] for k in ['rect','role','enabled']}
  native={'学习':'nav-learn','发音':'nav-pronunciation','排行榜':'nav-leaderboards','特别任务':'nav-quests','个人档案':'nav-profile','更多':'nav-more','返回':'close-guide'}.get(a['name'])
  if a['name']=='' and a['role']=='button':native='guide-speech-'+str(speech);speech+=1
  if native:aliases[state][key]=native
  add('geometry-'+str(j),'element_geometry',element=key,rect=a['rect'],tolerance_points=0)
  if a['role'] is not None:add('role-'+str(j),'element_role',element=key,role=a['role'])
  add('enabled-'+str(j),'element_boolean',element=key,field='enabled',expected=a['enabled'])
 if state=='guide-keyboard':
  assert s['focus']['name']=='welcome' and s['focus']['focus_visible'] is True
  add('welcome-keyboard-focus','interaction_boolean',field='guide_welcome_keyboard_focus',expected=True)
 add('source-acoustic-equality','pending',description='Guide phrase resources exist; original browser acoustic output and complete effects remain unverified')
c.update(revision='english-v73',parent_revision='english-v72',changes=['Fresh measured guide viewport/DPR, distinct post-04 product follow-up','Original actual Hi focus then Tab reaches welcome; semantic novelty proxy omits this behavior'])
assert c['requirements'][:len(prior)]==prior
assert len({r['id'] for r in c['requirements']})==len(c['requirements'])
h=read(B/'evidence/english-unit12-frontend-repair-v1/history.json')
# Four training plus four online executions retained, including repeated Enter room.
A=Path('projects/exploration-ablation/evidence');procedures=[]
# Collection shape retained in evidence; derive paired captures, not imagined outcomes.
for group in [A/'training04']+sorted(p for p in (A/'online04').iterdir() if p.is_dir()):
 for before in sorted(group.glob('*-before.json')):
  after=before.with_name(before.name.replace('-before.json','-after.json'))
  action=before.with_name(before.name.replace('-before.json','-action.raw.txt'))
  if not after.exists() or not action.exists():continue
  stem='guide04-'+group.name+'-'+before.stem.removesuffix('-before')
  for suffix,path in [('before',before),('after',after)]:h['states'].append(dict(id=stem+'-'+suffix,evidence=str(path),actions=read(path)['actions']))
  procedures.append({'from':stem+'-before','to':stem+'-after','action':'recorded-grouped-probe','outcome':'observed','evidence':str(action)})
# Grouped setup+Tab receipt, not a direct Tab from unfocused root.
for state in ['guide-root','guide-keyboard']:h['states'].append(dict(id=state,evidence=str(E/'source'/(state+'.json')),actions=read(E/'source'/(state+'.json'))['actions']))
# Discovery requires real known action identity. Grouped programmatic focus then Tab
# is an observation procedure and stays outside pointer-action coverage edges.
h['limitations']+=['04 semantic proxy zero result does not establish no focus/visual/audio change','Guide follow-up explicitly focuses Hi then presses Tab; procedure is recorded separately, not a pointer click edge','Old04 screenshots lack measured CSS/DPR and are not retroactively normalized for 1:1']
# Experiment grouped probes do not correspond one-to-one to a source action id;
# keep them as procedures, not false executed edges in frontier.
assert len(procedures)==8, 'Expected exactly eight recorded04 procedures'
assert len({s['id'] for s in h['states']})==len(h['states'])
f=frontier(ROOT,h)
feedback={'prior':'english-unit12-frontend-repair-v1/exploration-feedback.json','experiment04':'projects/exploration-ablation/REPORT04.md','findings':['Actual 04 semantic proxy0/0 leaves focus/visual/audio unmeasured','Source Hi focus+Tab reaches welcome focus-visible; native tokens have no corresponding controls','Old native fixture includes pending pronunciation coach: mismatched baseline retained, matched dismissed fixture rerun separately'],'next_exploration':['Use whole-home/frontend failure and unknown consumers as allocation signals, rather than word-count novelty alone','Pronunciation full exercise chain and source audio, home lower path/story/radio/guide flows','Third original lesson after observed skip, review and progress restoration','Guide keyboard traversal and input-mode effects including source audio attribution'],'causal_status':'No RSI gain or 1:1 claim'}
for name,data in [('contract.json',c),('reference.json',reference),('aliases.json',aliases),('history.json',h),('frontier.json',f),('experiment-procedures.json',procedures),('exploration-feedback.json',feedback)]: (out/name).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(dict(prior=len(prior),requirements=len(c['requirements']),states=len(h['states']),edges=len(h['transitions']),pending=len(f['pending']))))
