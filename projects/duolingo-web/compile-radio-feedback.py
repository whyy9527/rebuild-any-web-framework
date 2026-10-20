"""Extend frozen v8 with the actual seventh isolation feedback phrase/frame."""
import hashlib
import json
from pathlib import Path
from PIL import Image
base=Path(__file__).resolve().parent
fixture=json.loads((base/'fixture-reference-en-zh-v8.json').read_text())
source=base/'evidence/english-secondary-actions-v1/secondary-listen-isolation-feedback.json'
receipt=json.loads(source.read_text())
phrase='No ice, please.'
assert any(phrase in item.get('text','').splitlines() for item in receipt['visible'])
raw=json.loads((base/'evidence/english-secondary-actions-v1/secondary-session.json').read_text())['session']['challenges'][3]['content']
assert ''.join(t['value'] for t in raw['tokens'])==phrase
q=fixture['data']['candidate_course']['lessons'][6]['questions'][3]
assert q['id']=='en-zh-l7-q3' and q['answer']=='1'
q['feedbackHint']=phrase
name='en-seventh-isolation-wave-2-correct'
q['options'][1]['correctImageResource']=name
png=source.with_suffix('.png');rect=[558,492,710,522]
resource=base.parent/'education-swift/Sources/LingoSeed/Resources/Reference'/(name+'.png')
with Image.open(png) as im:im.crop(rect).save(resource)
fixture['provenance']['evidence'].append('projects/duolingo-web/evidence/english-radio-feedback-v1/README.md')
(base/'fixture-reference-en-zh-v9.json').write_text(json.dumps(fixture,ensure_ascii=False,indent=2)+'\n')
binding={'source_png':str(png.relative_to(base.parent.parent)), 'source_sha256':hashlib.sha256(png.read_bytes()).hexdigest(),'crop':rect,'resource':resource.name,'sha256':hashlib.sha256(resource.read_bytes()).hexdigest(),'scope':'Observed correct-feedback static waveform frame; not animation equality'}
(base/'evidence/english-radio-feedback-v1/resource-binding.json').write_text(json.dumps(binding,ensure_ascii=False,indent=2)+'\n')
