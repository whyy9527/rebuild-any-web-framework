"""Verify a source-observed resource in actual owned-app playback, not source acoustics."""
import argparse,hashlib,importlib.util,json,tempfile
from pathlib import Path
B=Path(__file__).resolve().parent;R=B.parent/'education-swift/Sources/LingoSeed/Resources/Reference'
spec=importlib.util.spec_from_file_location('audio',B/'compare-feedback-audio.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
p=argparse.ArgumentParser();p.add_argument('--native',required=True);p.add_argument('--source',required=True);p.add_argument('--out',required=True);a=p.parse_args();n=Path(a.native);out=Path(a.out);assert not out.exists()
source=json.loads(Path(a.source).read_text().split('### Result\n')[1].split('\n### Ran')[0]);urls={x['src'] for x in source['audio'] if x['src']}
assert source['path']=='/alphabets/en/pronunciation' and len(urls)==1
manifest=json.loads((B/'reference-pronunciation-practice-audio-v2.json').read_text());rows=[x for x in manifest['resources'] if x['url'] in urls];assert len(rows)==1
resource=rows[0];original=R/resource['resource'];assert hashlib.sha256(original.read_bytes()).hexdigest()==resource['sha256']
practice=json.loads((R/'pronunciation-practice.json').read_text());assert practice['lessons'][0]['questions'][0]['practiceAudioResources']==[resource['resource']]
name='pronunciation-entry-speech';receipt=json.loads((n/(name+'.wav.json')).read_text());assert not receipt.get('failure') and receipt['microphone'] is False and receipt['samples']>0 and [x['id'] for x in receipt['ui_actions']]==['pronunciation-start']
with tempfile.TemporaryDirectory() as tmp:
 ref=m.decode(original,Path(tmp));actual=m.decode(n/(name+'.wav'),Path(tmp));metrics=m.measure(ref,actual);assert abs(m.measure(ref,ref)['normalized_correlation']-1)<1e-8
out.write_text(json.dumps(dict(scope='Source media.play identity matched to original resource measured in real owned Swift entry output; source acoustic equality unverified',source_url=resource['url'],resource=resource['resource'],resource_sha256=resource['sha256'],recording_sha256=hashlib.sha256((n/(name+'.wav')).read_bytes()).hexdigest(),metrics=metrics,owned_capture=receipt,limitations=['No source acoustic recording','No completion effect, normal microphone exercise or adaptive selection equivalence inferred']),ensure_ascii=False,indent=2)+'\n')
print(json.dumps(dict(correlation=metrics['normalized_correlation'],gain=metrics['fitted_gain'])))
