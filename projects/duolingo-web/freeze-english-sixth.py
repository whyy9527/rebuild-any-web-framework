"""Freeze actual sixth-lesson continuation, keeping unknown frontend behavior explicit.

No API-row replay is used to reconstruct replacements. Actual positive feedback
and previous visited DOM snapshots are the evidence. This is not a grader model.
"""
import json
import re
from pathlib import Path

BASE=Path(__file__).resolve().parent
EV=BASE/'evidence/english-sixth-v1'
def read(name): return json.loads((EV/name).read_text())
def write(path,data):path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
def copytexts(snapshot):
    # Parse actual AX/CLI lines, excluding CLI console and command output.
    return sorted(set(re.findall(r'^\s*- (?:heading|button|textbox|link) "([^"\n]+)"',snapshot,re.M)+re.findall(r'^\s*- (?:text|generic|paragraph): (.+)$',snapshot,re.M)))
requirements=[];states={}
def state(name,snapshot,evidence,extra=()):
    sid='en-zh-l6-'+name;labels=sorted(set(copytexts(snapshot)+list(extra)))
    states[sid]={'accessible_text':labels}
    for i,label in enumerate(labels):
        requirements.append(dict(id=sid+'-text-'+str(i),state=sid,kind='accessible_text',text=label,evidence=evidence))
    for kind in ['same-state-visuals','actual-audio']:
        requirements.append(dict(id=sid+'-'+kind,state=sid,kind='pending',description=kind+' remains unverified',evidence=evidence))
    return sid
prefix=EV.relative_to(BASE.parent.parent).as_posix()+'/'
trajectory=[]
# q numbers are actual presentation positions, not original API indices.
for number in [6,7,8,9,10,11,12,13,14,15]:
    stem=f'english-sixth-q{number}'+('-adaptive' if number==9 else '')
    if number==7:
        before=read(stem+'-before.json')['snapshot'];feedback=read(stem+'-feedback.json')['snapshot']
        row=read('q7-input-action.json');files=[stem+'-before.json',stem+'-feedback.json','q7-input-action.json'];answer=row['input']
        assert 'textbox "Good morning, coffee with , please." [disabled]: milk' in feedback
    else:
        file=stem+'-answer.json';row=read(file);assert row['rejected'] is False
        before=row['before'];feedback=row['feedback'];files=[file]
        answer=row.get('input',[a['word'] for a in row.get('clicks',[])])
    assert re.search(r'heading "[^"\n]+" \[level=2\]',feedback)
    assert '正确答案：' not in feedback
    # Typed helper originally retained AX only; recover missing prompt from the
    # independently saved immediately preceding CLI snapshot, never API guesses.
    previous={7:'after-q7',9:'after-speech-decline',10:'after-q9-adaptive',11:'after-q10',12:'after-q11',13:'after-entry',14:'after-q13',15:'after-q14'}.get(number)
    if number!=7 and previous:
        file='english-sixth-'+previous+'.json';before+='\n'+read(file)['after'];files.append(file)
    evidence=[prefix+f for f in files]
    a=state(f'q{number}',before,evidence,row.get('prompts',[]));b=state(f'q{number}-feedback',feedback,evidence)
    trajectory.append(dict(id=f'q{number}',source_state=a,feedback_state=b,accepted_answer=answer,evidence=evidence))
for name,file in [('speech-declined','english-sixth-q9-speech-declined.json'),('challenge-entry','english-sixth-challenge-entry.json'),('complete','english-sixth-complete.json'),('profile','english-sixth-profile.json'),('home','english-sixth-home.json')]:
    d=read(file);state(name,d['snapshot'],[prefix+file])
visual=read('completion-visual.json');assert visual['experience']==15 and visual['accuracy']==100
# This rendered score is manual visual evidence, not a text/AX pass assertion.
trajectory_data=dict(kind='actual-sixth-lesson-continuation',observed=trajectory,prior='projects/duolingo-web/evidence/english-feedback-actions-v1/exploration-history.json',completion=visual,unknown=['Full normal-listening/speaking trajectories and transitions','15-minute expiry/persistence','Actual acoustic output and 1:1 render','General adaptation and score formulas'],next_source_state='Home; second node Lesson 3 of 4, hearts2/gems510')
write(EV/'trajectory.json',trajectory_data)
contract=dict(revision='actual-sixth-continuation-v1',requirements=requirements)
write(BASE/'frontend-english-sixth.json',contract)
write(EV/'source-observed.json',dict(kind='actual-source-AX-and-visible-DOM',states=states))
prior=json.loads((BASE/'frontend-english-v10.json').read_text())
prior['revision']='english-v11-sixth-continuation'
prior['requirements']+=requirements
assert len({r['id'] for r in prior['requirements']})==len(prior['requirements'])
write(BASE/'frontend-english-v11.json',prior)
print('Frozen',len(states),'states;',len(requirements),'new requirements;',len(prior['requirements']),'product requirements')
