"""Measure source/native pixel differences; does not promote diagnostics to acceptance."""
import argparse
import hashlib
import json
from pathlib import Path
from PIL import Image, ImageChops, ImageStat
from capture_color import srgb_image, profile_facts

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--native',required=True);p.add_argument('--out',required=True)
p.add_argument('--home-reference',help='Compare this actual home PNG with native home-window.png')
p.add_argument('--pairs', help='Explicit observed source/native screenshot-pair manifest; includes scope limitations')
lessons=p.add_mutually_exclusive_group()
lessons.add_argument('--second-lesson', action='store_true', help='Compare actual second-lesson normal and adaptive question captures')
lessons.add_argument('--third-lesson', action='store_true', help='Compare actual third-lesson normal and adaptive question captures')
lessons.add_argument('--fifth-lesson', action='store_true', help='Compare captured fifth mixed-error trajectory, including speech and settlement')
lessons.add_argument('--fourth-lesson', action='store_true', help='Compare actual fourth 12-question challenge')
a=p.parse_args()
if a.pairs and (a.home_reference or a.second_lesson or a.third_lesson or a.fourth_lesson or a.fifth_lesson): p.error('--pairs cannot be combined with predefined trajectories')
native=Path(a.native);source=Path('projects/duolingo-web/evidence/english-v1')
metadata=json.loads((native/'window.json').read_text())
x,y,w,h=metadata['content_rect_points'];scale=metadata['backing_scale']
assert (w,h)==(1200,732)
if a.second_lesson: source=Path('projects/duolingo-web/evidence/english-second-v1')
if a.third_lesson: source=Path('projects/duolingo-web/evidence/english-third-v1')
if a.fourth_lesson: source=Path('projects/duolingo-web/evidence/english-fourth-v1')
observations={}
for number in (() if a.pairs or a.fifth_lesson else (2,3) if a.fourth_lesson else (1,2) if a.second_lesson or a.third_lesson else (1,2,3)):
    for row in json.loads((source/f'replay-{number:02}.json').read_text())['observed']:
        if 'feedback' in row: observations[row['index']]=row
rows=[]
pairs=[]
explicit = json.loads(Path(a.pairs).read_text()) if a.pairs else None
if explicit:
    pairs = [(row.get('question'),row['stage'],Path(row['source']),native/row['native']) for row in explicit['pairs']]
elif a.home_reference:
    pairs.append((None, 'home', Path(a.home_reference), native/'home-window.png'))
else:
    for index,row in sorted(observations.items()):
        for stage in ('before','feedback'):
            prefix = 'en-zh-l4-q' if a.fourth_lesson else 'en-zh-l3-q' if a.third_lesson else 'en-zh-l2-q' if a.second_lesson else 'en-zh-q'
            pairs.append((index,stage,source/Path(row['screenshot_'+stage]).name,native/f'{prefix}{index}-{stage}.png'))
    if a.second_lesson:
        for index,stem in [(12,'english-second-adaptive'),(13,'english-second-adaptive-2'),(14,'english-second-adaptive-3')]:
            for stage in ('before','feedback'):
                pairs.append((index,stage,source/('reference-english-second-02-question-12-before.png' if index == 12 and stage == 'before' else 'reference-'+stem+'-'+stage+'.png'),native/f'en-zh-l2-q{index}-{stage}.png'))
    if a.third_lesson:
        for index in (12,13,14):
            for stage in ('before','feedback'):
                pairs.append((index,stage,source/f'reference-english-third-adaptive-{index}-{stage}.png',native/f'en-zh-l3-q{index}-{stage}.png'))
if a.fifth_lesson:
    assert not a.home_reference
    source=Path('projects/duolingo-web/evidence/english-next-node-v1')
    for filename in ['replay-01.json','replay-02.json','replay-04.json','replay-05.json']:
        for row in json.loads((source/filename).read_text())['observed']:
            if 'feedback' not in row: continue
            for stage in ['before','feedback']:
                pairs.append((row['index'],stage,source/Path(row['screenshot_'+stage]).name,native/f"en-zh-l5-q{row['index']}-{stage}.png"))
    for original,candidate in [
        ('reference-next-question-2-before','en-zh-l5-q2-before'),
        ('reference-listen-complete-before','en-zh-l5-q3-before'),
        ('reference-listen-complete-feedback','en-zh-l5-q3-feedback'),
        ('reference-next-02-question-5-before','en-zh-l5-q5-before'),
        ('reference-reverse-feedback','en-zh-l5-q5-feedback'),
        ('reference-speak-before','en-zh-l5-speech6-before'),
        ('reference-speak-declined','en-zh-l5-speech6-closed'),
        ('reference-hot-tea-wrong','en-zh-l5-q7-feedback'),
        ('reference-match8-before','en-zh-l5-q8-before'),
        ('reference-match8-wrong','en-zh-l5-q8-wrong'),
        ('reference-match8-feedback','en-zh-l5-q8-feedback'),
        ('reference-match11-before','en-zh-l5-q11-before'),
        ('reference-match11-feedback','en-zh-l5-q11-feedback'),
        ('reference-original14-before','en-zh-l5-q14-before'),
        ('reference-original14-feedback','en-zh-l5-q14-feedback'),
        ('reference-review-hot-feedback','en-zh-l5-q7-review-feedback'),
        ('reference-lesson5-complete-settled','en-zh-l5-complete-window'),
        ('reference-five-gems-settled','en-zh-l5-gems-window'),
        ('reference-profile','en-zh-l5-profile-window'),
        ('reference-home-after-five-uncovered','home-after-lesson-5-window')]:
        pairs.append((None,'fifth-'+original,source/(original+'.png'),native/(candidate+'.png')))
for index,stage,original,candidate in pairs:
    with Image.open(original) as im:
        source_profile=profile_facts(im);reference=srgb_image(im)
    with Image.open(candidate) as im:
        pixels=im.size
        assert pixels==(round(metadata['window_points'][0]*scale),round(metadata['window_points'][1]*scale))
        native_profile=profile_facts(im)
        rendered=srgb_image(im).crop(tuple(round(v*scale) for v in (x,y,x+w,y+h))).resize((int(w),int(h)),Image.Resampling.LANCZOS)
    assert reference.size==rendered.size
    diff=ImageChops.difference(reference,rendered)
    extrema=diff.getextrema();mean=ImageStat.Stat(diff).mean
    # Any RGB difference is reported, with no invented passing tolerance.
    rows.append({'question':index,'stage':stage,'source':original.as_posix(),
                 'native':candidate.name,'source_sha256':hashlib.sha256(original.read_bytes()).hexdigest(),
                 'native_sha256':hashlib.sha256(candidate.read_bytes()).hexdigest(),
                 'color_management':{'source':source_profile,'native':native_profile},
                 'mean_absolute_rgb_difference':mean,
                 'status':'identical' if all(hi==0 for lo,hi in extrema) else 'different'})
result={'kind':'same-viewport-pixel-diagnostic','native_trajectory':explicit['trajectory'] if explicit else 'fifth lesson from hearts4, cold and wrong pair, HOT review, deferred speech' if a.fifth_lesson else 'home after first lesson, hearts4' if a.home_reference else 'fourth lesson all 12 accepted, starting hearts4' if a.fourth_lesson else 'third lesson all accepted, starting hearts4' if a.third_lesson else 'second lesson all accepted, starting hearts4' if a.second_lesson else 'first question wrong sugar, then correct, retry coffee',
        'viewport':[w,h],'normalization':'ICC to common sRGB; crop native titlebar using measured content rect, downsample2x with Lanczos; reference pixels unchanged',
        'rows':rows,'candidate_acceptance':'not_proven',
        'limitations':['This is an actual pixel diagnostic, not a substitute for frontend acceptance',
                       'Animation frames and temporal sound not aligned',
                       'Font antialiasing differs across renderers; reported without tolerance or masking',
                       'Hearts tutorial, source interlude visuals and full completion chain remain incomplete']}
if explicit: result['limitations'] += explicit['limitations']
Path(a.out).write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'pairs':len(rows),'different':sum(r['status']=='different' for r in rows),'candidate_acceptance':'not_proven'}))
