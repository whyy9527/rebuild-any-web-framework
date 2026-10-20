"""Compile the executed grocery instance, including its declined oral branch."""
import argparse
import importlib.util
import json
from pathlib import Path
from review_instance_compiler import compile_question, effect_resource
BASE=Path(__file__).resolve().parent
EV=BASE/'evidence/english-stage2-path-v1/source'
BUNDLE=BASE.parent/'education-swift/Sources/LingoSeed/Resources/Reference'
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out-dir');args=p.parse_args()
spec=importlib.util.spec_from_file_location('english',BASE/'compile-english-course.py')
c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)
def read(name):return json.loads((EV/name).read_text())
records=[];interludes=[]
for name in ['persistent-grocery-batch01.json','persistent-grocery-batch02.json','persistent-grocery-batch03.json']:
    d=read(name);raws={r['index']:r['content'] for r in d['session']['challenges']}
    events=[(r['index'],'question',r) for r in d['observed'] if r.get('feedback') or raws[r['index']]['type']=='speak']
    events += [(r['index'],'interlude',r) for r in d['interludes']]
    for index,kind,row in sorted(events,key=lambda x:x[0]):
        if kind=='interlude':
            messages=row['facts']['encouragement_messages'];assert len(messages)==1
            interludes.append(dict(id=f'grocery-encouragement-{len(interludes)}',afterQuestionID=f'grocery-q{len(records)-1}',text=messages[0]))
        else:records.append((raws[index],row))
cards=[r for r in read('persistent-grocery-review.json')['visible'] if r['tag']=='DIV' and r['role']=='button']
assert len(records)==len(cards)==11
questions=[];speeches=[]
for i,((raw,row),card) in enumerate(zip(records,cards)):
    if raw['type']=='speak':
        assert i==4 and raw['prompt']=='Is this store expensive?'
        title,_,prompt=card['text'].partition('\n');assert prompt==raw['prompt']
        speeches.append(dict(id='grocery-speech',beforeQuestionID='grocery-q5',title=row['heading'],phrase=prompt,
            audioResource=c.resource(raw['tts'],'speech'),declineLabel='现在不做口语题',closedTitle='麦克风已关闭',closedBody='将在 15 分钟后恢复',
            resultReview=dict(title=title,prompt=prompt,correctAnswer=prompt,declinedAnswer=prompt,audioResources=[])))
        continue
    q=compile_question(c,lambda url:effect_resource(c,url),raw,row,card,f'grocery-q{i}')
    q['newWord']='新单词' in row['before']
    if '挑战题' in row['before']:q['indicator']='挑战题'
    if raw['type']=='assist':
        clips=list(dict.fromkeys(m['src'] for m in row.get('media',[]) if m['src'].startswith('https://d1vq87e9lcf771.cloudfront.net/')))
        assert len(clips)==1
        next(o for o in q['options'] if o['id']==q['answer'])['audioResource']=c.resource(clips[0],'speech')
    questions.append(q)
assert len(questions)==10 and len(interludes)==2
review=read('persistent-grocery-review-fill.json')['snapshot']
assert '你的答案： This store is very nice. 正确答案： This store is very nice.' in review
profile=read('grocery-return-profile.json')
assert '来创建你的个人档案吧！' in profile['snapshot']
lesson=dict(id='stage2-grocery-1',title='购买食品杂货',questions=questions,deferredSpeech=speeches,interludes=interludes,
    settlement=[dict(id='grocery-result',kind='result',title='单元完成啦！',continueLabel='继续',secondaryLabel='回顾本单元',experience=15,observedAccuracy=100,observedMistakes=0,accuracyLabel='超级棒'),
        dict(id='grocery-profile',kind='profile',title='来创建你的个人档案吧！',body='创建档案就能保存学习进度，随时都可以继续免费学习后续内容。',continueLabel='稍后再说',secondaryLabel='创建档案')])
after=read('grocery-home-after.json')
assert all(t in after['snapshot'] for t in ['青铜等级','505','Lesson 2 of 5'])
league=next(m for m in after['media'] if '/images/leagues/' in (m.get('src') or ''))
resource=c.resource(league['src'],'home');c.resources[resource].update(render_width=70,render_height=50)
lesson['observedHomeSnapshot']=dict(completedLessons=2,gems=505,streak=1,leagueTitle='青铜等级',leagueLink='查看排行榜',leagueMessage='学个单元就能上本周排行榜，跟其他小伙伴一决高低！',leagueResource=resource,questTarget=10,questProgress=10)
fixture=dict(data=dict(candidate_course=dict(id='duolingo-en-zh-stage2-grocery-instance',title=lesson['title'],speechLanguage='en',interfaceLanguage='zh',lessons=[lesson])),
    provenance=dict(source='10 accepted current-renderer questions, 1 declined oral question, 2 encouragements, 11 actual result-review cards',evidence=['projects/duolingo-web/evidence/english-stage2-path-v1/README.md'],
        unknown='Adaptive question selection, normal oral grading, wrong answers, timer recovery, exact pixels and acoustic output remain unverified. Result15XP/100% is this observed instance, not a scoring formula.'))
out=Path(args.out_dir) if args.out_dir else None
if out:out.mkdir(parents=True,exist_ok=False)
for path,data in [(BUNDLE/'stage2-grocery-1.json',fixture),(BASE/'fixture-reference-en-zh-stage2-grocery-v1.json',fixture),(BASE/'reference-assets-en-zh-stage2-grocery-v1.json',list(c.resources.values()))]:
    (out/path.name if out else path).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(dict(questions=len(questions),speech=len(speeches),interludes=len(interludes),review_cards=len(cards),resources=len(c.resources))))
