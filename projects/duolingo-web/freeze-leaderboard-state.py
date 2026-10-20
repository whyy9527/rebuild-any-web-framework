"""Freeze observed roleless clear and status selection across source reload/native restart."""
import argparse,json
from pathlib import Path
B=Path(__file__).resolve().parent;ROOT=B.parents[1];E=B/'evidence/english-leaderboard-state-v1'
def build():
 c=json.loads((B/'frontend-english-v50.json').read_text());old=c['requirements'][:];ref=json.loads((B/'evidence/english-home-branches-v1/reference.json').read_text());inventory={'states':{},'journeys':[]}
 names=['selected-hover','cleared','cleared-reload','selected-again','selected-reload']
 for name in names:
  d=json.loads((E/'source'/(name+'.json')).read_text());assert d['viewport']=={'width':1200,'height':732}
  state='status-'+name;image=str((E/'source'/(name+'.png')).relative_to(ROOT));evidence=[str((E/'source'/(name+'.json')).relative_to(ROOT)),image];inventory['states'][state]=d['actions']
  clear=next(a for a in d['actions'] if a['name']=='清除' and a.get('kind')=='pointer_candidate' and a['hit_test']);assert clear['role'] is None
  selected=any(m['rect'][:2]==[1022,159] for m in d['media']);assert selected==name.startswith('selected')
  texts=['青铜等级','设置状态','清除','去学个单元']
  def add(kind,suffix,**kw):c['requirements'].append({'id':state+'-'+suffix,'state':state,'kind':kind,'evidence':evidence,**kw})
  add('image_pixels','whole',reference_image=image,pixels=[1200,732])
  for i,t in enumerate(texts):assert t in d['snapshot'] or any(t in r['text'] for r in d['text_runs']);add('accessible_text','text-'+str(i),text=t)
  add('element_geometry','clear-rect',element='leaderboard-clear',rect=clear['rect'],tolerance_points=0)
  add('element_boolean','clear-enabled',element='leaderboard-clear',field='enabled',expected=True)
  add('interaction_boolean','selection',field='status_selected',expected=selected)
  add('interaction_boolean','clear-visible',field='status_clear_visible',expected=True)
  add('pending','clear-semantic-role',description='Original clear is a roleless pointer span; do not invent browser button semantics from cursor style')
  add('pending','actual-audio',description='Actual original/native application output for this transition not compared')
  ref['states'][state]={'accessible_text':texts,'elements':{'leaderboard-clear':{'rect':clear['rect'],'enabled':True}},'interactions':{'status_selected':selected,'status_clear_visible':True},'capture':{'path':image,'content_rect_points':[0,0,1200,732],'window_points':[1200,732],'backing_scale':1}}
 inventory['journeys']=[{'id':'actual-clear','from':'status-selected-hover','action':next(a['id'] for a in inventory['states']['status-selected-hover'] if a['name']=='清除'),'states':['status-cleared','status-cleared-reload']}]
 nav={'native_action':'nav-leaderboards'};pick={'native_action':'leaderboard-status-0'}
 def hover(name):return {'native_action':'leaderboard-status-0','operation':'hover','state':'status-'+name}
 restart={'native_action':'nav-leaderboards','operation':'restart'}
 scenarios={'journeys':[{'id':'clear-and-reload','steps':[nav,pick,hover('selected-hover'),{'native_action':'leaderboard-clear','state':'status-cleared'},restart,hover('cleared-reload')]},{'id':'selection-and-reload','steps':[nav,pick,hover('selected-again'),restart,hover('selected-reload')]}],'platform_mapping':'Actual source page reload vs actual native owned-child restart, same saved progress/preferences; no remote backend equivalence claim'}
 c.update(revision='english-v51',parent_revision='english-v50',changes=['Actual pointer-only clear, selected/cleared reload behavior; preserve v50'])
 assert c['requirements'][:len(old)]==old
 return c,ref,inventory,scenarios
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out-dir',required=True);out=Path(p.parse_args().out_dir);out.mkdir(parents=True,exist_ok=False)
 for name,value in zip(['contract','reference','inventory','scenarios'],build()):(out/(name+'.json')).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
