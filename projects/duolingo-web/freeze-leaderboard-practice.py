"""Freeze actual leaderboard practice initial question and exit, without inventing later questions."""
import argparse,json
from pathlib import Path
B=Path(__file__).resolve().parent;ROOT=B.parents[1];E=B/'evidence/english-leaderboard-state-v1'
def build():
 c=json.loads((B/'frontend-english-v51.json').read_text());old=c['requirements'][:];ref=json.loads((E/'reference.json').read_text());inventory={'states':{},'journeys':[]}
 for name in ['practice-entry','practice-return']:
  d=json.loads((E/'source'/(name+'.json')).read_text());assert d['viewport']=={'width':1200,'height':732};state='leaderboard-'+name;inventory['states'][state]=d['actions'];image=str((E/'source'/(name+'.png')).relative_to(ROOT));ev=[str((E/'source'/(name+'.json')).relative_to(ROOT)),image]
  texts=['选择配对','5 欢迎','6 热','7 茶','8 咖啡','现在不做听力题','检查'] if name=='practice-entry' else ['提供或接受饮料','第 1 阶段，第 1 部分']
  expected={'accessible_text':texts,'elements':{},'capture':{'path':image,'content_rect_points':[0,0,1200,732],'window_points':[1200,732],'backing_scale':1}}
  def add(kind,suffix,**kw):c['requirements'].append({'id':state+'-'+suffix,'state':state,'kind':kind,'evidence':ev,**kw})
  add('image_pixels','whole',reference_image=image,pixels=[1200,732])
  for i,t in enumerate(texts):assert t in d['snapshot'] or any(t in r['text'] for r in d['text_runs']);add('accessible_text','text-'+str(i),text=t)
  if name=='practice-entry':
   actions=d['actions'];mapping={'exit':next(a for a in actions if a['test']=='quit-button'),'listening-decline':next(a for a in actions if a['test']=='player-skip'),'check':next(a for a in actions if a['test']=='player-next')}
   for i in range(4):
    mapping['pair-left-'+str(i)]=next(a for a in actions if a['name']==str(i+1));mapping['pair-right-'+str(i)]=next(a for a in actions if a['name'].startswith(str(i+5)+'\n'))
   for key,a in mapping.items():
    expected['elements'][key]={'role':a['role'],'rect':a['rect'],'enabled':a['enabled']}
    add('element_role',key+'-role',element=key,role=a['role']);add('element_geometry',key+'-rect',element=key,rect=a['rect'],tolerance_points=0);add('element_boolean',key+'-enabled',element=key,field='enabled',expected=a['enabled'])
  flags={'practice_present':name=='practice-entry','learn_present':name=='practice-return','exit_confirmation_present':False};expected['interactions']=flags
  for key,value in flags.items():add('interaction_boolean',key,field=key,expected=value)
  add('pending','current-session-data',description='Only initial current question and exit observed; full current session content/voice not frozen, historical default variant is not proof of equality')
  add('pending','actual-audio',description='Actual original/native acoustic outputs not compared')
  ref['states'][state]=expected
 action=next(a['id'] for a in inventory['states']['leaderboard-practice-entry'] if a['test']=='quit-button');inventory['journeys']=[{'id':'initial-unanswered-exit','from':'leaderboard-practice-entry','action':action,'states':['leaderboard-practice-return']}]
 scenarios={'journeys':[{'id':'leaderboard-practice','steps':[{'native_action':'nav-leaderboards'},{'native_action':'leaderboard-practice','state':'leaderboard-practice-entry'},{'native_action':'exit','state':'leaderboard-practice-return'}]}],'limits':'Only initial unanswered exit; no rule inferred for later answered states'}
 c.update(revision='english-v52',parent_revision='english-v51',changes=['Actual leaderboard current practice question/exit exposes historical default content mismatch; preserve all v51 requirements'])
 assert c['requirements'][:len(old)]==old
 return c,ref,inventory,scenarios
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out-dir',required=True);out=Path(p.parse_args().out_dir);out.mkdir(parents=True,exist_ok=False)
 for name,value in zip(['contract','reference','inventory','scenarios'],build()):(out/(name+'.json')).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
