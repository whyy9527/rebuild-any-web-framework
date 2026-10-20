"""Produce explicit source/native capture pairs, retaining missing source pixels."""
import argparse
import json
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--out',required=True);a=p.parse_args()
BASE=Path(__file__).resolve().parent;ROOT=BASE.parents[1]
OLD=BASE/'evidence/english-secondary-actions-v1';EV=BASE/'evidence/english-seventh-v1'
pairs=[]
def add(stage,source,native):
    assert source.exists(),source
    pairs.append(dict(stage=stage,source=source.relative_to(ROOT).as_posix(),native=native))
for key,source,native in [('q0','secondary-reset-q0.png','en-zh-l7-q0-before.png'),('q0-skipped','secondary-q0-skipped.png','en-zh-l7-q0-skipped.png'),('q1','secondary-keyboard-answer-before.png','en-zh-l7-q1-empty.png'),('q1-feedback','secondary-keyboard-answer-feedback.png','en-zh-l7-q1-feedback.png'),('q2','secondary-pairs-before.png','en-zh-l7-q2-before.png'),('q2-feedback','secondary-pairs-feedback.png','en-zh-l7-q2-feedback.png'),('q3','secondary-listen-isolation-before.png','en-zh-l7-q3-before.png'),('q3-feedback','secondary-listen-isolation-feedback.png','en-zh-l7-q3-feedback.png'),('q4','secondary-harder-answer-before.png','en-zh-l7-q4-empty.png'),('q4-feedback','secondary-harder-answer-feedback.png','en-zh-l7-q4-feedback.png')]:add(key,OLD/source,native)
for key,stem in [('q5','seventh-q5-answer'),('q6','seventh-q6-answer'),('q7','seventh-q7-answer'),('q8','seventh-q8-answer'),('q9','seventh-q9-answer'),('q10-inserted','seventh-inserted-answer'),('q11','seventh-q11-answer'),('q12','seventh-q12-answer'),('q13-replacement','seventh-q13-replacement-answer'),('q14','seventh-q14-answer'),('review-q0','seventh-review-q0-answer')]:
    for phase in ['before','feedback']:
        name='en-zh-l7-'+key+('' if key=='review-q0' and phase=='before' else '-'+phase)
        add(key+'-'+phase,EV/(stem+'-'+phase+'.png'),name+'.png')
for key,source,native in [('q10-declined','seventh-speech-declined.png','en-zh-l7-q10-speech-closed.png'),('review-intro','seventh-review-intro.png','en-zh-l7-review-intro-window.png'),('result','seventh-completion-settled.png','en-zh-l7-result-window.png'),('achievement','seventh-achievement.png','en-zh-l7-achievement-window.png'),('profile','seventh-profile.png','en-zh-l7-profile-window.png'),('home','seventh-home.png','home-after-lesson-7-window.png')]:add(key,EV/source,native)
result=dict(trajectory='Actual seventh skip/radio2/input-preferences/speech-declined/insertion/review/settlement path; source heart2->3 refresh unexplained, native retains2; animation/audio phase unaligned',limitations=['All RGB differences retained without tolerance or masking','q1/q4 use actual empty-after-toggle captures to match source before state','Source q10-speech has an AX receipt but no archived PNG; visual comparison unavailable, not passed'],unavailable=[dict(state='en-zh-l7-q10-speech',reason='No archived source PNG')],pairs=pairs)
Path(a.out).write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print('pairs',len(pairs),'unavailable',1)
