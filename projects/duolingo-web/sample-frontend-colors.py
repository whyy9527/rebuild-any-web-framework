"""Project frozen color locations onto actual native captures; never infer pass flags."""
import argparse
import hashlib
import json
from pathlib import Path
from PIL import Image
from capture_color import profile_facts, srgb_image

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--contract', required=True)
p.add_argument('--observed', required=True)
p.add_argument('--out', required=True)
a = p.parse_args()
receipt = json.loads(Path(a.observed).read_text())
requirements = json.loads(Path(a.contract).read_text())['requirements']
for key, state in receipt['states'].items():
    points = {tuple(r['point']) for r in requirements if r['state'] == key and r['kind'] == 'pixel_color'}
    if not points:
        continue
    capture = state['capture']
    path = Path(capture['path'])
    x, y, w, h = capture['content_rect_points']
    scale = capture['backing_scale']
    with Image.open(path) as image:
        assert image.size == tuple(round(v * scale) for v in capture['window_points'])
        profile = profile_facts(image)
        rendered = srgb_image(image).crop(tuple(round(v * scale) for v in (x, y, x+w, y+h))).resize((int(w), int(h)), Image.Resampling.LANCZOS)
    state['pixel_color_space'] = 'sRGB'
    state['pixel_samples'] = {','.join(map(str, point)): list(rendered.getpixel(point)) for point in sorted(points)}
    state['pixel_sample_capture'] = dict(sha256=hashlib.sha256(path.read_bytes()).hexdigest(), filename=path.name, color_management=profile,
        normalization='ICC to sRGB; measured content crop and backing scale; Lanczos to source viewport; no masks or tolerance')
with Path(a.out).open('x') as output:
    output.write(json.dumps(receipt, ensure_ascii=False, indent=2)+'\n')
