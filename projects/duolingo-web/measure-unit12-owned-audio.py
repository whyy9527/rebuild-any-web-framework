"""Compare original files with actual owned-app recordings; do not claim source acoustic equality."""
import argparse,importlib.util,json,tempfile,hashlib
from pathlib import Path
B=Path(__file__).resolve().parent;R=B.parent/'education-swift/Sources/LingoSeed/Resources/Reference'
spec=importlib.util.spec_from_file_location('audio',B/'compare-feedback-audio.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
p=argparse.ArgumentParser();p.add_argument('--native',required=True);p.add_argument('--out',required=True);a=p.parse_args();n=Path(a.native);out=Path(a.out);assert not out.exists()
l=json.loads((R/'unit12-home-1.json').read_text())['data']['candidate_course']['lessons'][0];guide=json.loads((R/'unit12-guide.json').read_text())
rows=[]
for record,resource,gain in [('unit12-guide-welcome',guide['phrases'][0]['audioResource'],1),('unit12-first-feedback',l['questions'][0]['correctFeedbackAudioResource'],.35),('unit12-completion',l['completionAudioResource'],.5)]:
 receipt=json.loads((n/(record+'.wav.json')).read_text());assert not receipt.get('failure') and receipt['microphone'] is False and len(receipt['ui_actions'])==1 and receipt['samples']>0
 with tempfile.TemporaryDirectory() as d:
  ref=m.decode(R/resource,Path(d));actual=m.decode(n/(record+'.wav'),Path(d));metrics=m.measure(ref,actual);check=m.measure(ref,ref)
  assert abs(check['normalized_correlation']-1)<1e-8
 rows.append(dict(recording=record,resource=resource,resource_sha256=hashlib.sha256((R/resource).read_bytes()).hexdigest(),recording_sha256=hashlib.sha256((n/(record+'.wav')).read_bytes()).hexdigest(),source_invocation_gain=gain,metrics=metrics,owned_capture=receipt))
result=dict(scope='Actual UI-triggered owned Swift output vs original public resources; source invocation gain is not source acoustic output',recordings=rows,limitations=['No acoustic equality claim: source mixer, latency, motion and other cues remain unverified','Only six source feedback windows contained the original effect; missed events remain unknown'])
out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps([(r['recording'],r['metrics']['normalized_correlation'],r['metrics']['fitted_gain']) for r in rows]))
