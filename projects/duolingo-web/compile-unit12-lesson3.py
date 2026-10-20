"""Compile the executed third lesson from visible UI and actual play receipts.

No hidden answer keys, network challenge payload, synthetic voice, or inferred
character identity. Unknown audio/character branches remain absent and pending.
"""
import argparse,importlib.util,json,re
from pathlib import Path
from review_instance_compiler import effect_resource
B=Path(__file__).resolve().parent;E=B/'evidence/english-unit12-lesson3-v1/source'
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out-dir',required=True);O=Path(p.parse_args().out_dir);O.mkdir(parents=True,exist_ok=False)
spec=importlib.util.spec_from_file_location('english',B/'compile-english-course.py');c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)
def read(name):return json.loads((E/(name+'.json')).read_text())
def heading(s,level=1):return re.search(r'heading "([^"\n]+)" \[level='+str(level)+r'\]',s).group(1)
def speech(events):return list(dict.fromkeys(e['src'] for e in events if e['src'].startswith('https://d1vq87e9lcf771.cloudfront.net/')))
def res(url):return c.resource(url,'speech')
review=read('settlement-review');cards=[a['name'] for a in review['actions'] if a['role']=='button' and a['name'] not in ['','回顾本单元','继续']];assert len(cards)==16
# These accepted answers are the actual clicked labels, checked below against
# operation receipts (q0 and q1 were recorded before the reusable answer helper).
answers={0:['厨房','干净','吗'],1:['披萨','在','桌子','上'],3:['别','担心','猫','很','干净'],5:['couch'],7:['the','couch'],9:['the','kitchen'],10:['Your','couch','is','big'],11:['table'],12:['couch'],14:['Here','is','my','couch']}
# Boundaries are cumulative observation logs. They do not imply source acoustic equality.
qs=[];speech_rows=[]
for i in range(16):
 before=read('unit12-lesson3-first-question' if i==0 else f'q{i}-before');snap=before['snapshot'];assert i==0 or before['capture_state_consistent']
 source=next(x['test'].split('challenge-')[1] for x in before['visible'] if (x.get('test')or'').startswith('challenge '))
 title,_,prompt=cards[i].partition('\n');presentation=dict(title=title,prompt=prompt,correctAnswer='',audioResources=[])
 if i==2:
  clips=speech(read('q2-decline')['played'][len(read('q1-answer')['played']):]);assert len(clips)==1
  phrase=before['rendered_text_groups'][0]['text'];assert phrase=='Oh, the kitchen is clean!'
  presentation.update(correctAnswer=phrase,declinedAnswer=phrase)
  speech_rows.append(dict(id='unit12-speech',beforeQuestionID='unit12-q3',title=heading(snap),phrase=phrase,audioResource=res(clips[0]),declineLabel='现在不做口语题',closedTitle='麦克风已关闭',closedBody='将在 15 分钟后恢复',resultReview=presentation));continue
 feedback=read('review-q0-feedback' if i==0 else f'q{i}-feedback')['snapshot'];assert 'heading' in feedback
 q=dict(id=f'unit12-q{i}',prompt=heading(snap),sourceType=source,sourceLanguage='en',explanation='',newWord='新单词' in snap,correctFeedback=heading(feedback,2),correctFeedbackAudioResource=effect_resource(c,'https://d35aaqx5ub95lt.cloudfront.net/sounds/37d8f0b39dcfe63872192c89653a93f6.mp3'),correctFeedbackAudioVolume=0.35)
 if '新词形' in snap:q['indicator']='新词形'
 if source=='match':
  acts=[a for a in before['actions'] if a['role']=='button' and a['name'] not in ['','检查','跳过']];assert len(acts)==10
  left=[a['name'].split('\n',1)[1] for a in acts[:5]];right=[a['name'].split('\n',1)[1] for a in acts[5:]]
  # Actual pairs were clicked in left visual order, not answer-key order.
  pair_right=["I'm good",'skirt','want','store','table'] if i==13 else ['cute','three','spider','come in','couch']
  pairs=[];effects=[]
  for j,(l,r) in enumerate(zip(left,pair_right)):
   row=read(f'q{i}-pair{j}');prior=row.get('before_event_count',len(read('q12-next')['played']));assert row['after_left_event_count']==prior
   events=row['played'][prior:];clips=speech(events);assert len(clips)==1
   fx=list(dict.fromkeys(e['src'] for e in events if '/videos/sound/Match_Correct_' in e['src']));assert len(fx)==1
   assert all(e['volume']==1 for e in events if e['src']==fx[0])
   pairs.append(dict(id=str(j),left=l,right=r,audioResource=res(clips[0])));effects.append(effect_resource(c,fx[0]))
  q.update(kind='matching',pairs=pairs,rightOrder=[next(p['id'] for p in pairs if p['right']==t) for t in right],matchedAudioResources=effects)
  presentation['correctAnswer']='All pairs matched';presentation['audioResources']=[p['audioResource'] for p in pairs]
 elif source in ['assist','dialogue']:
  options=[dict(id=str(j),text=re.sub(r'^\d\s*','',a['name'])) for j,a in enumerate(a for a in before['actions'] if a['role']=='radio')]
  accepted=read(f'q{i}-answer');chosen=accepted['chosen'][0]['name'];q.update(kind='choice',options=options,answer=next(o['id'] for o in options if o['text']==re.sub(r'^\d\s*','',chosen)))
  q['hint']={4:'桌子',6:'沙发',8:'Where is the hat?'}[i]
  presentation['correctAnswer']=next(o['text'] for o in options if o['id']==q['answer'])
  if i in [4,6]:
   start=len(read(f'q{i-1}-next' if i>4 else 'q3-next')['played']);clips=speech(accepted['played'][start:]);assert len(clips)==1
   next(o for o in options if o['id']==q['answer'])['audioResource']=res(clips[0])
  else:
   clips=speech(read('q8-replay')['played']);q['audioResource']=res(next(u for u in reversed(clips) if '/vikramen/' in u))
   avatars=[m['src'] for m in before['media'] if '/world-characters/avatars/' in (m.get('src') or '')];assert len(avatars)==2
   q['dialogueAvatars']=[c.resource(u,'avatar') for u in avatars]
 else:
  assert i in answers
  bank=[a['name'] for a in before['actions'] if a['role']=='button' and a.get('test','') and 'challenge-tap-token' in a['test']]
  words=[dict(id=f'word-{j}',text=t) for j,t in enumerate(bank)];assert words
  if i not in [0,1]:assert [x['name'] for x in read(f'q{i}-answer')['chosen']]==answers[i]
  q.update(kind='word_tiles',words=words,answer_words=[next(w['id'] for w in words if w['text']==t) for t in answers[i]])
  presentation['correctAnswer']=''.join(answers[i]) if source=='translate' else ' '.join(answers[i])
  if source=='translate':q['hint']=before['rendered_text_groups'][0]['text']
  if i in [5,11]:
   q['contextHighlights']=['France','table'] if i==5 else ['Tokyo','couch']
   q['contextExamples']=[x['text'] for x in before['rendered_text_groups'][:2]];assert len(q['contextExamples'])==2
   q.update(completionPrefix='My hat is on the ' if i==5 else 'Your hat is on the ',completionSuffix='.')
  elif i in [7,9]:q.update(example=before['rendered_text_groups'][0]['text'],completionPrefix='Here is ',completionSuffix='!')
  elif i==12:
   q.update(completionPrefix='I like my new ',completionSuffix='!')
   u=next(m['src'] for m in before['media'] if '/images/e201ab2962707879b7eacea8bde72fad' in (m.get('src') or ''));q['promptImageResource']=c.resource(u,'image')
  if i==0:
   q.update(skipLabel='跳过',skipCorrectText='厨房干净吗？',reviewWordOrder=[next(w['id'] for w in words if w['text']==t) for t in ['干净','厨房','食物','吗']])
  # Keep only voices actually observed between this prompt and its accepted action.
  if i in [0,1,3,7,9,10,14]:
   urls={0:'vikramen/9a25122e375e9f8849afb1348b0e176a',1:'beaen/d2d357d7d690e635a18a0c24098bc8ba',3:'linen/88040a443f767f0fdcb424bd2df57710',7:'oscaren/e778140b95bb4b0f45a5e7b2a80a91ee',9:'linen/140818b59904f11bc915a11066a753af',10:'harrison/c496a70015112d464ed6c6cadc7ee18c',14:'harrison/55bd3deab9425f5e6928ed58c8136aca'}
   url='https://d1vq87e9lcf771.cloudfront.net/'+urls[i]
   all_events=read('settlement-review-open')['played'];assert url in [e['src'] for e in all_events]
   q['audioResource']=res(url)
   if i in [7,9]:
    q['exampleAudioResource']=q['audioResource'];events=read(f'q{i}-answer')['played'];start=next(j for j,e in enumerate(events) if e['src']==url);clips=speech(events[start:]);assert len(clips)==3
    for w,u in zip(words,clips[1:]):w['audioResource']=res(u)
 q['resultReview']=presentation;qs.append(q)
assert len(qs)==15 and len(speech_rows)==1
result=read('settlement-current');art=next(m for m in result['media'] if m['tag'].lower()=='svg' and m.get('svg'));name='en-unit12-lesson3-result-observed-frame';(O/(name+'.svg')).write_text(art['svg']);c.resources[name]=dict(name=name,url='https://www.duolingo.com/lesson',kind='home',source_file=name+'.svg',inline_svg=True,render_width=art['rect'][2],render_height=art['rect'][3])
icon=next(m for m in read('q5-before')['media'] if m['tag'].lower()=='svg' and m['rect']==[300,121,32,32]);icon_name='en-pattern-context-indicator';(O/(icon_name+'.svg')).write_text(icon['svg']);c.resources[icon_name]=dict(name=icon_name,url='https://www.duolingo.com/lesson',kind='home',source_file=icon_name+'.svg',inline_svg=True,render_width=32,render_height=32)
settlement=[dict(id='result',kind='result',title='完美！',body='你练习全对，无错完成本单元',continueLabel='继续',secondaryLabel='回顾本单元',experience=15,observedAccuracy=100,observedMistakes=0,accuracyLabel='超级棒',artResource=name)]
icons=[m for m in result['media'] if m['tag']=='IMG'];assert len(icons)==2
for field,icon in zip(['experienceIconResource','accuracyIconResource'],icons):
 r=c.resource(icon['src'],'home');c.resources[r].update(render_width=icon['rect'][2],render_height=icon['rect'][3]);settlement[0][field]=r
reward=read('after-result');assert '你又获取了一颗红心' in reward['snapshot'];hearts=[m for m in reward['media'] if m['tag']=='IMG'];assert len(hearts)==5
settlement += [dict(id='heart-reward',kind='practice_heart',title='你又获取了一颗红心！',body='学习新单元需要红心！',continueLabel='继续',secondaryLabel='回顾本单元',heartResources=[c.resource(m['src'],'home') for m in hearts]),dict(id='profile',kind='profile',title='来创建你的个人档案吧！',body='创建档案就能保存学习进度，随时都可以继续免费学习后续内容。',continueLabel='稍后再说',secondaryLabel='创建档案')]
assert '来创建你的个人档案吧！' in read('after-heart-reward')['snapshot']
lesson=dict(id='unit12-home-3',title='描述你的家居布局',questions=qs,deferredSpeech=speech_rows,settlement=settlement,reviewInterlude=dict(id='unit12-review-intro',afterQuestionID='unit12-q15',text='一起来复习一下之前你不太熟练的部分吧！'),completionAudioResource=effect_resource(c,'https://d35aaqx5ub95lt.cloudfront.net/sounds/2aae0ea735c8e9ed884107d6f0a09e35.mp3'),completionAudioVolume=0.5)
after=read('home-after');assert all(t in after['snapshot'] for t in ['505','Lesson 4 of 6','青铜等级'])
prior=json.loads((B/'fixture-reference-en-zh-unit12-lesson2-v1.json').read_text())['data']['candidate_course']['lessons'][0]['observedHomeSnapshot']
lesson['observedHomeSnapshot']=dict(prior,completedLessons=5)
fixture=dict(data=dict(candidate_course=dict(id='duolingo-en-zh-unit12-home3-instance',title=lesson['title'],interfaceLanguage='zh',speechLanguage='en',lessons=[lesson])),provenance=dict(source='Executed visible UI, accepted answers, declined oral, skipped first/review, actual original play calls. Not a network answer key.',unknown='Character animations, unobserved voices, alternatives, full pixels, source acoustic output and later locked lessons remain pending. Source-specific 15XP/100%, not a scoring formula.'))
(O/'unit12-home-3.json').write_text(json.dumps(fixture,ensure_ascii=False,indent=2)+'\n');(O/'resources.json').write_text(json.dumps(list(c.resources.values()),ensure_ascii=False,indent=2)+'\n')
print(json.dumps(dict(questions=len(qs),oral=len(speech_rows),resources=len(c.resources))))
