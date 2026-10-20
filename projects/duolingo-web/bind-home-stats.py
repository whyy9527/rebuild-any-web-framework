"""Bind actual owned AX menus; panel presence derives only from collected text."""
import argparse,json,hashlib
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--native',required=True);p.add_argument('--keyboard',required=True);p.add_argument('--aliases',required=True);p.add_argument('--out',required=True);a=p.parse_args()
files=[Path(a.native),Path(a.keyboard)];data=[json.loads(f.read_text()) for f in files];assert data[0]['candidate_binary_sha256']==data[1]['candidate_binary_sha256'];assert all(d['failure'] is None for d in data)
out=Path(a.out);assert not out.exists();d=data[0];assert not set(d['states'])&set(data[1]['states']);d['states'].update(data[1]['states']);aliases=json.loads(Path(a.aliases).read_text());bound=0
for name,state in d['states'].items():
 texts=state['accessible_text'];assert isinstance(texts,list) and all(isinstance(t,str) for t in texts)
 state.setdefault('interactions',{}).update({'stat_'+menu+'_menu_present':label in texts for menu,label in [('course','我的课程'),('gems','宝石'),('streak','连胜精英俱乐部'),('hearts','红心')]})
 for source,native in aliases.get(name,{}).items():
  if native in state['elements']:
   state['elements'][source]=dict(state['elements'][native],native_identifier=native);bound+=1
 d['derived_from']=[dict(path=str(f),sha256=hashlib.sha256(f.read_bytes()).hexdigest()) for f in files]
out.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n');print(json.dumps(dict(states=len(d['states']),bound=bound,binary=d['candidate_binary_sha256'])))
