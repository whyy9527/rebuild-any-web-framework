"""Bind a currently observed public character to its verified source Rive file."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import re
from urllib.request import urlopen

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--current', required=True)
p.add_argument('--renderer', required=True)
p.add_argument('--out', required=True)
a = p.parse_args()
current_path, renderer_path = Path(a.current), Path(a.renderer)
current, renderer = json.loads(current_path.read_text()), json.loads(renderer_path.read_text())
assert current['visible_text'] == renderer['prompt'], 'Current content and canvas observation differ'
character = current['content']['character']
assert re.fullmatch(r'[A-Za-z_]+', character['name'])
svg, animation = character['image']['svg'], renderer['renderer']['animation']
assert svg.startswith('https://d2pur3iezf4d1j.cloudfront.net/images/') and '?' not in svg
assert animation['url'].startswith('https://d35aaqx5ub95lt.cloudfront.net/rive/') and '?' not in animation['url']
out = Path(a.out)
assert not out.exists(), 'Choose a fresh receipt before importing'
with urlopen(animation['url'], timeout=30) as response:
    wire = response.read()
decoded = gzip.decompress(wire) if wire.startswith(b'\x1f\x8b') else wire
sha = hashlib.sha256(decoded).hexdigest()
assert decoded[:4] == b'RIVE' and sha == renderer['renderer']['buffer']['sha256'], 'Public file differs from actual source renderer buffer'
base = Path(__file__).resolve().parent.parent / 'education-swift/Sources/LingoSeed/Resources/Reference'
resource = 'en-character-'+character['name'].lower()+'.riv'
target = base / resource
assert not target.exists() or target.read_bytes() == decoded, 'Existing character resource has different bytes'
key = 'en-image-'+hashlib.sha256(svg.encode()).hexdigest()[:20]
configuration = dict(resource=resource, name=character['name'], artboard=animation['artBoardName'],
    stateMachine=animation['stateMachineName'], correctTrigger=animation['correctStateName'],
    incorrectTrigger=animation['incorrectStateName'], resetTrigger=animation['notSetStateName'],
    darkModeInput=animation['darkModeStateName'], rtlInput=animation['rtlStateName'],
    scale=animation['scale'], xOffsetPercentage=animation['xOffsetPercentage'], yOffsetPercentage=animation['yOffsetPercentage'])
config_path = base / 'character-animations.json'
configurations = json.loads(config_path.read_text())
assert key not in configurations or configurations[key] == configuration, 'Existing binding differs; inspect source version before replacing'
target.write_bytes(decoded)
configurations[key] = configuration
config_path.write_text(json.dumps(configurations, ensure_ascii=False, indent=2)+'\n')
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(dict(public_svg=svg, public_rive=animation['url'], resource=resource,
    wire_bytes=len(wire), wire_sha256=hashlib.sha256(wire).hexdigest(), decoded_bytes=len(decoded), decoded_sha256=sha,
    source_buffer_equal=True, configuration_key=key, configuration=configuration,
    source_current=current_path.name, source_renderer=renderer_path.name,
    limitations=['Asset identity and observed renderer parameters only; native pose, timing, geometry and sound require separate verification.']), indent=2)+'\n')
print(json.dumps(dict(imported=character['name'], bytes=len(decoded), source_buffer_equal=True)))
