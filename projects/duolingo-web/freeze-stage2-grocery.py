"""Append real grocery frontend observations; preserve all v64 requirements."""
import argparse,json,re
from pathlib import Path
BASE=Path(__file__).resolve().parent;ROOT=BASE.parents[1];E=BASE/'evidence/english-stage2-path-v1/source'
p=argparse.ArgumentParser();p.add_argument('--out-dir',required=True);out=Path(p.parse_args().out_dir);out.mkdir(parents=True,exist_ok=False)
c=json.loads((BASE/'frontend-english-v64.json').read_text());prior=c['requirements'][:];reference=dict(states={});aliases={}
cases=[]
for name,state in [('persistent-stage2-home-before','grocery-home-before'),('persistent-grocery-popover','grocery-popover'),('persistent-grocery-speech-before','grocery-speech'),('persistent-grocery-speech-closed','grocery-speech-declined'),('persistent-grocery-result','grocery-result'),('persistent-grocery-review','grocery-review'),('persistent-grocery-review-fill','grocery-review-fill'),('grocery-return-profile','grocery-profile'),('grocery-home-after','grocery-home-after'),('persistent-grocery-home-popup-after','grocery-guide-coach'),('persistent-grocery-guide-coach-open','grocery-guide')]:
 s=json.loads((E/(name+'.json')).read_text());cases.append((state,name,s))
card_index=0
for name in ['persistent-grocery-batch01','persistent-grocery-batch02','persistent-grocery-batch03']:
 d=json.loads((E/(name+'.json')).read_text());raws={v['index']:v['content'] for v in d['session']['challenges']}
 for row in d['observed']:
  if raws[row['index']]['type']=='speak':card_index+=1;continue
  if not row.get('feedback'):continue
  state=f'grocery-q{card_index}';card_index+=1
  for suffix,key,shot in [('', 'before','screenshot_before'),('-feedback','feedback','screenshot_feedback')]:
   screenshot=row[shot];snapshot=row[key]
   cases.append((state+suffix,Path(screenshot).stem,dict(source_receipt=name+'.json',snapshot=snapshot,text_runs=[dict(text=t) for t in re.findall(r'heading "([^"\n]+)"',snapshot)],actions=[])))
 assert card_index<=11
for state,name,s in cases:
 image=str((E/(name+'.png')).relative_to(ROOT));assert (ROOT/image).exists(),image
 ev=[str((E/(name+'.json')).relative_to(ROOT))] if (E/(name+'.json')).exists() else [str((E/s['source_receipt']).relative_to(ROOT))]
 ev.append(image);texts=list(dict.fromkeys(t['text'] for t in s['text_runs']))
 reference['states'][state]=dict(accessible_text=texts,elements={},capture=dict(path=image,content_rect_points=[0,0,1200,732],window_points=[1200,732],backing_scale=1));aliases[state]={}
 def add(suffix,kind,**kw):c['requirements'].append(dict(id=state+'-'+suffix,state=state,kind=kind,evidence=ev,**kw))
 add('whole','image_pixels',reference_image=image,pixels=[1200,732])
 for i,text in enumerate(texts):add('text-'+str(i),'accessible_text',text=text)
 for i,a in enumerate(s.get('actions',[])):
  key=f'grocery-action-{i}';reference['states'][state]['elements'][key]={k:a[k] for k in ['rect','role','enabled']}
  native={'学习':'nav-learn','现在不做口语题':'speech-decline','点击并开始录音':'speech-record','继续':'speech-continue' if state=='grocery-speech-declined' else 'settlement-continue','回顾本单元':'settlement-secondary','稍后再说':'settlement-continue','打开这个部分的指南':'open-guide','查看排行榜':'view-leaderboards','显示全部':'view-quests'}.get(a['name'])
  if a.get('test','') and 'skill-path-level-0' in a['test']:native='stage2-path-0'
  if native:aliases[state][key]=native
  add(key+'-geometry','element_geometry',element=key,rect=a['rect'],tolerance_points=0)
  if a['role'] is not None:add(key+'-role','element_role',element=key,role=a['role'])
  add(key+'-enabled','element_boolean',element=key,field='enabled',expected=a['enabled'])
 add('audio','pending',description='Aligned source application output remains unavailable; bundled original resource is not acoustic equality')
c.update(revision='english-v65',parent_revision='english-v64',changes=['Fresh stage2 prepared state505gems/1streak, separate from old530gems/2streak','Actual grocery10accepted+oraldecline+11reviewcards+profile+home2of5','Original Bea path animation identity retained; no phase equality claim'])
assert c['requirements'][:len(prior)]==prior
assert len({r['id'] for r in c['requirements']})==len(c['requirements'])
for name,data in [('contract.json',c),('reference.json',reference),('aliases.json',aliases)]:
 (out/name).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(dict(prior=len(prior),requirements=len(c['requirements']),new_states=len(cases))))
