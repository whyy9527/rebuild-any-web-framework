"""Bind explicit platform aliases to already-measured facts, without inventing values."""
import argparse,json,hashlib
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--observed',required=True);p.add_argument('--aliases',required=True);p.add_argument('--out',required=True);a=p.parse_args()
source=Path(a.observed);manifest=Path(a.aliases);out=Path(a.out);assert not out.exists()
d=json.loads(source.read_text());aliases=json.loads(manifest.read_text());bound=[];unresolved=[]
for state,mapping in aliases.items():
 if state not in d['states']:continue
 elements=d['states'][state]['elements']
 for key,native in mapping.items():
  if native not in elements:unresolved.append(dict(state=state,element=key,native=native));continue
  elements[key]=dict(elements[native],native_identifier=native);bound.append(dict(state=state,element=key,native=native))
d['alias_binding']=dict(source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),manifest_sha256=hashlib.sha256(manifest.read_bytes()).hexdigest(),bound=bound,unresolved=unresolved,scope='Only names are bound; raw roles, values, rects and capture paths remain measured facts')
out.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n');print(json.dumps(dict(bound=len(bound),unresolved=len(unresolved))))
