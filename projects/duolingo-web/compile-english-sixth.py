"""Compile the executed sixth double-decline trajectory, not a normal-path guess.

The fixture extends the curriculum for explicit execution. Default stays v6
until normal/declined continuations are separated and verified on the source.
"""
import copy
import importlib.util
import json
import re
from pathlib import Path

BASE=Path(__file__).resolve().parent
EV=BASE/'evidence/english-sixth-v1'
OLD=BASE/'evidence/english-listening-decline-v1'
CHAR=BASE/'evidence/english-character-render-v1'
def read(p): return json.loads(p.read_text())
def write(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
def heading(s,level):return re.search(r'heading "([^"\n]+)" \[level='+str(level)+r'\]',s).group(1)
spec=importlib.util.spec_from_file_location('english',BASE/'compile-english-course.py');compiler=importlib.util.module_from_spec(spec);spec.loader.exec_module(compiler)
fixture=read(BASE/'fixture-reference-en-zh-v6.json')
for row in read(BASE/'reference-assets-en-zh-v6.json')+read(BASE/'reference-assets-english-character-probe.json'):compiler.resources[row['name']]=row
session=read(CHAR/'sixth-session.json')['session']
q0=read(BASE/'fixture-english-character-probe.json')['data']['candidate_course']['lessons'][0]['questions'][0];q0['id']='en-zh-l6-q0'
q1row=read(OLD/'q1-answer.json');assert not q1row['rejected']
c=session['challenges'][1]['content'];row=dict(q1row,heading=heading(q1row['before'],1),word_bank=q1row['choices'],actions=[dict(word=a['word']) for a in q1row['clicks']])
q1=compiler.compile_questions(dict(session,challenges=[session['challenges'][1]]),{1:row},{},prefix='en-zh-l6-q')[0];q1['correctFeedback']=heading(q1row['feedback'],2)
prefix=read(BASE/'fixture-listening-decline.json')['data']['candidate_course']['lessons'][0]['questions']
questions=[q0,q1]
for q,suffix in zip(prefix,['listening','adaptive','fill']):
 q=copy.deepcopy(q);q['id']='en-zh-l6-'+suffix;questions.append(q)
sugar=read(BASE/'fixture-feedback-actions.json')['data']['candidate_course']['lessons'][0]['questions'][0];sugar['id']='en-zh-l6-sugar';questions.append(sugar)
for number in [6,7,8,9,10,11,12,13,14,15]:
 stem=f'english-sixth-q{number}'+('-adaptive' if number==9 else '')
 if number==7:
  before=read(EV/(stem+'-before.json'))['snapshot'];feedback=read(EV/(stem+'-feedback.json'))['snapshot'];answer=read(EV/'q7-input-action.json')['input']
  assert 'textbox "Good morning, coffee with , please." [disabled]: milk' in feedback
 else:
  observed=read(EV/(stem+'-answer.json'));assert observed['rejected'] is False
  before=observed['before'];feedback=observed['feedback'];answer=observed.get('input')
 q=dict(id=f'en-zh-l6-q{number}',prompt=heading(before,1),explanation='',correctFeedback=heading(feedback,2))
 if number in [7,10]:
  c=session['challenges'][6 if number==7 else 9]['content'];tokens=c['displayTokens'];blanks=[i for i,t in enumerate(tokens) if t['isBlank']];assert len(blanks)==1
  i=blanks[0];assert answer==tokens[i]['text']
  q.update(kind='text_entry',sourceType='completeReverseTranslation',hint=c['prompt'],answer=answer,completionPrefix=''.join(t['text'] for t in tokens[:i]),completionSuffix=''.join(t['text'] for t in tokens[i+1:]))
  # Junior/Oscar were independently inspected in these actual source PNGs.
  q['characterResource']=compiler.resource(c['character']['image']['svg'],'image')
 elif number>=13:
  prior={13:'english-sixth-after-entry.json',14:'english-sixth-after-q13.json',15:'english-sixth-after-q14.json'}[number]
  snapshot=read(EV/prior)['after'];hint=re.findall(r'^\s*- text: (.+)$',snapshot,re.M);assert len(hint)==1
  assert '挑战题' in before
  q.update(kind='text_entry',sourceType='translate',hint=hint[0],answer=answer,indicator='挑战题')
 else:
  bank=observed['choices'];words,ids=compiler.compile_word_bank([dict(text=t) for t in bank],bank,[a['word'] for a in observed['clicks']]);assert len(observed['prompts'])==1
  q.update(kind='word_tiles',sourceType='translate',hint=observed['prompts'][0],words=words,answer_words=ids,sourceLanguage='en' if number!=8 else 'zh')
 questions.append(q)
assert len(questions)==16  # 15 graded + ungraded listening-decline stage.
speech=session['challenges'][8]['content']
assert speech['prompt']=='coffee with sugar'
assert '麦克风已关闭' in read(EV/'english-sixth-q9-speech-declined.json')['snapshot']
assert '哎哟不错哦！要不要玩点刺激的？' in read(EV/'english-sixth-challenge-entry.json')['snapshot']
complete=read(EV/'completion-visual.json');assert complete['experience']==15 and complete['accuracy']==100
lesson=dict(id='lesson-6',title='第 2/4 单元',questions=questions,
 deferredSpeech=[dict(id='en-zh-l6-speech',beforeQuestionID='en-zh-l6-q9',title='朗读下面的句子',phrase=speech['prompt'],audioResource=compiler.resource(speech['tts'],'speech'),declineLabel='现在不做口语题',closedTitle='麦克风已关闭',closedBody='将在 15 分钟后恢复')],
 interludes=[dict(id='en-zh-l6-challenge-entry',afterQuestionID='en-zh-l6-q12',text='哎哟不错哦！要不要玩点刺激的？')],
 settlement=[dict(id='en-zh-l6-complete',kind='result',title=complete['title'],body=complete['body'],continueLabel='继续',secondaryLabel='回顾本单元',experience=15,observedAccuracy=100,observedMistakes=0,accuracyLabel='超级棒'),dict(id='en-zh-l6-profile',kind='profile',title='来创建你的个人档案吧！',body='创建档案就能保存学习进度，随时都可以继续免费学习后续内容。',continueLabel='稍后再说',secondaryLabel='创建档案')])
course=fixture['data']['candidate_course'];course['lessons'].append(lesson);course['pathNodes'][1]['lessonIDs'].append('lesson-6')
course['home']['progressSnapshots'].append(dict(course['home']['progressSnapshots'][-1],completedLessons=6,gems=510,leagueCountdown='14 小时'))
fixture['provenance']['source']+='; explicit sixth observed double-decline trajectory (not general adaptation)'
fixture['provenance']['evidence'] += [str(p.relative_to(BASE.parent.parent)) for p in [EV/'trajectory.json',EV/'completion-visual.json',EV/'english-sixth-home.json',OLD/'q1-answer.json',CHAR/'sixth-session.json']]
fixture['provenance']['unknown']='Sixth fixture executes the actually observed double-decline path only. Normal listening/speech continuations, timer recovery, grading variants, missing character/audio bindings, score rules and 1:1 visuals/audio remain unverified; default remains v6 until branch integration.'
write(BASE/'fixture-reference-en-zh-v7.json',fixture)
write(BASE/'reference-assets-en-zh-v7.json',list(compiler.resources.values()))
print('Compiled sixth observed path:',len(questions)-1,'graded, listening decline + deferred speech;',len(compiler.resources),'public resources')
