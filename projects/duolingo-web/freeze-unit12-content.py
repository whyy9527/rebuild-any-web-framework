"""Append executed unit12 content states without weakening v68."""
import argparse,json,re
from pathlib import Path
B=Path(__file__).resolve().parent;ROOT=B.parents[1];E=B/'evidence/english-unit12-content-v1/source'
p=argparse.ArgumentParser();p.add_argument('--out-dir',required=True);out=Path(p.parse_args().out_dir);out.mkdir(parents=True,exist_ok=False)
c=json.loads((B/'frontend-english-v68.json').read_text());prior=c['requirements'][:];reference=dict(states={});aliases={};cases=[]
for name,state in [('unit12-guide-ready-top','unit12-guide-top'),('unit12-guide-ready-bottom','unit12-guide-bottom'),('unit12-current-lesson-popup','unit12-home-popup'),('unit12-lesson-oral-before','unit12-home-speech'),('unit12-lesson-oral-closed','unit12-home-speech-declined'),('unit12-lesson-result-stable','unit12-home-result'),('unit12-lesson-review','unit12-home-review'),('unit12-lesson-after-result','unit12-home-profile'),('unit12-home-after-lesson','unit12-home-after')]:
 s=json.loads((E/(name+'.json')).read_text());cases.append((state,name,s))
index=0
for name in ['unit12-lesson-batch01','unit12-lesson-batch02']:
 d=json.loads((E/(name+'.json')).read_text());raws={v['index']:v['content'] for v in d['session']['challenges']}
 for row in d['observed']:
  if raws[row['index']]['type']=='speak':index+=1;continue
  if not row.get('feedback'):continue
  state=f'unit12-home-q{index}';index+=1
  for suffix,key,shot in [('-before','before','screenshot_before'),('-feedback','feedback','screenshot_feedback')]:
   cases.append((state+suffix,Path(row[shot]).stem,dict(source_receipt=name+'.json',snapshot=row[key],text_runs=[dict(text=t) for t in re.findall(r'heading "([^"\n]+)"',row[key])],actions=[])))
 for j,row in enumerate(d['interludes']):
  shot=row.get('screenshot')
  if shot:cases.append((f'unit12-home-interlude-{name[-2:]}-{j}',Path(shot).stem,dict(source_receipt=name+'.json',text_runs=[dict(text=t) for t in row['facts']['encouragement_messages']],actions=[])))
assert index==18
for state,name,s in cases:
 image=str((E/(name+'.png')).relative_to(ROOT));assert (ROOT/image).exists(),image
 receipt=E/(name+'.json');ev=[str((receipt if receipt.exists() else E/s['source_receipt']).relative_to(ROOT)),image]
 # Rolling digit DOM ranges include clipped inventory; their actually visible final value is checked by whole-image comparison.
 texts=list(dict.fromkeys(t['text'] for t in s['text_runs'] if not (state=='unit12-home-result' and re.fullmatch(r'\d',t['text']))))
 reference['states'][state]=dict(accessible_text=texts,elements={},capture=dict(path=image,content_rect_points=[0,0,1200,732],window_points=[1200,732],backing_scale=1));aliases[state]={}
 def add(suffix,kind,**kw):c['requirements'].append(dict(id=state+'-'+suffix,state=state,kind=kind,evidence=ev,**kw))
 add('whole','image_pixels',reference_image=image,pixels=[1200,732])
 for i,text in enumerate(texts):add('text-'+str(i),'accessible_text',text=text)
 for i,a in enumerate(s.get('actions',[])):
  key=f'{state}-action-{i}';reference['states'][state]['elements'][key]={k:a[k] for k in ['rect','role','enabled']}
  native={'学习':'nav-learn','现在不做口语题':'speech-decline','点击并开始录音':'speech-record','继续':'speech-continue' if state.endswith('speech-declined') else 'settlement-continue','回顾本单元':'settlement-secondary','稍后再说':'settlement-continue','打开这个部分的指南':'open-guide','返回':'close-guide','开始 +10 经验':'stage2-lesson-confirm'}.get(a['name'])
  if native:aliases[state][key]=native
  add(key+'-geometry','element_geometry',element=key,rect=a['rect'],tolerance_points=0)
  if a['role'] is not None:add(key+'-role','element_role',element=key,role=a['role'])
  add(key+'-enabled','element_boolean',element=key,field='enabled',expected=a['enabled'])
 add('audio','pending',description='Invocation resource/gain evidence is separate from acoustic equality; missed events remain unknown')
 if 'guide' in state or state.endswith('result'):add('motion','pending',description='Original source motion must be tested; a captured original frame does not establish animation equality')
c.update(revision='english-v69',parent_revision='english-v68',changes=['Actual unit12 guide and 17 graded questions, deferred oral branch, 18 review cards and home2of6','Original feedback volume0.35/completion0.5 observed; incomplete event windows retained','Clipped rolling digit inventory excluded from text assertions only; exact whole-result image retained'])
assert c['requirements'][:len(prior)]==prior
assert len({r['id'] for r in c['requirements']})==len(c['requirements'])
for name,data in [('contract.json',c),('reference.json',reference),('aliases.json',aliases)]: (out/name).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(dict(prior=len(prior),requirements=len(c['requirements']),new_states=len(cases))))
