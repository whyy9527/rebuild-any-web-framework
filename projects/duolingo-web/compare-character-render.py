"""Measure actual source/native character captures, without a passing tolerance."""
import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image, ImageChops, ImageStat

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--native', required=True)
p.add_argument('--source', default='projects/duolingo-web/evidence/english-character-render-v1')
p.add_argument('--out', required=True)
a = p.parse_args()
native, source = Path(a.native), Path(a.source)
metadata = json.loads((native / 'window.json').read_text())
observed = json.loads((native / 'observed.json').read_text())
x, y, w, h = metadata['content_rect_points']
scale = metadata['backing_scale']
assert (w, h) == (1200, 732)

def content(path):
    with Image.open(path) as im:
        assert im.size == tuple(round(v * scale) for v in metadata['window_points'])
        return im.crop(tuple(round(v * scale) for v in (x, y, x+w, y+h))).convert('RGB').resize((w, h), Image.Resampling.LANCZOS)

rows, motion = [], []
for stage, reference, state in [('before', 'bea-idle-page.png', 'en-zh-render-q0'),
                                ('feedback', 'bea-correct-page.png', 'en-zh-render-q0-feedback')]:
    candidate = native / f'en-zh-render-q0-{stage}.png'
    original = source / reference
    with Image.open(original) as im:
        ref = im.convert('RGB')
    rendered = content(candidate)
    assert ref.size == rendered.size
    difference = ImageChops.difference(ref, rendered)
    rows.append({'state': state, 'source': reference, 'native': candidate.name,
                 'source_sha256': hashlib.sha256(original.read_bytes()).hexdigest(),
                 'native_sha256': hashlib.sha256(candidate.read_bytes()).hexdigest(),
                 'mean_absolute_rgb_difference': ImageStat.Stat(difference).mean,
                 'status': 'different' if difference.getbbox() else 'identical'})
    rx, ry, rw, rh = observed['states'][state]['elements']['question-character']['rect']
    frames = sorted(native.glob(f'en-zh-render-q0-character-{"idle" if stage == "before" else "feedback"}-*.png'))
    assert len(frames) == 12
    # Measure only the actual character region; other changing UI cannot count as character motion.
    roi = tuple(round(v) for v in (rx, ry, rx+rw, ry+rh))
    hashes = [hashlib.sha256(content(frame).crop(roi).tobytes()).hexdigest() for frame in frames]
    motion.append({'state': state, 'rect': [rx, ry, rw, rh], 'frames': len(frames),
                   'distinct_character_rgb_frames': len(set(hashes)),
                   'frame_hashes': dict(zip([frame.name for frame in frames], hashes))})

source_frames = []
for name in ['bea-idle.json', 'bea-correct.json', 'lucy-idle.json']:
    data = json.loads((source / name).read_text())
    hashes, bounds = [], []
    for frame in data['frames']:
        path = source / frame['file']
        assert hashlib.sha256(path.read_bytes()).hexdigest() == frame['sha256']
        with Image.open(path) as im:
            rgba = im.convert('RGBA')
            assert rgba.getchannel('A').getextrema() == (0, 255)
            bounds.append(rgba.getchannel('A').getbbox())
            hashes.append(hashlib.sha256(rgba.tobytes()).hexdigest())
    source_frames.append({'capture': name, 'frames': len(hashes), 'distinct_rgba_frames': len(set(hashes)), 'alpha_bounds': bounds})

result = {'kind': 'actual-character-render-diagnostic', 'viewport': [w, h],
          'normalization': 'Measured native titlebar crop, 2x downsample Lanczos; source unchanged',
          'pixel_pairs': rows, 'native_character_motion': motion, 'source_transparent_buffer_frames': source_frames,
          'candidate_acceptance': 'not_proven',
          'limitations': ['Different capture times; animation phases not aligned',
                         'Motion proves changing character pixels, not matching source state-machine timing or mouth/audio sync',
                         'Pixel differences include typography, layout, antialiasing and animation; no masks or passing tolerance']}
Path(a.out).write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({'pixel_pairs': [r['status'] for r in rows], 'native_distinct_character_frames': [r['distinct_character_rgb_frames'] for r in motion], 'candidate_acceptance': 'not_proven'}))
