"""Preserve v71 and freeze actual reload/reminder/third-lesson entry evidence."""
import argparse,json
from pathlib import Path
B=Path(__file__).resolve().parent;ROOT=B.parents[1];E=B/'evidence/english-unit12-lesson2-v1';S=E/'source'
p=argparse.ArgumentParser();p.add_argument('--out-dir',required=True);out=Path(p.parse_args().out_dir);out.mkdir(parents=True,exist_ok=False)
c=json.loads((B/'frontend-english-v71.json').read_text());prior=c['requirements'][:];ref=json.loads((E/'reference.json').read_text());aliases=json.loads((E/'aliases.json').read_text())
for state,name in [('unit12-lesson2-home-restarted','unit12-lesson2-home-reloaded'),('unit12-lesson3-notification','unit12-lesson3-notification'),('unit12-lesson3-popup','unit12-lesson3-popup'),('unit12-lesson3-first-question','unit12-lesson3-first-question'),('unit12-lesson3-skip-feedback','unit12-lesson3-skip-feedback')]:
 source=S if name not in ['unit12-lesson3-first-question','unit12-lesson3-skip-feedback'] else B/'evidence/english-unit12-frontend-repair-v1/source'
 s=json.loads((source/(name+'.json')).read_text());image=str((source/(name+'.png')).relative_to(ROOT));ev=[str((source/(name+'.json')).relative_to(ROOT)),image]
 texts=list(dict.fromkeys(t['text'] for t in s['text_runs']));ref['states'][state]=dict(accessible_text=texts,elements={},capture=dict(path=image,content_rect_points=[0,0,1200,732],window_points=[1200,732],backing_scale=1));aliases[state]={}
 def add(suffix,kind,**kw):c['requirements'].append(dict(id=state+'-'+suffix,state=state,kind=kind,evidence=ev,**kw))
 add('whole','image_pixels',reference_image=image,pixels=[1200,732])
 for j,text in enumerate(texts):add('text-'+str(j),'accessible_text',text=text)
 for j,a in enumerate(s['actions']):
  key=f'{state}-action-{j}';ref['states'][state]['elements'][key]={k:a[k] for k in ['rect','role','enabled']}
  native={'学习':'nav-learn','发音':'nav-pronunciation','排行榜':'nav-leaderboards','特别任务':'nav-quests','个人档案':'nav-profile','更多':'nav-more','开始 +10 经验':'stage2-lesson-confirm','Lesson 3 of 6':'unit12-path-0'}.get(a['name'])
  if native:aliases[state][key]=native
  add('geometry-'+str(j),'element_geometry',element=key,rect=a['rect'],tolerance_points=0)
  if a['role'] is not None:add('role-'+str(j),'element_role',element=key,role=a['role'])
  add('enabled-'+str(j),'element_boolean',element=key,field='enabled',expected=a['enabled'])
 add('audio','pending',description='No source acoustic equality or reminder sound evidence inferred')
c.update(revision='english-v72',parent_revision='english-v71',changes=['Actual reload keeps Lesson3of6; reminder blocks node click until declined','Third lesson first prompt and actual empty skip captured; hearts stay4, remaining lesson unknown'])
assert c['requirements'][:len(prior)]==prior
assert len({r['id'] for r in c['requirements']})==len(c['requirements'])
for name,data in [('contract.json',c),('reference.json',ref),('aliases.json',aliases)]:(out/name).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(dict(prior=len(prior),requirements=len(c['requirements']),new_states=5)))
