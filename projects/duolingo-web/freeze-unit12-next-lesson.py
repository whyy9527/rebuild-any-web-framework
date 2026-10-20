"""Freeze actual new omissions; an unimplemented discovered state stays not_run."""
import argparse,json
from pathlib import Path
B=Path(__file__).resolve().parent;ROOT=B.parents[1];E=B/'evidence/english-unit12-content-v1';S=E/'source'
p=argparse.ArgumentParser();p.add_argument('--out-dir',required=True);out=Path(p.parse_args().out_dir);out.mkdir(parents=True,exist_ok=False)
c=json.loads((B/'frontend-english-v69.json').read_text());prior=c['requirements'][:];ref=dict(states={});aliases={};cases=[]
for name,state in [('unit12-radio-popover','unit12-radio-locked'),('unit12-radio-intercepted','unit12-pronunciation-coach'),('unit12-lesson2-popup','unit12-next-popup')]:cases.append((state,name,json.loads((S/(name+'.json')).read_text()),[str((S/(name+'.json')).relative_to(ROOT))]))
batch=json.loads((S/'unit12-lesson2-surface-probe.json').read_text());assert batch['accepted']==1 and batch['session']['challenges'][0]['content']['type']=='select'
row=batch['observed'][0]
for suffix,key,shot in [('before','frontend_before','screenshot_before'),('feedback','frontend_feedback','screenshot_feedback')]:cases.append(('unit12-next-q0-'+suffix,Path(row[shot]).stem,row[key],[str((S/'unit12-lesson2-surface-probe.json').relative_to(ROOT))]))
for state,name,s,ev in cases:
 image=str((S/(name+'.png')).relative_to(ROOT));assert (ROOT/image).exists();ev=ev+[image];texts=list(dict.fromkeys(t['text'] for t in s['text_runs']))
 ref['states'][state]=dict(accessible_text=texts,elements={},capture=dict(path=image,content_rect_points=[0,0,1200,732],window_points=[1200,732],backing_scale=1));aliases[state]={}
 def add(suffix,kind,**kw):c['requirements'].append(dict(id=state+'-'+suffix,state=state,kind=kind,evidence=ev,**kw))
 add('whole','image_pixels',reference_image=image,pixels=[1200,732])
 for i,text in enumerate(texts):add('text-'+str(i),'accessible_text',text=text)
 for i,a in enumerate(s['actions']):
  key=state+'-action-'+str(i);ref['states'][state]['elements'][key]={k:a[k] for k in ['rect','role','enabled']}
  if a['name']=='开始 +10 经验':aliases[state][key]='stage2-lesson-confirm'
  add('geometry-'+str(i),'element_geometry',element=key,rect=a['rect'],tolerance_points=0)
  if a['role'] is not None:add('role-'+str(i),'element_role',element=key,role=a['role'])
  add('enabled-'+str(i),'element_boolean',element=key,field='enabled',expected=a['enabled'])
 add('audio','pending',description='Source invocation and acoustic comparison pending for this new branch')
c.update(revision='english-v70',parent_revision='english-v69',changes=['Delayed pronunciation coach intercepts radio/home actions; actual backdrop click dismisses it','Original unit12 radio is locked apartment tour','Lesson2of6 begins with select living-room, not repeated first lesson','Replay now captures actual frontend control geometry/CSS/hit-test/text/clipping before and after each question'])
assert c['requirements'][:len(prior)]==prior
assert len({r['id'] for r in c['requirements']})==len(c['requirements'])
for name,data in [('contract.json',c),('reference.json',ref),('aliases.json',aliases)]:(out/name).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(dict(prior=len(prior),requirements=len(c['requirements']),new_states=len(cases))))
