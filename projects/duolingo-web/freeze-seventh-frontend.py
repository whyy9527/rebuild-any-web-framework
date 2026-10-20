"""Add actually observed seventh-lesson states to the shared frontend mold.

Uses archived real UI receipts, not the initial API order or candidate output.
Source observations are a replay of collected facts, not a new live source run.
"""
import json
import re
from pathlib import Path
BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[1]
EV = BASE/'evidence/english-seventh-v1'
OLD = BASE/'evidence/english-secondary-actions-v1'
def read(path): return json.loads(path.read_text())
def write(path, value): path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
def relative(path): return path.relative_to(ROOT).as_posix()
rows=[]
def add(key,path,field='snapshot',extra=None):
    d=read(path);snapshot=d[field]; texts=[]
    for line in snapshot.splitlines():
        match=re.search(r'\b(?:heading|button) "([^"\n]+)"',line)
        if match: texts.append(match[1])
        match=re.search(r'\btext: (.+)$',line)
        if match and '0 1 2 3 4 5 6 7 8 9' not in match[1]:
            value=match[1]
            if value.startswith('"'):
                try: value=json.loads(value)
                except ValueError: pass
            texts.append(value)
    texts.extend(extra or [])
    rows.append(dict(state='en-zh-l7-'+key, evidence=relative(path), texts=list(dict.fromkeys(texts))))
add('q0',OLD/'secondary-reset-q0.json')
add('q0-skipped',OLD/'secondary-q0-skipped.json')
for key,filename in [('q1','secondary-keyboard-answer.json'),('q2','secondary-pairs.json'),('q4','secondary-harder-answer.json')]:
    path=OLD/filename;d=read(path)
    add(key,path,'before',d.get('prompts'))
    add(key+'-feedback',path,'feedback')
add('q3',OLD/'secondary-listen-isolation-before.json')
add('q3-feedback',OLD/'secondary-listen-isolation-feedback.json')
for key,filename in [('q5','seventh-q5-answer.json'),('q6','seventh-q6-answer.json'),('q7','seventh-q7-answer.json'),('q8','seventh-q8-answer.json'),('q9','seventh-q9-answer.json'),('q10-inserted','seventh-inserted-answer.json'),('q11','seventh-q11-answer.json'),('q12','seventh-q12-answer.json'),('q13-replacement','seventh-q13-replacement-answer.json'),('q14','seventh-q14-answer.json'),('review-q0','seventh-review-q0-answer.json')]:
    path=EV/filename;d=read(path);assert not d['rejected']
    add(key,path,'before',d.get('prompts'))
    add(key+'-feedback',path,'feedback')
add('q10-speech',EV/'seventh-q10.json','after')
add('q10-declined',EV/'seventh-speech-declined.json')
add('review-intro',EV/'seventh-review-intro.json')
# AX's rolling-digit parents are not displayed score values. Explicit PNG annotation.
visual=read(EV/'settlement-visual.json');assert visual['experience']==15 and visual['accuracy']==100
rows.append(dict(state='en-zh-l7-result',evidence=relative(EV/'settlement-visual.json'),texts=[visual['title'],visual['body'],'15','100%','回顾本单元','继续']))
add('achievement',EV/'seventh-achievement.json')
add('profile',EV/'seventh-profile.json')
add('home',EV/'seventh-home.json')
requirements=[];states={}
for row in rows:
    state=row['state'];refs=[row['evidence']]
    assert row['texts'],state
    states[state]={'accessible_text':row['texts']}
    for i,text in enumerate(row['texts']):
        requirements.append(dict(id=state+'-text-'+str(i),state=state,kind='accessible_text',text=text,evidence=refs))
    for dimension in ['pixels','actual-audio']:
        requirements.append(dict(id=state+'-'+dimension,state=state,kind='pending',description='Actual '+dimension+' equivalence not verified for this source state',evidence=refs))
# Trace-level skip result is independently derived from real before/after/review/PNG.
before=read(OLD/'secondary-reset-q0.json')['snapshot'];skipped=read(OLD/'secondary-q0-skipped.json')['snapshot']
assert 'text: "2"' in before and 'text: "2"' in skipped
assert read(EV/'seventh-review-q0-answer.json')['prompts']==['tea and coffee']
state='en-zh-l7-q0-skipped';facts={'hearts_unchanged':True,'original_question_reviewed':True,'settlement_mistake':False}
states[state]['interactions']=facts
for field,value in facts.items():
    requirements.append(dict(id=state+'-'+field,state=state,kind='interaction_boolean',field=field,expected=value,evidence=[relative(OLD/'secondary-q0-skipped.json'),relative(EV/'seventh-review-q0-answer.json'),relative(EV/'settlement-visual.json')]))
contract={'revision':'actual-seventh-skip-normal-listening-speech-declined-v1','requirements':requirements}
write(BASE/'frontend-english-seventh-v1.json',contract)
write(EV/'source-full-observed.json',{'states':states,'scope':'Replay of actual source UI receipts. Settlement numbers explicitly read from actual PNG. Not a new live rerun or visual/audio equivalence.'})
product=read(BASE/'frontend-english-v12.json');product['revision']='english-v13-with-actual-seventh-source';product['requirements']+=requirements
assert len({r['id'] for r in product['requirements']})==len(product['requirements'])
write(BASE/'frontend-english-v13.json',product)
print('Frozen',len(states),'actual source states;',len(requirements),'seventh requirements;',len(product['requirements']),'product requirements')
