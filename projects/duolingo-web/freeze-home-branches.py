"""Freeze actual completed-node and leaderboard transitions, preserving v49."""
import argparse,json
from pathlib import Path
B=Path(__file__).resolve().parent; ROOT=B.parents[1]; E=B/'evidence/english-home-branches-v1'
def build():
 c=json.loads((B/'frontend-english-v49.json').read_text());old=c['requirements'][:]
 ref=json.loads((B/'evidence/english-home-journey-v1/reference.json').read_text());inventory={'states':{},'journeys':[]}
 maps={
 'completed':{'skill-path-state-passed skill-path-unit-test-0':'completed-practice','legendary-node-button':'completed-legendary'},
 'completed-practice':{'create-profile':'path-profile-create','create-profile-later':'path-profile-later'},
 'practice-later':{'skill-path-state-passed skill-path-unit-test-0':'completed-practice','legendary-node-button':'completed-legendary'},
 'legendary':{'legendary-start-button':'legendary-start','quit-button':'legendary-quit'},
 'legendary-profile':{'create-profile':'path-profile-create','create-profile-later':'path-profile-later'},
 'legendary-later':{'skill-path-state-passed skill-path-unit-test-0':'completed-practice','legendary-node-button':'completed-legendary'},
 'legendary-quit':{'skill-path-state-passed skill-path-unit-test-0':'completed-practice','legendary-node-button':'completed-legendary'},
 'leaderboard':{},'leaderboard-status':{},'leaderboard-return':{}}
 texts={k:['提供或接受饮料','完成传奇挑战，展示你的传奇实力','练习 +5 经验','晋升传奇 +40 经验'] for k in ['completed','practice-later','legendary-later','legendary-quit']}
 for k in ['completed-practice','legendary-profile']:texts[k]=['来创建你的个人档案吧！','创建档案就能保存学习进度，随时都可以继续免费学习后续内容。','稍后创建帐户']
 texts['legendary']=['来向我们展示你的传奇实力吧','完成这个超硬核挑战，晋升到传奇等级！','开始 +40 经验','下次再说']
 for k in ['leaderboard','leaderboard-status']:texts[k]=['青铜等级','只要一息尚存，就要坚持到底。来学个单元，挑战本周排行榜！','设置状态','去学个单元','0 经验']
 texts['leaderboard-return']=['提供或接受饮料','第 1 阶段，第 1 部分']
 observations={}
 for name,mapping in maps.items():
  d=json.loads((E/'source'/(name+'.json')).read_text());assert d['viewport']=={'width':1200,'height':732}
  state='branch-'+name;observations[name]=d;inventory['states'][state]=d['actions'];image=str((E/'source'/(name+'.png')).relative_to(ROOT));evidence=[str((E/'source'/(name+'.json')).relative_to(ROOT)),image]
  expected={'accessible_text':texts[name],'elements':{},'capture':{'path':image,'content_rect_points':[0,0,1200,732],'window_points':[1200,732],'backing_scale':1}}
  def add(kind,suffix,**kw):c['requirements'].append({'id':state+'-'+suffix,'state':state,'kind':kind,'evidence':evidence,**kw})
  add('image_pixels','whole',reference_image=image,pixels=[1200,732])
  for i,text in enumerate(texts[name]):
   assert text in d['snapshot'] or any(text in r['text'] for r in d['text_runs']),(name,text)
   add('accessible_text','text-'+str(i),text=text)
  candidates=[v for v in d['actions'] if v['hit_test']]
  if name.startswith('leaderboard') and name!='leaderboard-return':
   a=next(v for v in candidates if v['name']=='去学个单元');mapping={**mapping,a['id']:'leaderboard-practice'}
   # This first status icon was actually clicked, not all other controls.
   a=next(v for v in candidates if v['rect']==[830,279,48,48]);mapping={**mapping,a['id']:'leaderboard-status-0'}
  for source_id,native_id in mapping.items():
   a=next(v for v in candidates if v['test']==source_id or v['id']==source_id)
   expected['elements'][native_id]={'role':a['role'],'rect':a['rect'],'enabled':a['enabled']}
   add('element_role',native_id+'-role',element=native_id,role=a['role']);add('element_geometry',native_id+'-rect',element=native_id,rect=a['rect'],tolerance_points=0);add('element_boolean',native_id+'-enabled',element=native_id,field='enabled',expected=a['enabled'])
  flags={'profile_present':name in ['completed-practice','legendary-profile'],'legendary_present':name=='legendary','completed_popover_present':name in ['completed','practice-later','legendary-later','legendary-quit'],'status_selected':name=='leaderboard-status'}
  # Covered dialogs do not imply absence underneath; compare only actionable layer flags.
  expected['interactions']=flags
  for key,value in flags.items():add('interaction_boolean',key,field=key,expected=value)
  add('pending','actual-audio',description='Original/native acoustic outputs for this transition not compared')
  ref['states'][state]=expected
 sequence=[('start-lesson','completed'),('completed-practice','completed-practice'),('path-profile-later','practice-later'),('completed-legendary','legendary'),('legendary-start','legendary-profile'),('path-profile-later','legendary-later'),('completed-legendary',None),('legendary-quit','legendary-quit')]
 scenarios={'journeys':[{'id':'completed-branches','steps':[{'native_action':a,**({'state':'branch-'+s} if s else {})} for a,s in sequence]},{'id':'leaderboard','steps':[{'native_action':'nav-leaderboards','state':'branch-leaderboard'},{'native_action':'leaderboard-status-0','state':'branch-leaderboard-status'},{'native_action':'nav-learn','state':'branch-leaderboard-return'}]}]}
 # Map actual state-scoped controls to observed successor states, rather than inventing coverage from the assertions.
 edges=[('completed','练习 +5 经验','completed-practice'),('completed-practice','稍后创建帐户','practice-later'),('practice-later','晋升传奇 +40 经验','legendary'),('legendary','开始 +40 经验','legendary-profile'),('legendary-profile','稍后创建帐户','legendary-later'),('legendary-later','晋升传奇 +40 经验','legendary'),('legendary','下次再说','legendary-quit'),('leaderboard-status','学习','leaderboard-return')]
 for i,(start,action,end) in enumerate(edges):
  a=next(v for v in observations[start]['actions'] if v['name']==action and v['hit_test']);inventory['journeys'].append({'id':'transition-'+str(i),'from':'branch-'+start,'action':a['id'],'states':['branch-'+end]})
 a=next(v for v in observations['leaderboard']['actions'] if v['rect']==[830,279,48,48]);inventory['journeys'].append({'id':'select-status','from':'branch-leaderboard','action':a['id'],'states':['branch-leaderboard-status']})
 c.update(revision='english-v50',parent_revision='english-v49',changes=['Actual completed-node practice/Legendary guest transitions and leaderboard destination/status/return; preserve v49'])
 assert c['requirements'][:len(old)]==old
 return c,ref,inventory,scenarios
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out-dir',required=True);out=Path(p.parse_args().out_dir);out.mkdir(parents=True,exist_ok=False)
 for name,value in zip(['contract','reference','inventory','scenarios'],build()):(out/(name+'.json')).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
