"""Compile the executed level review; skip unsubmitted coverage boundaries, not attempts."""
import importlib.util
import json
from pathlib import Path
from review_instance_compiler import compile_question, effect_resource
BASE=Path(__file__).resolve().parent
EV=BASE/'evidence/english-home-frontier-v1/source'
spec=importlib.util.spec_from_file_location('english',BASE/'compile-english-course.py')
c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)
def read(name):return json.loads((EV/name).read_text())
def effect(url):return effect_resource(c,url)
records=[]
for name in ['lesson-current-walk.json','lesson-after-speech.json','lesson-after-reverse.json']:
    data=read(name)
    for raw,row in zip(data['session']['challenges'],data['observed']):
        if row.get('feedback') or raw['content']['type']=='speak':records.append((raw['content'],row))
cards=[r for r in read('lesson-review-open.json')['visible'] if r['tag']=='DIV' and r['role']=='button']
assert len(records)==len(cards)==13
questions=[];speeches=[]
for i,((raw,row),card) in enumerate(zip(records,cards)):
    title,_,prompt=card['text'].partition('\n')
    if raw['type']=='speak':
        assert i==1 and raw['prompt']==prompt=='Thank you.'
        speeches.append(dict(id='level-review-speech',beforeQuestionID='level-review-q2',title=row['heading'],phrase=prompt,
            audioResource=c.resource(raw['tts'],'speech'),declineLabel='现在不做口语题',closedTitle='麦克风已关闭',closedBody='将在 15 分钟后恢复',
            resultReview=dict(title=title,prompt=prompt,correctAnswer=prompt,declinedAnswer=prompt,audioResources=[])))
    else:questions.append(compile_question(c,effect,raw,row,card,f'level-review-q{i}'))
assert len(questions)==12 and sum(q['sourceType']=='completeReverseTranslation' for q in questions)==4
lesson=dict(id='level-review-1',title='提供或接受饮料',questions=questions,deferredSpeech=speeches,
    entry=dict(id='level-review-entry',title='来复习一下这个等级，完成后有惊喜哦！',startLabel='开始挑战 +20 经验',declineLabel='下次再说'),
    settlement=[dict(id='level-review-result',kind='result',title='完美！',body='你练习全对，无错完成本单元',continueLabel='继续',secondaryLabel='回顾本单元')])
parent=json.loads((BASE/'fixture-reference-en-zh-v11.json').read_text())
fixture=json.loads(json.dumps(parent))
lesson['id']='lesson-8'
lesson['settlement'] += [
    dict(id='eighth-score',kind='score_progress',title='离提升你的英语分数又近了一步！',levelLabel='5',body='5 → 6',continueLabel='继续'),
    dict(id='eighth-boost',kind='boost',title='到手一个经验宝！',body='恭喜你完成了这个等级！接下来 15 分钟里，做单元练习可得双倍经验！',continueLabel='继续',secondaryLabel='回顾本单元'),
    dict(id='eighth-legendary',kind='legendary',title='来向我们展示你的传奇实力吧',body='完成这个超硬核挑战，晋升到传奇等级！',continueLabel='不，谢谢',secondaryLabel='开始 +80 经验'),
    dict(id='eighth-profile',kind='profile',title='来创建你的个人档案吧！',body='创建档案就能保存学习进度，随时都可以继续免费学习后续内容。',continueLabel='稍后再说',secondaryLabel='创建档案')]
fixture['data']['candidate_course']['lessons'].append(lesson)
fixture['data']['candidate_course']['pathNodes'][1]['lessonIDs'].append('lesson-8')
fixture['provenance']=dict(source='Original seven lessons retained; observed fourth unit of second level appended as lesson8',evidence=['projects/duolingo-web/evidence/english-home-frontier-v1/README.md'],unknown='Adaptive selection, normal oral, stable reward formulas and full post-result pixels')
assert fixture['data']['candidate_course']['lessons'][:7]==parent['data']['candidate_course']['lessons']
(BASE/'fixture-reference-en-zh-v12.json').write_text(json.dumps(fixture,ensure_ascii=False,indent=2)+'\n')
(BASE/'reference-assets-en-zh-eighth-v2.json').write_text(json.dumps(list(c.resources.values()),ensure_ascii=False,indent=2)+'\n')
print(json.dumps(dict(questions=len(questions),cards=len(cards),resources=len(c.resources),main_lessons=8)))
