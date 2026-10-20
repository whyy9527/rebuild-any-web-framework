"""Append actual sequential practice-instance text, geometry and whole-image requirements."""
import argparse,json
from pathlib import Path
B=Path(__file__).resolve().parent;R=B.parents[1];E=B/'evidence/english-leaderboard-practice-instance-v1';S=E/'source'
def build():
 c=json.loads((B/'frontend-english-v52.json').read_text());parent=c['requirements'][:];ref=json.loads((B/'evidence/english-leaderboard-state-v1/practice-reference.json').read_text());records=[]
 for n in ['walk','after-speech']:
  d=json.loads((S/(n+'.json')).read_text());records.extend((r['content'],o) for r,o in zip(d['session']['challenges'],d['observed']))
 assert len(records)==17
 def state(key,image,texts,evidence,elements=None):
  elements=elements or {};assert Path(R/image).exists(),image
  d={'accessible_text':list(dict.fromkeys(texts)),'elements':elements,'capture':{'path':image,'content_rect_points':[0,0,1200,732],'window_points':[1200,732],'backing_scale':1}};ref['states'][key]=d
  def add(suffix,kind,**kw):c['requirements'].append(dict(id=key+'-'+suffix,state=key,kind=kind,evidence=evidence,**kw))
  add('whole','image_pixels',reference_image=image,pixels=[1200,732])
  for i,t in enumerate(d['accessible_text']):add('text-'+str(i),'accessible_text',text=t)
  for name,e in elements.items():
   add(name+'-geometry','element_geometry',element=name,rect=e['rect'],tolerance_points=0);add(name+'-role','element_role',element=name,role=e['role']);add(name+'-enabled','element_boolean',element=name,field='enabled',expected=e['enabled'])
  add('actual-audio','pending',description='Original/native actual acoustic equality unverified; only three match cues observed, fourth unknown')
 for i,(raw,row) in enumerate(records):
  ev=[str((S/('walk.json' if i<8 else 'after-speech.json')).relative_to(R))];key='leaderboard-review-q'+str(i)
  if raw['type']=='speak':continue
  texts=[row['heading']];elements={}
  if raw['type']=='listenMatch':
   texts+= [str(j+5)+' '+t for j,t in enumerate(row['right_text'])]
   for j in range(4):
    for side in ['left','right']:
     rect=row[side+'_rects'][j]
     identity=j if side=='left' else next(p['left_index'] for p in row['pair_audio_order'] if p['translation']==row['right_text'][j])
     elements['pair-'+side+'-'+str(identity)]={'rect':[rect[k] for k in ['x','y','width','height']],'role':'button','enabled':True}
  elif raw.get('prompt') and raw['type'] in ['translate','assist']:texts.append(raw['prompt'])
  state(key,row['screenshot_before'],texts,ev,elements)
  import re
  feedback=re.search(r'heading "([^"\n]+)" \[level=2\]',row['feedback']).group(1)
  state(key+'-feedback',row['screenshot_feedback'],[feedback],ev)
 for stem,key,texts in [('speech-before','leaderboard-review-speech',['朗读下面的句子']),('speech-declined','leaderboard-review-speech-declined',['麦克风已关闭','将在 15 分钟后恢复']),('result','leaderboard-review-result',['完美！','你练习全对，无错完成本单元','回顾本单元','重新练习']),('review','leaderboard-review-practice-review-open',['查看你的成绩单！','点击下面的小方块来浏览答案吧！'])]:
  p=S/(stem+'.json');d=json.loads(p.read_text());assert all(t in d['snapshot'] or any(t in x['text'] for x in d['text_runs']) for t in texts)
  elements={}
  if stem=='review':
   cards=[x for x in d['visible'] if x['tag']=='DIV' and x['role']=='button'];assert len(cards)==17
   elements={'review-card-'+str(i):{k:x[k] for k in ['rect','role','enabled']} for i,x in enumerate(cards)}
  state(key,str((S/(stem+'.png')).relative_to(R)),texts,[str(p.relative_to(R))],elements)
 c.update(revision='english-v53',parent_revision='english-v52',changes=['Actual new sequential leaderboard instance,16 scored plus one declined speech and17review cards; no adaptive selection claim'])
 assert c['requirements'][:len(parent)]==parent and len({r['id'] for r in c['requirements']})==len(c['requirements'])
 return c,ref
def with_listening_controls(c,ref):
 old=c['requirements'][:];rows=[]
 for n in ['walk','after-speech']:
  d=json.loads((S/(n+'.json')).read_text());rows.extend((n,r) for r in d['observed'])
 for i,(n,r) in enumerate(rows):
  if '现在不做听力题' in r['before']:
   key='leaderboard-review-q'+str(i)
   c['requirements'].append(dict(id=key+'-listening-decline-label',state=key,kind='accessible_text',text='现在不做听力题',evidence=[str((S/(n+'.json')).relative_to(R))]))
   ref['states'][key]['accessible_text'].append('现在不做听力题')
 c.update(revision='english-v54',parent_revision='english-v53',changes=['Screenshot inspection exposes missing listening-decline control in compiled current instance; append actual six visible labels without relaxing image checks'])
 assert len(c['requirements'])==3084 and c['requirements'][:len(old)]==old
 return c,ref
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out-dir',required=True);p.add_argument('--with-listening-controls',action='store_true');a=p.parse_args();out=Path(a.out_dir);out.mkdir(parents=True,exist_ok=False)
 values=build()
 if a.with_listening_controls:values=with_listening_controls(*values)
 for n,v in zip(['contract.json','reference.json'],values):(out/n).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
