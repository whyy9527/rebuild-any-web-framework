"""Fit an original public resource to one actual owned-app UI recording.

Reports presence, gain and delay; never declares source acoustic equivalence.
"""
import argparse,hashlib,importlib.util,json,tempfile
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--reference',required=True);p.add_argument('--recording',required=True);p.add_argument('--out',required=True);a=p.parse_args()
reference,recording,out=Path(a.reference),Path(a.recording),Path(a.out);assert not out.exists()
receipt=json.loads(recording.with_suffix('.wav.json').read_text())
assert receipt['microphone'] is False and len(receipt['ui_actions'])==1 and receipt['samples']>0 and not receipt.get('failure')
spec=importlib.util.spec_from_file_location('measure',Path(__file__).with_name('compare-feedback-audio.py'));m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
with tempfile.TemporaryDirectory() as folder:
 ref=m.decode(reference,Path(folder));actual=m.decode(recording,Path(folder));result=m.measure(ref,actual)
d=dict(scope='Original resource presence in actual owned-app output triggered inside recording',reference=dict(path=str(reference),sha256=hashlib.sha256(reference.read_bytes()).hexdigest()),recording=dict(path=str(recording),sha256=hashlib.sha256(recording.read_bytes()).hexdigest()),fit=result,owned_receipt=receipt,limitations=['Timing/gain fitted rather than calibrated','Source call/playing receipt is not acoustic capture','Not full sound equivalence and not RSI ablation'])
out.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n');print(json.dumps(result))
