"""Freeze the complete actually executed second home lesson; preserve v70."""
import argparse,json,re
from pathlib import Path
B=Path(__file__).resolve().parent;ROOT=B.parents[1];E=B/'evidence/english-unit12-lesson2-v1';S=E/'source';OLD=B/'evidence/english-unit12-content-v1'
p=argparse.ArgumentParser();p.add_argument('--out-dir',required=True);out=Path(p.parse_args().out_dir);out.mkdir(parents=True,exist_ok=False)
c=json.loads((B/'frontend-english-v70.json').read_text());prior=c['requirements'][:];ref=json.loads((OLD/'next-reference.json').read_text());aliases=json.loads((OLD/'next-aliases.json').read_text());cases=[];i=0
fixture=json.loads((B/'fixture-reference-en-zh-unit12-lesson2-v1.json').read_text())['data']['candidate_course']['lessons'][0];questions={q['id']:q for q in fixture['questions']}
for name in ['unit12-lesson2-surface-probe','unit12-lesson2-batch01','unit12-lesson2-batch02']:
 d=json.loads((S/(name+'.json')).read_text());raws={r['index']:r['content'] for r in d['session']['challenges']}
 for row in d['observed']:
  if raws[row['index']]['type']=='speak':i+=1;continue
  if not row.get('feedback'):continue
  q=questions[f'unit12-q{i}']
  if i>0:
   for suffix,key,shot in [('before','frontend_before','screenshot_before'),('feedback','frontend_feedback','screenshot_feedback')]:
    surface=dict(row[key],text_runs=[dict(text=row['heading'])]);cases.append((f'unit12-lesson2-q{i}-{suffix}',Path(row[shot]).stem,surface,name+'.json',q))
  i+=1
 for j,row in enumerate(d['interludes']):cases.append((f'unit12-lesson2-interlude-{j}',Path(row['screenshot']).stem,dict(text_runs=[dict(text=t) for t in row['facts']['encouragement_messages']],actions=[]),name+'.json',None))
assert i==13
for name,state in [('unit12-lesson2-oral-before','unit12-lesson2-speech'),('unit12-lesson2-oral-closed','unit12-lesson2-speech-declined'),('unit12-lesson2-result','unit12-lesson2-result'),('unit12-lesson2-review','unit12-lesson2-review'),('unit12-lesson2-after-result','unit12-lesson2-profile'),('unit12-lesson2-home-after','unit12-lesson2-home-after')]:
 s=json.loads((S/(name+'.json')).read_text());s['text_runs']=[t for t in s['text_runs'] if not (state=='unit12-lesson2-result' and re.fullmatch(r'\d',t['text']))];cases.append((state,name,s,name+'.json',None))
for state,name,s,receipt,q in cases:
 image=str((S/(name+'.png')).relative_to(ROOT));assert (ROOT/image).exists();ev=[str((S/receipt).relative_to(ROOT)),image]
 texts=list(dict.fromkeys(t['text'] for t in s['text_runs']));ref['states'][state]=dict(accessible_text=texts,elements={},capture=dict(path=image,content_rect_points=[0,0,1200,732],window_points=[1200,732],backing_scale=1));aliases[state]={}
 def add(suffix,kind,**kw):c['requirements'].append(dict(id=state+'-'+suffix,state=state,kind=kind,evidence=ev,**kw))
 add('whole','image_pixels',reference_image=image,pixels=[1200,732])
 for j,text in enumerate(texts):add('text-'+str(j),'accessible_text',text=text)
 for j,a in enumerate(s['actions']):
  key=f'{state}-action-{j}';ref['states'][state]['elements'][key]={k:a[k] for k in ['rect','role','enabled']}
  native={'现在不做口语题':'speech-decline','继续':'speech-continue' if state.endswith('speech-declined') else 'continue' if q else 'settlement-continue','回顾本单元':'settlement-secondary','稍后再说':'settlement-continue','检查':'check','跳过':'skip','学习':'nav-learn','发音':'nav-pronunciation'}.get(a['name'])
  if a.get('test')=='quit-button':native='exit'
  if q and a['role']=='radio':
   clean=re.sub(r'^\d\s*|\s*\d$','',a['name']).strip();opts=[o for o in q.get('options',[]) if o['text']==clean]
   if len(opts)==1:native='option-'+opts[0]['id']
  if q and q['kind']=='word_tiles' and not native:
   words=[w for w in q['words'] if w['text']==a['name'].strip()]
   if len(words)==1:native=('selected-word-' if state.endswith('feedback') and words[0]['id'] in q['answer_words'] else 'word-bank-')+words[0]['id']
  if native:aliases[state][key]=native
  add('geometry-'+str(j),'element_geometry',element=key,rect=a['rect'],tolerance_points=0)
  if a['role'] is not None:add('role-'+str(j),'element_role',element=key,role=a['role'])
  add('enabled-'+str(j),'element_boolean',element=key,field='enabled',expected=a['enabled'])
 add('audio','pending',description='Source invocation window and source acoustic output remain separate requirements')
c.update(revision='english-v71',parent_revision='english-v70',changes=['All12accepted, deferred oral, two encouragements,13cards and observed home3of6','Actual frontend surfaces retain CSS/range/clipping/hit-test; contract checks whole image plus control rect/role/enabled, not inferred CSS parity','Original junior+Duo result frame remains distinct from prior Vikram frame'])
assert c['requirements'][:len(prior)]==prior
assert len({r['id'] for r in c['requirements']})==len(c['requirements'])
for name,data in [('contract.json',c),('reference.json',ref),('aliases.json',aliases)]:(out/name).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(dict(prior=len(prior),requirements=len(c['requirements']),new_states=len(cases))))
