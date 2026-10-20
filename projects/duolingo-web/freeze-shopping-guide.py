"""Append actual shopping guide frontend observations without relaxing v65."""
import argparse,json,re
from pathlib import Path
B=Path(__file__).resolve().parent;ROOT=B.parents[1];E=B/'evidence/english-shopping-guide-v1';S=E/'source'
p=argparse.ArgumentParser();p.add_argument('--out-dir',required=True);out=Path(p.parse_args().out_dir);out.mkdir(parents=True,exist_ok=False)
c=json.loads((B/'frontend-english-v65.json').read_text());prior=c['requirements'][:];reference=dict(states={});aliases={}
for state,name in [('shopping-guide-top','grocery-guide-v2-top'),('shopping-guide-bottom','grocery-guide-v2-bottom'),('shopping-guide-hat-hover','grocery-guide-v2-hat-hover'),('shopping-guide-hat-click','grocery-guide-v2-hat-click'),('shopping-guide-return','grocery-guide-v2-return')]:
 path=S/(name+'.json');s=json.loads(path.read_text());image=str(path.with_suffix('.png').relative_to(ROOT));ev=[str(path.relative_to(ROOT)),image]
 texts=list(dict.fromkeys(t['text'] for t in s['text_runs'] if not re.fullmatch('[A-Za-z.,!?]',t['text'])))
 if state!='shopping-guide-return':
  phrases=json.loads((B.parent/'education-swift/Sources/LingoSeed/Resources/Reference/shopping-guide.json').read_text())['phrases']
  for phrase in phrases:
   if any(phrase['translation']==t['text'] for t in s['text_runs']):texts.append(phrase['english'])
  ev.append(str((S/'grocery-guide-all-five-audio.raw.txt').relative_to(ROOT)))
 reference['states'][state]=dict(accessible_text=texts,elements={},capture=dict(path=image,content_rect_points=[0,0,1200,732],window_points=[1200,732],backing_scale=1));aliases[state]={}
 def add(suffix,kind,**kw):c['requirements'].append(dict(id=state+'-'+suffix,state=state,kind=kind,evidence=ev,**kw))
 add('whole','image_pixels',reference_image=image,pixels=[1200,732])
 for i,text in enumerate(texts):add('text-'+str(i),'accessible_text',text=text)
 speech=0
 for i,a in enumerate(s['actions']):
  key='shopping-guide-action-'+str(i);reference['states'][state]['elements'][key]={k:a[k] for k in ['rect','role','enabled']}
  native={'返回':'close-guide','学习':'nav-learn','打开这个部分的指南':'open-guide','查看排行榜':'view-leaderboards','显示全部':'view-quests'}.get(a['name'])
  if a['tag']=='BUTTON' and a['name']=='' and 270<a['rect'][0]<760:
   # Actual vertical order identifies current source phrase; offscreen buttons
   # remain in source control_inventory, not invented as visible controls.
   native='guide-speech-'+str(speech);speech+=1
  if native:aliases[state][key]=native
  add(key+'-geometry','element_geometry',element=key,rect=a['rect'],tolerance_points=0)
  if a['role'] is not None:add(key+'-role','element_role',element=key,role=a['role'])
  add(key+'-enabled','element_boolean',element=key,field='enabled',expected=a['enabled'])
 add('audio','pending',description='Actual source application output remains unavailable; five triggered public files are not acoustic equality')
c.update(revision='english-v66',parent_revision='english-v65',changes=['Five actual shopping speech triggers and English rendered whole sentences beyond per-letter ARIA','Roleless keyboard-focus token inventory retained; actual hat hover/click/Enter produced no popup','Source guide scrolling and return after coach recorded separately'])
assert c['requirements'][:len(prior)]==prior
for name,d in [('contract.json',c),('reference.json',reference),('aliases.json',aliases)]:(out/name).write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(dict(prior=len(prior),requirements=len(c['requirements']),new_states=len(reference['states']))))
