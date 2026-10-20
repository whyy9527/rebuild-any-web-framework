"""Freeze actual cold rejection and HOT acceptance without replacing older probes."""
from pathlib import Path
import json
BASE=Path(__file__).resolve().parent;EV=BASE/'evidence/english-next-node-v1'
read=lambda name:json.loads((EV/name).read_text())
wrong=read('hot-tea-wrong.json');review=read('review-hot.json')
assert wrong['input']=='cold' and 'hot tea' in wrong['feedback']
assert review['input']=='HOT' and '正确！' in review['feedback']
assert read('session.json')['session']['challenges'][7]['content']['displayTokens'][0]['text']=='hot'
f=json.loads((BASE/'fixture-english-input-probe.json').read_text());c=f['data']['candidate_course'];c['id']='english-hot-review-probe'
q=dict(c['lessons'][0]['questions'][1]);q.update(id='en-zh-node2-hot-review',answer='hot',hint='热茶',completionPrefix='',completionSuffix=' tea',correctFeedback='正确！')
c['lessons']=[dict(id='hot-review-probe',title='热茶错题重练验证',questions=[q])];c['pathNodes']=[dict(kind='star',lessonIDs=['hot-review-probe'],lessonCount=4)]
f['provenance']=dict(source='Actual cold rejection, HOT acceptance in source hot-tea review',evidence=['projects/duolingo-web/evidence/english-next-node-v1/hot-tea-wrong.json','projects/duolingo-web/evidence/english-next-node-v1/review-hot.json'],scope='One isolated mistake/review component, not full lesson',unknown='Case-insensitive comparison inferred from HOT acceptance; whitespace, punctuation and typo grading remain unverified')
(BASE/'fixture-english-hot-review-probe.json').write_text(json.dumps(f,ensure_ascii=False,indent=2)+'\n')
prefix='projects/duolingo-web/evidence/english-next-node-v1/';state='en-zh-node2-hot-review';req=[]
def add(kind,suffix,part,**fields):req.append(dict(id=state+'-'+suffix,state=state+part,kind=kind,evidence=[prefix+'hot-tea-wrong.json',prefix+'review-hot.json'],**fields))
for text in ['正确答案：','hot tea']:add('accessible_text','wrong-'+text,'-wrong',text=text)
add('interaction_boolean','wrong-heart','-wrong',field='heart_decremented_once',expected=True)
add('interaction_boolean','wrong-locked','-wrong',field='submitted_input_locked',expected=True)
add('accessible_text','review-label','-review',text='错题重练')
add('interaction_boolean','review-empty','-review',field='review_input_empty',expected=True)
add('accessible_text','accepted','-feedback',text='正确！')
for category in ['visual','audio','full-grader']:add('pending',category,'',description='Typed review '+category+' equality remains unverified')
contract=dict(revision='hot-review-component-v1',scope='Observed cold rejection and HOT acceptance; not full source grading',requirements=req)
(BASE/'frontend-english-hot-review-probe.json').write_text(json.dumps(contract,ensure_ascii=False,indent=2)+'\n')
f=json.loads((BASE/'frontend-english-v8.json').read_text());f.update(revision='actual-en-zh-frontends-v9',scope='Preserve v8 and add observed typed error, full correction, review and uppercase input',requirements=f['requirements']+req)
(BASE/'frontend-english-v9.json').write_text(json.dumps(f,ensure_ascii=False,indent=2)+'\n')
print('Source hot review fixture and v9 frontend frozen;',len(f['requirements']),'product requirements')
