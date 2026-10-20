"""Freeze actual difficulty/report UI observations for both platform drivers."""
import json
import re
from pathlib import Path

BASE=Path(__file__).resolve().parent
EV=BASE/'evidence/english-feedback-actions-v1'
key='en-zh-feedback-sugar'
def read(n):return json.loads((EV/n).read_text())
states={};requirements=[]
def texts(s):return sorted(set(re.findall(r'"([^"\n]+)"',s)+re.findall(r'- text: ([^\n]+)',s)))
def observe(suffix,file,interactions=None):
    d=read(file);s=d.get('snapshot',d.get('feedback'))
    state=key+suffix;states[state]={'accessible_text':texts(s),'interactions':interactions or {}}
    return state,s,(EV/file).relative_to(BASE.parent.parent).as_posix()
def text(state,suffix,value,evidence):requirements.append(dict(id=state+'-'+suffix,state=state,kind='accessible_text',text=value,evidence=[evidence]))
def boolean(state,field,value,evidence):requirements.append(dict(id=state+'-'+field,state=state,kind='interaction_boolean',field=field,expected=value,evidence=[evidence]))
state,s,ref=observe('-feedback','sugar-answer.json')
for label in ['非常好！','太简单','太难','报错']:text(state,label,label,ref)
for suffix,file in [('-easy','english-feedback-easy-selected.json'),('-hard','english-feedback-hard-selected.json'),('-deselected','english-feedback-deselected.json')]:
    d=read(file);s=d['snapshot']
    facts={field:bool(re.search(r'- button "'+label+r'"[^\n]*\[pressed\]',s)) for field,label in [('easy_selected','太简单'),('hard_selected','太难')]}
    state,s,ref=observe(suffix,file,facts)
    for field,value in facts.items():boolean(state,field,value,ref)
state,s,ref=observe('-report-open','english-feedback-report-open.json',{'submit_disabled':True})
reasons=re.findall(r'- checkbox "([^"\n]+)"',s)
assert len(reasons)==6 and '- button "提交" [disabled]' in s
for i,label in enumerate(reasons):text(state,'reason-'+str(i),label,ref)
boolean(state,'submit_disabled',True,ref)
layout=read('english-feedback-report-reopened.json')
popup=next(n for n in layout['visible'] if n['tag']=='BUTTON' and n['text']=='提交')['ancestors'][0]['rect']
rect=[popup[k] for k in ['x','y','width','height']]
states[state]['elements']={'question-report':{'rect':rect}}
requirements.append(dict(id=state+'-geometry',state=state,kind='element_geometry',element='question-report',rect=rect,tolerance_points=0,evidence=[(EV/'english-feedback-report-reopened.json').relative_to(BASE.parent.parent).as_posix()]))
state,s,ref=observe('-report-other','english-feedback-report-other-selected.json',{'other_checked':True,'submit_enabled':True})
assert '- checkbox "其他问题" [checked]' in s and '- button "提交" [disabled]' not in s
for field in ['other_checked','submit_enabled']:boolean(state,field,True,ref)
state,s,ref=observe('-report-two','english-feedback-report-two-selected.json',{'both_checked':True})
assert '- checkbox "音频听起来不正确" [checked]' in s and '- checkbox "其他问题" [checked]' in s
boolean(state,'both_checked',True,ref)
state,s,ref=observe('-report-closed','english-feedback-report-cancelled.json',{'report_closed':True})
assert '- checkbox ' not in s
boolean(state,'report_closed',True,ref);text(state,'feedback','非常好！',ref)
state,s,ref=observe('-report-reopened','english-feedback-report-reopened.json',{'submit_disabled':True,'all_unchecked':True})
assert len(re.findall(r'- checkbox ',s))==6 and '[checked]' not in s and '- button "提交" [disabled]' in s
for field in ['submit_disabled','all_unchecked']:boolean(state,field,True,ref)
for gap in ['same-state-pixels','audio','other-challenge-report-options','submission-service','difficulty-server-effect','escape-and-outside-native-dismissal']:
    requirements.append(dict(id='feedback-'+gap,state=key+'-feedback',kind='pending',description=gap+' remains unverified',evidence=[ref]))
for name,data in [('frontend-feedback-actions.json',dict(revision='actual-feedback-actions-v1',requirements=requirements)),('evidence/english-feedback-actions-v1/source-observed.json',dict(kind='actual-source-AX-and-visible-DOM',states=states))]:
    (BASE/name).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
print('Frozen',len(requirements),'requirements from',len(states),'actually visited source states')
