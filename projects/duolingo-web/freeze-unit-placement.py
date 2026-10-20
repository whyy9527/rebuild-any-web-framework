"""Append source unit12 frontend evidence, preserving all v67 requirements."""
import argparse,json,re
from pathlib import Path
B=Path('projects/duolingo-web');E=B/'evidence/english-unit-placement-v1';S=E/'source'
p=argparse.ArgumentParser();p.add_argument('--out-dir',required=True);out=Path(p.parse_args().out_dir);out.mkdir(parents=True,exist_ok=False)
c=json.loads((B/'frontend-english-v67.json').read_text());prior=len(c['requirements']);ref={'states':{}};aliases={}
names=['unit12-intro','unit12-first-question','unit12-gap-first','unit12-exit-confirm','unit12-result-stable','unit12-after-result','unit12-after-score','unit12-after-unlock','unit12-home-uncovered','unit12-review']
nav={'home-nav':'nav-learn','characters-nav':'nav-pronunciation','leaderboard-nav':'nav-leaderboards','quests-nav':'nav-quests','shop-nav':'nav-shop','profile-tab':'nav-profile','create-profile-juicy':'view-profile','sign-in-juicy':'sign-in','leaderboards-open':'view-leaderboards'}
for name in names:
 state='unit12-q0-before' if name=='unit12-first-question' else name
 path=S/(name+'.json');d=json.loads(path.read_text());assert d['viewport']=={'width':1200,'height':732}
 texts=list(dict.fromkeys(t['text'] for t in d['text_runs'] if not re.fullmatch(r'[A-Za-z.,!?]|\d+|%',t['text'])))
 texts+=list(dict.fromkeys(t['text'] for t in d.get('rendered_text_groups',[])))
 # Counters are clipped CSS animations: DOM includes hidden0..9. Screenshot
 # independently proves50XP/100%; never turn every DOM digit into visible text.
 if name=='unit12-result-stable':texts += ['50','100%']
 image=str(path.with_suffix('.png'));ev=[str(path),image];aliases[state]={}
 ref['states'][state]={'accessible_text':texts,'elements':{},'capture':{'path':image,'content_rect_points':[0,0,1200,732],'window_points':[1200,732],'backing_scale':1}}
 def add(suffix,kind,**kw):c['requirements'].append(dict(id=state+'-'+suffix,state=state,kind=kind,evidence=ev,**kw))
 add('whole','image_pixels',reference_image=image,pixels=[1200,732])
 for i,text in enumerate(texts):add('text-'+str(i),'accessible_text',text=text)
 for i,a in enumerate(d['actions']):
  key=state+'-action-'+str(i);target=nav.get(a['test']);label=a['name'].strip();test=a['test']
  if test=='quit-button':target='exit'
  if test=='challenge-choice':target='option-option-'+str(sum(x['test']=='challenge-choice' for x in d['actions'][:i]))
  if name=='unit12-intro':target='unit-placement-later' if label=='下次再说' else 'unit-placement-start'
  elif label=='继续努力':target='practice-quit-cancel'
  elif label=='退出':target='practice-quit-confirm'
  elif label=='回顾本单元':target='settlement-secondary'
  elif label=='稍后再说':target='settlement-continue'
  elif test=='player-next' and label=='检查':target='check'
  elif label=='继续':target='settlement-continue'
  elif label=='显示全部' and a.get('href')=='/quests':target='view-quests'
  if target:
   aliases[state][key]=target
   ref['states'][state]['elements'][key]={'rect':a['rect'],'role':a['role'],'enabled':a['enabled']}
   for suffix,kind,kw in [('geometry','element_geometry',{'rect':a['rect'],'tolerance_points':0}),('role','element_role',{'role':a['role']}),('enabled','element_boolean',{'field':'enabled','expected':a['enabled']})]:add(key+'-'+suffix,kind,element=key,**kw)
  else:add(key+'-interaction','pending',description='Original observed entry awaits actual native behavior verification')
 add('audio','pending',description='Original acoustic output equality and per-state native output remain to verify')
 if name in ['unit12-result-stable','unit12-after-result']:add('animation','pending',description='Captured original frame/canvas does not verify native animation identity, phase or triggers')
# Every accepted source question has original before/feedback screenshots. Add
# all of them, rather than letting a representative gapFill stand for18 questions.
qindex=0
for filename in ['unit12-batch02.json','unit12-batch04.json','unit12-batch05.json']:
 d=json.loads((S/filename).read_text())
 for row in d['observed']:
  for phase,key in [('before','screenshot_before'),('feedback','screenshot_feedback')]:
   state='unit12-q'+str(qindex)+'-'+phase
   if state in ref['states']:continue
   path=S/row[key];assert path.is_file()
   ev=[str(S/filename),str(path)]
   texts=[row['heading']]
   if phase=='feedback':
    found=re.search(r'heading "([^"\n]+)" \[level=2\]',row['feedback']);assert found;texts.append(found.group(1))
   ref['states'][state]={'accessible_text':texts,'elements':{},'capture':{'path':str(path),'content_rect_points':[0,0,1200,732],'window_points':[1200,732],'backing_scale':1}}
   add('whole','image_pixels',reference_image=str(path),pixels=[1200,732])
   for i,text in enumerate(texts):add('text-'+str(i),'accessible_text',text=text)
   add('audio','pending',description='Source media URLs and native playback are separate from actual acoustic equivalence')
  qindex += 1
assert qindex==18
interlude_index=0
for filename in ['unit12-batch02.json','unit12-batch04.json','unit12-batch05.json']:
 for row in json.loads((S/filename).read_text())['interludes']:
  state='unit12-interlude-'+str(interlude_index);image=S/row['screenshot'];assert image.is_file()
  ev=[str(S/filename),str(image)];text=row['facts']['encouragement_messages'][0]
  ref['states'][state]={'accessible_text':[text],'elements':{},'capture':{'path':str(image),'content_rect_points':[0,0,1200,732],'window_points':[1200,732],'backing_scale':1}}
  add('whole','image_pixels',reference_image=str(image),pixels=[1200,732]);add('text','accessible_text',text=text)
  add('animation','pending',description='Original interlude animation and native artwork identity still to verify')
  interlude_index+=1
assert interlude_index==4

c.update(revision='english-v68',parent_revision='english-v67',changes=['Actual unit12 five-heart independent test, gapFill, roleless quit overlay,50XP/100%,unpromoted score10,unit2 unlock and changed home','Original hidden rolling digits excluded from visible-text interpretation; screenshots retained'])
assert c['requirements'][:prior]==json.loads((B/'frontend-english-v67.json').read_text())['requirements']
for name,d in [('contract.json',c),('reference.json',ref),('aliases.json',aliases)]: (out/name).write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'prior':prior,'requirements':len(c['requirements']),'states':len(ref['states'])}))
