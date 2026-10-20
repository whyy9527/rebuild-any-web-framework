"""Collect screenshot RGB facts for frozen q3 locations, not pass/fail flags."""
import argparse
import hashlib
import json
from pathlib import Path
from PIL import Image
from capture_color import srgb_image, profile_facts
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--native',required=True);p.add_argument('--observed',required=True);p.add_argument('--out',required=True)
a=p.parse_args();native=Path(a.native);d=json.loads(Path(a.observed).read_text());m=json.loads((native/'window.json').read_text())
x,y,w,h=m['content_rect_points'];scale=m['backing_scale'];assert [w,h]==[1200,732]
for phase in ['before','feedback']:
 state='en-zh-l7-q3'+('-feedback' if phase=='feedback' else '')
 path=native/f'en-zh-l7-q3-{phase}.png'
 with Image.open(path) as im:
  assert im.size==tuple(round(v*scale) for v in m['window_points'])
  profile=profile_facts(im)
  rendered=srgb_image(im).crop(tuple(round(v*scale) for v in (x,y,x+w,y+h))).resize((int(w),int(h)),Image.Resampling.LANCZOS)
 d['states'][state]['pixel_color_space']='sRGB'
 d['states'][state]['pixel_samples']={','.join(map(str,point)):list(rendered.getpixel(point)) for point in [(850,500),(301,500)]}
 d['states'][state]['pixel_sample_capture']={'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'filename':path.name,'color_management':profile,'normalization':'ICC to sRGB, measured native titlebar crop and Lanczos downsample to source 1200x732; no masks/tolerance'}
with Path(a.out).open('x') as f:f.write(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
