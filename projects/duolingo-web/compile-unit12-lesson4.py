"""Compile fourth-lesson visible UI, executed answers and original play receipts.

Current-character metadata contains only visible actor/resource identity, never
future answers. Keyboard mode is an executed branch, not inferred from tiles.
"""
import argparse,importlib.util,json,re
from pathlib import Path
from review_instance_compiler import effect_resource
B=Path(__file__).resolve().parent;E=B/'evidence/english-unit12-lesson4-v1/source'
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out-dir',required=True);O=Path(p.parse_args().out_dir);O.mkdir(parents=True,exist_ok=False)
spec=importlib.util.spec_from_file_location('english',B/'compile-english-course.py');c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)
read=lambda name:json.loads((E/(name+'.json')).read_text())
def heading(s,level=1):return re.search(r'heading "([^"\n]+)" \[level='+str(level)+r'\]',s).group(1)
def speech(events):return list(dict.fromkeys(e['src'] for e in events if e['src'].startswith('https://d1vq87e9lcf771.cloudfront.net/')))
def background(s):return [re.fullmatch(r'url\("(https:[^"]+)"\)',x['backgroundImage']).group(1) for x in s['background_media']]
# Full semantic inventory includes review cards below the viewport; actions
# intersecting the viewport alone omit the last two cards.
cards=[x['name'] for x in read('settlement-review')['control_inventory'] if x['explicit_role']=='button' and x['name'] and x['name'] not in ['回顾本单元','继续']];assert len(cards)==18
qs=[];oral=[]
for i in range(18):
 before=read('q15-wordbank' if i==15 else f'q{i}-before');snap=before['snapshot']
 assert before['capture_state_consistent']
 source=next(x['test'].split('challenge-')[1] for x in before['visible'] if (x.get('test')or'').startswith('challenge '))
 title,_,prompt=cards[i].partition('\n');presentation=dict(title=title,prompt=prompt,correctAnswer='',audioResources=[])
 if i==10:
  phrase=before['rendered_text_groups'][0]['text'];assert phrase=='Have a seat here.'
  assert '麦克风已关闭' in read('q10-decline')['snapshot']
  clips=speech(read('q9-next')['played'][len(read('q9-answer')['played']):]);assert len(clips)==1
  character=read('q10-current-character')['content']['character'];key=c.resource(character['image']['svg'],'image')
  oral.append(dict(id='unit12-speech',beforeQuestionID='unit12-q11',title=heading(snap),phrase=phrase,audioResource=c.resource(clips[0],'speech'),characterResource=key,declineLabel='现在不做口语题',closedTitle='麦克风已关闭',closedBody='将在 15 分钟后恢复',resultReview=dict(presentation,correctAnswer=phrase,declinedAnswer=phrase)));continue
 accepted=read(f'q{i}-answer');feedback=read(f'q{i}-feedback');assert heading(feedback['snapshot'],2)
 q=dict(id=f'unit12-q{i}',prompt=heading(snap),sourceType=source,sourceLanguage='zh' if i>=15 else 'en',explanation='',newWord='新单词' in snap,correctFeedback=heading(feedback['snapshot'],2),correctFeedbackAudioResource=effect_resource(c,'https://d35aaqx5ub95lt.cloudfront.net/sounds/37d8f0b39dcfe63872192c89653a93f6.mp3'),correctFeedbackAudioVolume=0.35)
 for indicator in ['新词形','挑战题']:
  if indicator in snap:q['indicator']=indicator
 prior=[] if i==0 else read('q10-next' if i==11 else 'hard-next' if i==15 else f'q{i-1}-next')['played']
 clips=speech(accepted['played'][len(prior):])
 # Prompt speech may already occur in the preceding Continue receipt.
 previous=[] if i==0 else read('q9-answer' if i==11 else 'q14-answer' if i==15 else f'q{i-1}-answer')['played']
 prompt_clips=speech(prior[len(previous):])
 if source in ['assist','select']:
  acts=[x for x in before['actions'] if x['role']=='radio'];options=[]
  for j,x in enumerate(acts):
   text=re.sub(r'^\d\s*|\s*\d$', '',x['name']).strip();options.append(dict(id=str(j),text=text))
  chosen=accepted['chosen'][0]['name'];chosen=re.sub(r'^\d\s*|\s*\d$','',chosen).strip()
  q.update(kind='choice',options=options,answer=next(x['id'] for x in options if x['text']==chosen));presentation['correctAnswer']=chosen
  if source=='select':
   urls=background(before);assert len(urls)==len(options)
   for o,u in zip(options,urls):o['imageResource']=c.resource(u,'image')
  else:q['hint']={2:'食物',7:'请坐',9:'冰箱'}[i]
  if clips:next(x for x in options if x['id']==q['answer'])['audioResource']=c.resource(clips[0],'speech')
 else:
  bank=[a['name'] for a in before['actions'] if a.get('test') and 'challenge-tap-token' in a['test']]
  assert bank
  words=[dict(id=f'word-{j}',text=t) for j,t in enumerate(bank)]
  answer=accepted['value'].split() if i==14 else [x['name'] for x in accepted['chosen']]
  q.update(kind='word_tiles',words=words,answer_words=[next(w['id'] for w in words if w['text']==t) for t in answer])
  presentation['correctAnswer']=''.join(answer) if source=='translate' and i<15 else ' '.join(answer)
  if source=='translate':q['hint']=before['rendered_text_groups'][0]['text']
  if i==3:
   q.update(contextExamples=[x['text'] for x in before['rendered_text_groups'][:2]],contextHighlights=['Mexico','bathroom'],completionPrefix='Your salad is in the ',completionSuffix='.')
  if i==5:
   q.update(completionPrefix='Oh, your ',completionSuffix=' is in the kitchen!',explanation='哦，你的猫在厨房里！')
   u=next(m['src'] for m in before['media'] if '/images/b2be3c2b9cc33a85213c4cd08573effc' in (m.get('src')or''));q['promptImageResource']=c.resource(u,'image')
  if i==14:
   assert accepted['value']=='two bathrooms' and '太棒了！' in accepted['snapshot']
   q.update(keyboardAnswer=accepted['value'],keyboardPrompt='键入你听到的内容',explanation='两个洗手间')
  if i>=15:q.update(keyboardAnswer=' '.join(answer),keyboardPrompt=q['prompt'])
  if prompt_clips:q['audioResource']=c.resource(prompt_clips[0],'speech')
  if i==12:
   character=read('q12-current-character')['content']['character'];q['characterResource']=c.resource(character['image']['svg'],'image')
 q['resultReview']=presentation;qs.append(q)
assert len(qs)==17 and len(oral)==1
result=read('settlement-current');art=next(m for m in result['media'] if m['tag'].lower()=='svg' and m.get('svg'));name='en-unit12-lesson4-result-observed-frame';(O/(name+'.svg')).write_text(art['svg']);c.resources[name]=dict(name=name,url='https://www.duolingo.com/lesson',kind='home',source_file=name+'.svg',inline_svg=True,render_width=art['rect'][2],render_height=art['rect'][3])
settlement=[dict(id='result',kind='result',title='完美！',body='你练习全对，无错完成本单元',continueLabel='继续',secondaryLabel='回顾本单元',experience=15,observedAccuracy=100,observedMistakes=0,accuracyLabel='超级棒',artResource=name)]
icons=[m for m in result['media'] if m['tag']=='IMG'];assert len(icons)==2
for field,icon in zip(['experienceIconResource','accuracyIconResource'],icons):
 r=c.resource(icon['src'],'home');c.resources[r].update(render_width=icon['rect'][2],render_height=icon['rect'][3]);settlement[0][field]=r
achievement=read('after-result');assert '神射手成就等级已提升！' in achievement['snapshot'] and '第 3 级' in achievement['snapshot'];u=background(achievement);assert len(u)==1
r=c.resource(u[0],'home');c.resources[r].update(render_width=150,render_height=186.75)
settlement += [dict(id='achievement',kind='achievement',title='神射手成就等级已提升！',body='完成了 5 个单元，而且完全没有犯错',levelLabel='第 3 级',artResource=r,continueLabel='继续',secondaryLabel='回顾本单元'),dict(id='profile',kind='profile',title='来创建你的个人档案吧！',body='创建档案就能保存学习进度，随时都可以继续免费学习后续内容。',continueLabel='稍后再说',secondaryLabel='创建档案')]
assert '来创建你的个人档案吧！' in read('after-achievement')['snapshot']
home=read('home-after');assert all(t in home['snapshot'] for t in ['155','Lesson 5 of 6','青铜等级'])
prior_home=json.loads((B/'fixture-reference-en-zh-unit12-lesson3-v1.json').read_text())['data']['candidate_course']['lessons'][0]['observedHomeSnapshot']
lesson=dict(id='unit12-home-4',title='描述你的家居布局',questions=qs,deferredSpeech=oral,interludes=[dict(id='unit12-hard-intro',afterQuestionID='unit12-q14',text='哎哟不错哦！要不要玩点刺激的？')],settlement=settlement,observedHomeSnapshot=dict(prior_home,completedLessons=6,gems=155),completionAudioResource=effect_resource(c,'https://d35aaqx5ub95lt.cloudfront.net/sounds/2aae0ea735c8e9ed884107d6f0a09e35.mp3'),completionAudioVolume=0.5)
fixture=dict(data=dict(candidate_course=dict(id='duolingo-en-zh-unit12-home4-instance',title=lesson['title'],interfaceLanguage='zh',speechLanguage='en',lessons=[lesson])),provenance=dict(source='Actual visible UI and accepted click/typed answers; original current actor/renderer identity only; no hidden answer keys.',unknown='Unobserved actors/voices, alternate answers, normal oral grading, slow speech, pixels and source acoustic equality remain pending.155gem cohort observed, cause of change unknown.15XP100% is this source instance.'))
(O/'unit12-home-4.json').write_text(json.dumps(fixture,ensure_ascii=False,indent=2)+'\n');(O/'resources.json').write_text(json.dumps(list(c.resources.values()),ensure_ascii=False,indent=2)+'\n')
print(json.dumps(dict(questions=len(qs),oral=len(oral),resources=len(c.resources))))
