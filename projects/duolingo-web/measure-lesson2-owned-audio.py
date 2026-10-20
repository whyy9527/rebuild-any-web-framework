"""Measure two actual UI-triggered lesson2 speech outputs, not source acoustics."""
import argparse,hashlib,importlib.util,json,tempfile
from pathlib import Path
B=Path(__file__).resolve().parent;R=B.parent/'education-swift/Sources/LingoSeed/Resources/Reference'
spec=importlib.util.spec_from_file_location('audio',B/'compare-feedback-audio.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
p=argparse.ArgumentParser();p.add_argument('--native',required=True);p.add_argument('--out',required=True);a=p.parse_args();n=Path(a.native);out=Path(a.out);assert not out.exists()
q=json.loads((R/'unit12-home-2.json').read_text())['data']['candidate_course']['lessons'][0]['questions'];rows=[]
for name,resource,action in [('lesson2-select-living-room',q[0]['options'][0]['audioResource'],'option-0'),('lesson2-assist-feedback',q[1]['options'][0]['audioResource'],'check')]:
 receipt=json.loads((n/(name+'.wav.json')).read_text());assert not receipt.get('failure') and receipt['microphone'] is False and receipt['samples']>0 and [v['id'] for v in receipt['ui_actions']]==[action]
 with tempfile.TemporaryDirectory() as tmp:
  ref=m.decode(R/resource,Path(tmp));actual=m.decode(n/(name+'.wav'),Path(tmp));metrics=m.measure(ref,actual);assert abs(m.measure(ref,ref)['normalized_correlation']-1)<1e-8
 rows.append(dict(recording=name,resource=resource,resource_sha256=hashlib.sha256((R/resource).read_bytes()).hexdigest(),recording_sha256=hashlib.sha256((n/(name+'.wav')).read_bytes()).hexdigest(),metrics=metrics,owned_capture=receipt))
out.write_text(json.dumps(dict(scope='Original resource presence in owned Swift output after real selection/grading; source acoustic equality remains unverified',recordings=rows,limitations=['No source acoustic output recorded','No completion-effect or every-question sound equivalence inferred','Missed original media event windows remain unknown; no substitute effect added']),ensure_ascii=False,indent=2)+'\n')
print(json.dumps([(r['recording'],r['metrics']['normalized_correlation'],r['metrics']['fitted_gain']) for r in rows]))
