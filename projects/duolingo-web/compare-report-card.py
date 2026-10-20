"""Compare actual report-card pixels at independently measured matching geometry."""
import argparse
import json
import math
from pathlib import Path
from PIL import Image, ImageChops, ImageStat

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--native',required=True);p.add_argument('--out',required=True)
a=p.parse_args();native=Path(a.native)
source=Path('projects/duolingo-web/evidence/english-feedback-actions-v1')
expected=json.loads((source/'source-observed.json').read_text())['states']['en-zh-feedback-sugar-report-open']['elements']['question-report']['rect']
observed=json.loads((native/'observed.json').read_text())['states']
metadata=json.loads((native/'window.json').read_text());scale=metadata['backing_scale'];x,y,w,h=metadata['content_rect_points']
assert (w,h)==(1200,732)
rows=[]
for stage,file in [('report-open','english-feedback-report-open.png'),('report-other','english-feedback-report-other-selected.png'),('report-two','english-feedback-report-two-selected.png'),('report-reopened','english-feedback-report-reopened.png')]:
    state='en-zh-feedback-sugar-'+stage
    actual=observed[state]['elements'].get('question-report',{}).get('rect')
    row={'state':state,'expected_rect':expected,'actual_rect':actual}
    if actual!=expected:row['status']='geometry_mismatch';rows.append(row);continue
    rx,ry,rw,rh=expected;roi=(math.floor(rx),math.floor(ry),math.ceil(rx+rw),math.ceil(ry+rh))
    with Image.open(source/file) as im:
        assert im.size==(w,h)
        reference=im.convert('RGB').crop(roi)
    with Image.open(native/(state+'.png')) as im:
        assert im.size==tuple(round(v*scale) for v in metadata['window_points'])
        content=im.crop(tuple(round(v*scale) for v in (x,y,x+w,y+h))).convert('RGB').resize((w,h),Image.Resampling.LANCZOS)
    diff=ImageChops.difference(reference,content.crop(roi))
    row.update(status='different' if diff.getbbox() else 'identical',mean_absolute_rgb_difference=ImageStat.Stat(diff).mean,roi_pixels=list(roi))
    rows.append(row)
result={'kind':'actual-report-card-pixel-diagnostic','rows':rows,'candidate_acceptance':'not_proven',
        'limitations':['Card only, excludes close control and lesson background; full product state differs',
                       'Native measured titlebar crop and 2x downsample; original unchanged',
                       'No masks or passing tolerance; typography, checkbox strokes and antialiasing remain in comparison']}
Path(a.out).write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'statuses':[r['status'] for r in rows],'candidate_acceptance':'not_proven'}))
