"""Freeze actual q0 skip/review as a compressed action probe, not lesson seven.

Source receipts precede implementation. Full-course scoring, elapsed heart
refresh, changed review bank order, animation and skip audio remain separate.
"""
import json
from pathlib import Path
BASE = Path(__file__).resolve().parent
OLD = BASE/'evidence/english-secondary-actions-v1'
EV = BASE/'evidence/english-seventh-v1'
def read(p): return json.loads(p.read_text())
def write(p,x): p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
f = read(BASE/'fixture-reference-en-zh-secondary-v3.json')
c = read(OLD/'secondary-session.json')['session']['challenges'][0]['content']
before=read(OLD/'secondary-reset-q0.json'); skipped=read(OLD/'secondary-q0-skipped.json')
review=read(EV/'seventh-review-q0-answer.json')
assert 'button "跳过"' in before['snapshot']
assert 'heading "正确答案："' in skipped['snapshot'] and 'text: 茶和咖啡' in skipped['snapshot']
assert not review['rejected'] and [x['word'] for x in review['clicks']] == c['correctTokens']
a=read(BASE/'reference-assets-en-zh-v7.json')
character=next(x['name'] for x in a if x['url']==c['character']['image']['svg'])
words=['谢谢你','和','茶','咖啡']
q=dict(id='en-zh-l7-q0',kind='word_tiles',sourceType='translate',sourceLanguage='en',prompt='用中文（简体）写出这句话',hint=c['prompt'],words=[dict(id=str(i),text=t) for i,t in enumerate(words)],answer_words=[str(words.index(t)) for t in c['correctTokens']],explanation='',characterResource=character,skipLabel='跳过',skipCorrectText=c['correctSolutions'][0],correctFeedback='真厉害！')
lesson=f['data']['candidate_course']['lessons'][0]
lesson.update(id='skip-probe',title='Observed skip and review',questions=[q],reviewInterlude=dict(id='en-zh-l7-review-intro',afterQuestionID=q['id'],text='一起来复习一下之前你不太熟练的部分吧！'))
# No frozen full-course XP on a compressed one-question probe.
lesson.pop('settlement',None)
f['data']['evidence']=['projects/duolingo-web/evidence/'+x for x in ['english-secondary-actions-v1/secondary-reset-q0.json','english-secondary-actions-v1/secondary-q0-skipped.json','english-seventh-v1/seventh-review-intro.json','english-seventh-v1/seventh-review-q0-answer.json']]
f['data']['unknown']='One-question action probe, not full seventh lesson. Review bank order, external heart refresh, skip audio, scoring formula and full visual equality remain unverified.'
write(BASE/'fixture-reference-en-zh-skip-v1.json',f)
full=read(BASE/'frontend-english-seventh-v1.json')
requirements=[x for x in full['requirements'] if x['state'] in ['en-zh-l7-q0','en-zh-l7-q0-skipped','en-zh-l7-review-intro','en-zh-l7-review-q0','en-zh-l7-review-q0-feedback'] and not (x.get('field')=='settlement_mistake')]
write(BASE/'frontend-english-skip-v1.json',dict(revision='actual-skip-review-probe-v1',requirements=requirements))

contract=dict(revision='actual-skip-review-geometry-v2',requirements=requirements.copy())
for state,path in [('en-zh-l7-q0',OLD/'secondary-reset-q0.json')]:
    control=next(x for x in read(path)['visible'] if x.get('test')=='player-skip')
    assert control['enabled'] is True
    contract['requirements'].append(dict(id=state+'-skip-geometry',state=state,kind='element_geometry',element='skip',rect=control['rect'],tolerance_points=0,evidence=['projects/duolingo-web/evidence/english-secondary-actions-v1/secondary-reset-q0.json']))
write(BASE/'frontend-english-skip-v2.json',contract)
