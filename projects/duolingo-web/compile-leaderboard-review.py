"""Compile one actually accepted leaderboard practice instance, not its adaptive selector."""
import importlib.util,json
from pathlib import Path
from review_instance_compiler import compile_question,effect_resource
B=Path(__file__).resolve().parent;E=B/'evidence/english-leaderboard-practice-instance-v1';S=E/'source'
spec=importlib.util.spec_from_file_location('english',B/'compile-english-course.py');c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)
def read(n):return json.loads((S/(n+'.json')).read_text())
def effect(u):return effect_resource(c,u)
records=[]
for n in ['walk','after-speech']:
 d=read(n);records.extend((r['content'],o) for r,o in zip(d['session']['challenges'],d['observed']))
cards=[r for r in read('review')['visible'] if r['tag']=='DIV' and r['role']=='button'];assert len(records)==len(cards)==17
questions=[];speech=[]
for i,((raw,row),card) in enumerate(zip(records,cards)):
 if raw['type']=='speak':
  assert i==7 and not row.get('feedback') and card['text'].endswith(raw['prompt'])
  decline=read('speech-declined');assert '麦克风已关闭' in decline['snapshot'] and '将在 15 分钟后恢复' in decline['snapshot']
  speech.append(dict(id='leaderboard-review-speech',beforeQuestionID=f'leaderboard-review-q{i+1}',title=row['heading'],phrase=raw['prompt'],audioResource=c.resource(raw['tts'],'speech'),declineLabel='现在不做口语题',closedTitle='麦克风已关闭',closedBody='将在 15 分钟后恢复',resultReview=dict(title='朗读下面的句子',prompt=raw['prompt'],correctAnswer=raw['prompt'],declinedAnswer=raw['prompt'],audioResources=[])))
  continue
 # The historical helper assumes four distinct match cues. This instance only
 # observed three, so compile content separately and retain the partial evidence.
 matched=list(dict.fromkeys(m['src'] for m in row.get('media',[]) if m['src'].startswith('https://simg-ssl.duolingo.com/videos/sound/Match_Correct_')))
 content_row=dict(row,media=[m for m in row.get('media',[]) if m['src'] not in matched]) if raw['type']=='listenMatch' else row
 q=compile_question(c,effect,raw,content_row,card,f'leaderboard-review-q{i}')
 if raw['type']=='listenMatch':
  assert len(matched)==3
  q['matchedAudioResources']=[effect(u) for u in matched]
 if raw['type']=='assist':
  clips=list(dict.fromkeys(m['src'] for m in row['media'] if m['src'].startswith('https://d1vq87e9lcf771.cloudfront.net/')));assert len(clips)==1
  next(o for o in q['options'] if o['id']==q['answer'])['audioResource']=c.resource(clips[0],'speech')
 if '现在不做听力题' in row['before']:
  # Reuse the separately observed shared decline presentation, retaining the
  # current instance branch as unexecuted rather than claiming its replacement.
  template=json.loads((B/'fixture-reference-en-zh-general-practice-v4.json').read_text())['data']['candidate_course']['lessons'][0]['questions'][0]['listeningDecline']
  assert template['label']=='现在不做听力题'
  q['listeningDecline']=template
 questions.append(q)
assert len(questions)==16 and len(speech)==1
intro=read('after-speech')['interludes'];assert len(intro)==1 and intro[0]['index']==6
assert '完美！' in read('result')['snapshot']
lesson=dict(id='leaderboard-review-practice',title='英语练习',questions=questions,deferredSpeech=speech,reviewSpeechCard=7,interludes=[dict(id='leaderboard-review-intro',afterQuestionID='leaderboard-review-q13',text=intro[0]['decision']['text'])],settlement=[dict(id='leaderboard-review-result',kind='result',title='完美！',body='你练习全对，无错完成本单元',continueLabel='继续',secondaryLabel='回顾本单元',retryLabel='重新练习')])
fixture=dict(provenance=dict(source='Actual sequential leaderboard entry instance; 16 accepted questions plus one speech declined; no future session read',evidence=[str(E.relative_to(B.parents[1]))],unknown='Adaptive selection, normal speech grading, XP/rewards, fourth match cue not observed, current listening-decline replacement unexecuted (shared presentation reused from prior observed general practice) and acoustic equality; explicit fixture is not default selection policy'),data=dict(candidate_course=dict(id='duolingo-leaderboard-review-instance',title='英语练习',speechLanguage='en',interfaceLanguage='zh',mistakeHeartCost=0,lessons=[lesson])))
for name,value in [('fixture-reference-en-zh-leaderboard-review-v1.json',fixture),('reference-assets-en-zh-leaderboard-review-v1.json',list(c.resources.values()))]:(B/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'graded':len(questions),'speech_declined':len(speech),'cards':len(cards),'resources':len(c.resources)}))
