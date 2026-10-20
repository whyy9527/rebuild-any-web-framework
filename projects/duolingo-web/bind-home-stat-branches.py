"""Bind actual same-binary UI facts, including newly implemented heart controls."""
import argparse,json,hashlib
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--native',required=True);p.add_argument('--aliases',required=True);p.add_argument('--out',required=True);a=p.parse_args()
B=Path('projects/duolingo-web');d=json.loads(Path(a.native).read_text());assert d['failure'] is None
names={'hearts-refilled':'stat-branches-refill','hearts-full':'stat-branches-full','hearts-super-signup':'stat-branches-super','hearts-super-login':'stat-branches-super-login','hearts-course-keyboard':'stat-branches-course-menu','hearts-restarted':'stat-branches-restarted','hearts-before':'stats-home-root'}
for old,new in names.items():assert new not in d['states'];d['states'][new]=d['states'].pop(old)
aliases=json.loads(Path(a.aliases).read_text());aliases.update(json.loads((B/'evidence/english-home-stats-v1/aliases.json').read_text()))
s=json.loads((B/'evidence/english-home-stats-v1/source/hearts-calibrated.json').read_text())
for i,x in enumerate(s['actions']):
 k={'无限红心':'stat-hearts-super','补心':'stat-hearts-refill','做练习获取红心':'stat-hearts-practice'}.get(x['name'].split('\n')[0])
 if k:aliases['stats-hearts']['stats-hearts-action-'+str(i)]=k
bound=0
for name,state in d['states'].items():
 texts=state['accessible_text'];assert isinstance(texts,list)
 state.setdefault('interactions',{}).update({'stat_'+m+'_menu_present':label in texts for m,label in [('course','我的课程'),('gems','宝石'),('streak','连胜精英俱乐部'),('hearts','红心')]})
 for key,native in aliases.get(name,{}).items():
  if native in state['elements']:state['elements'][key]=dict(state['elements'][native],native_identifier=native);bound+=1
out=Path(a.out);assert not out.exists();d['derived_from']={'path':a.native,'sha256':hashlib.sha256(Path(a.native).read_bytes()).hexdigest()};d['binding']='Actual AX aliases and state names; no pass flags';out.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n');print(json.dumps(dict(bound=bound,states=len(d['states']))))
