"""Check repaired source radio geometry/roles and visible skip; retain other failures."""
import argparse,hashlib,json
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--report',required=True);p.add_argument('--before',required=True);p.add_argument('--out',required=True);a=p.parse_args()
report=Path(a.report);before=Path(a.before);rows=json.loads(report.read_text())['rows'];old={r['id']:r for r in json.loads(before.read_text())['rows']};byid={r['id']:r for r in rows};required=[]
for q in [1,4]:
 for phase in ['before','feedback']:
  for index in [1,2,3]:
   for field in ['geometry','role']:required.append(f'unit12-lesson2-q{q}-{phase}-{field}-{index}')
 for field in ['geometry','role','enabled']:required.append(f'unit12-lesson2-q{q}-before-{field}-4')
assert all(byid[k]['status']=='pass' for k in required),[(k,byid[k]['status'])for k in required if byid[k]['status']!='pass']
changed=[dict(id=k,before=old[k]['status'],after=byid[k]['status'])for k in required]
Path(a.out).write_text(json.dumps(dict(status='pass',checks=len(required),report_sha256=hashlib.sha256(report.read_bytes()).hexdigest(),before_sha256=hashlib.sha256(before.read_bytes()).hexdigest(),changes=changed,limitations=['Only these ordinary assist radio geometry/roles and skip controls are asserted','Strict full image, CSS/text metrics, other layout, reminder and unvisited course states remain separately failing or unverified','Not a mechanism ablation']),ensure_ascii=False,indent=2)+'\n')
print(json.dumps(dict(status='pass',checks=len(required))))
