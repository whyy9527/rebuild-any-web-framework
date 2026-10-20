"""Preserve v66 and append actual same-viewport guide and newly reached home branches."""
import argparse,json,re
from pathlib import Path
B=Path('projects/duolingo-web');E=B/'evidence/english-home-scroll-v1';S=E/'source'
p=argparse.ArgumentParser();p.add_argument('--out-dir',required=True);out=Path(p.parse_args().out_dir);out.mkdir(parents=True,exist_ok=False)
c=json.loads((B/'frontend-english-v66.json').read_text());prior=len(c['requirements']);ref={'states':{}};aliases={}
known={'home-nav':'nav-learn','characters-nav':'nav-pronunciation','leaderboard-nav':'nav-leaderboards','quests-nav':'nav-quests','shop-nav':'nav-shop','profile-tab':'nav-profile','leaderboards-open':'view-leaderboards','create-profile-juicy':'view-profile','sign-in-juicy':'sign-in'}
for state in ['home-scroll-guide-top','home-scroll-guide-top-stable','home-scroll-guide-bottom','home-scroll-radio-after','home-scroll-unit-jump']:
 path=S/(state+'.json');s=json.loads(path.read_text());assert s['viewport']=={'width':1200,'height':732}
 texts=list(dict.fromkeys(t['text'] for t in s['text_runs'] if not re.fullmatch('[A-Za-z.,!?]',t['text'])))
 texts+=list(dict.fromkeys(v['text'] for v in s.get('rendered_text_groups',[])))
 image=str(path.with_suffix('.png'));ev=[str(path),image]
 ref['states'][state]={'accessible_text':texts,'elements':{},'capture':{'path':image,'content_rect_points':[0,0,1200,732],'window_points':[1200,732],'backing_scale':1}}
 aliases[state]={}
 def add(suffix,kind,**kw):c['requirements'].append(dict(id=state+'-'+suffix,state=state,kind=kind,evidence=ev,**kw))
 add('whole','image_pixels',reference_image=image,pixels=[1200,732])
 for i,text in enumerate(texts):add('text-'+str(i),'accessible_text',text=text)
 for i,a in enumerate(s['actions']):
  key=state+'-action-'+str(i);ref['states'][state]['elements'][key]={'rect':a['rect'],'role':a.get('role'),'enabled':a['enabled']}
  target=known.get(a.get('test'))
  if a.get('href')=='/quests' and a.get('name')=='显示全部':target='view-quests'
  if a.get('name')=='返回':target='close-guide'
  if a.get('test')=='skill-path-level-0 skill-path-level-skill':target='stage2-path-0'
  if a['id'].startswith('BUTTON:#') and 'guide-' in state:target='guide-speech-'+a['id'].split('#')[-1]
  if target:
   aliases[state][key]=target
   for suffix,kind,kw in [('geometry','element_geometry',{'rect':a['rect'],'tolerance_points':0}),('role','element_role',{'role':a.get('role') or ('link' if a['tag']=='A' else 'button')}),('enabled','element_boolean',{'field':'enabled','expected':a['enabled']})]:add(key+'-'+suffix,kind,element=key,**kw)
  else:add(key+'-interaction','pending',description='Actual source entry retained; native action outcome not implemented/verified')
 add('audio','pending',description='Source browser acoustic equality remains unavailable')
c.update(revision='english-v67',parent_revision='english-v66',changes=['Actual shared sticky scroll, new locked radio and independent unit placement intro','Fresh four-heart source fixture remains distinct from five-heart v66'])
assert c['requirements'][:prior]==json.loads((B/'frontend-english-v66.json').read_text())['requirements']
for name,d in [('contract.json',c),('reference.json',ref),('aliases.json',aliases)]:(out/name).write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'prior':prior,'requirements':len(c['requirements']),'states':len(ref['states'])}))
