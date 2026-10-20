"""Check actual native Rive input readbacks against source UI/config, not screenshots."""
import argparse
import hashlib
import json
from pathlib import Path

BASE=Path(__file__).resolve().parent
E=BASE/'evidence/english-avatar-categories-v1'
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--native',required=True);p.add_argument('--out',required=True)
a=p.parse_args();native=Path(a.native)
initial=json.loads((E/'observed-initial-state.json').read_text())
records=[json.loads(line.removeprefix('avatar-runtime-inputs ')) for line in (native/'child.log').read_text().splitlines() if line.startswith('avatar-runtime-inputs ')]
assert records,'No runtime readbacks; do not infer success from source code'
checks=[]
for value in range(1,16):
    rows=[r for r in records if r.get('SkinTone')==value]
    expected=initial|{'SkinTone':value,'ENG_ONLY_Zoom':3}
    checks.append({'skin_input':value,'runtime_rows':len(rows),'pass':bool(rows) and all(all(r.get(k)==v for k,v in expected.items()) for r in rows)})
provenance=json.loads((E/'renderer-provenance.json').read_text())
asset=BASE.parents[1]/'projects/education-swift/Sources/LingoSeed/Resources/Reference/en-avatar-builder.riv'
checks.append({'original_asset_bytes':hashlib.sha256(asset.read_bytes()).hexdigest()==provenance['sha256'],'pass':hashlib.sha256(asset.read_bytes()).hexdigest()==provenance['sha256']})
result={'kind':'actual native Rive number readbacks','runtime_records':len(records),'checks':checks,'pass':all(r['pass'] for r in checks),'limits':['Readbacks establish input availability/application, not pixel or acoustic equality','Logs are not individually timestamp-aligned to screenshots; actual15radio actions are separately verified','No native category/composition/SMButtons interaction claim','Autoplay asset/input integration is not a temporal animation comparison']}
with Path(a.out).open('x') as f:json.dump(result,f,ensure_ascii=False,indent=2);f.write('\n')
print(json.dumps({'pass':sum(r['pass'] for r in checks),'fail':sum(not r['pass'] for r in checks),'runtime_records':len(records)}))
raise SystemExit(0 if result['pass'] else 1)
