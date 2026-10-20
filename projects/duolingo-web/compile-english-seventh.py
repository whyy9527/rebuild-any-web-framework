"""Compile the actual seventh trajectory, retaining unknown option1 audio.

API complements executed UI receipts; it does not replace adaptive ordering.
This extends the product curriculum, not a compressed component fixture.
"""
import copy
import importlib.util
import json
import re
from pathlib import Path
BASE=Path(__file__).resolve().parent
OLD=BASE/'evidence/english-secondary-actions-v1'
EV=BASE/'evidence/english-seventh-v1'
def read(p): return json.loads(p.read_text())
def write(p,d): p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
def heading(s,level): return re.search(r'heading "([^"\n]+)" \[level='+str(level)+r'\]',s).group(1)
spec=importlib.util.spec_from_file_location('english',BASE/'compile-english-course.py');c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)
for r in read(BASE/'reference-assets-en-zh-v7.json'): c.resources[r['name']]=r
session=read(OLD/'secondary-session.json')['session']['challenges']
fixture=read(BASE/'fixture-reference-en-zh-v7.json')
probe=read(BASE/'fixture-reference-en-zh-secondary-v3.json')['data']['candidate_course']['lessons'][0]['questions']
q0=read(BASE/'fixture-reference-en-zh-skip-v1.json')['data']['candidate_course']['lessons'][0]['questions'][0]
q0['audioResource']=c.resource(session[0]['content']['tts'],'speech')
review=read(EV/'seventh-review-q0-answer.json');q0['reviewWordOrder']=[next(w['id'] for w in q0['words'] if w['text']==t) for t in review['choices']]
questions=[q0]
def enrich(q,index,before,feedback):
    q=copy.deepcopy(q);q['id']=f'en-zh-l7-q{index}';q['correctFeedback']=heading(feedback,2)
    raw=session[index]['content']
    if raw.get('tts'): q['audioResource']=c.resource(raw['tts'],'speech')
    if raw.get('slowTts'): q['slowAudioResource']=c.resource(raw['slowTts'],'speech')
    if 'button "跳过"' in before: q['skipLabel']='跳过'
    return q
r=read(OLD/'secondary-keyboard-answer.json');questions.append(enrich(probe[0],1,r['before'],r['feedback']));questions[-1]['sourceObservationPhase']='empty'
def matching(index,path):
    r=read(path);assert not r['rejected']
    rights=re.findall(r'- button "[5-8] ([^"\n]+)"',r['before']);assert len(rights)==4
    pairs=[]
    for row in r['rows']:
        urls=list(dict.fromkeys(row['played_audio']));assert len(urls)==1
        pairs.append(dict(id=str(row['left_index']),left=str(row['left_index']+1),right=row['translation'],audioResource=c.resource(urls[0],'speech')))
    q=dict(id=f'en-zh-l7-q{index}',kind='matching',sourceType='listenMatch',prompt=heading(r['before'],1),pairs=pairs,rightOrder=[next(p['id'] for p in pairs if p['right']==t) for t in rights],explanation='',correctFeedback=heading(r['feedback'],2))
    # Decline affordance observed; its seventh-specific adaptive continuation unknown.
    q['listeningDecline']=dict(label='现在不做听力题',title='听力练习已关闭',body='将在 15 分钟后恢复')
    return q
questions.append(matching(2,OLD/'secondary-pairs.json'))
raw=session[3]['content'];m=read(BASE/'evidence/english-eighth-v1/retained-seventh-media.json')
ice=raw['tokens'][2]['tts'];assert any(x['src']==ice for x in m['media'])
assert raw['correctIndex']==1 and raw['solutionTranslation']=='不要冰，谢谢。'
r=read(OLD/'secondary-listen-isolation-feedback.json');assert 'radio "2" [checked]' in r['snapshot']
questions.append(dict(id='en-zh-l7-q3',kind='choice',sourceType='listenIsolation',prompt='选择音频填空',hint='No __, please.',options=[dict(id='0',text='1',imageResource='en-seventh-isolation-wave-1'),dict(id='1',text='2',imageResource='en-seventh-isolation-wave-2',audioResource=c.resource(ice,'speech'))],answer='1',audioResource=c.resource(raw['tts'],'speech'),characterResource=c.resource(raw['character']['image']['svg'],'image'),correctFeedback='好棒！',explanation='意思是： 不要冰，谢谢。'))
r=read(OLD/'secondary-harder-answer.json');questions.append(enrich(probe[1],4,r['before'],r['feedback']));questions[-1]['sourceObservationPhase']='empty'
questions.append(matching(5,EV/'seventh-q5-answer.json'))
for index,probeindex in [(6,2),(7,3)]:
    r=read(EV/f'seventh-q{index}-answer.json');questions.append(enrich(probe[probeindex],index,r['before'],r['feedback']))
for index in [8,9]:
    raw=session[index]['content'];r=read(EV/f'seventh-q{index}-answer.json');assert not r['rejected']
    q=dict(kind='word_tiles' if index==8 else 'text_entry',sourceType=raw['type'],prompt=heading(r['before'],1),explanation='')
    if index==8:
        q.update(hint=raw['prompt'],sourceLanguage='zh',words=[dict(id=str(i),text=v['text'],**({'audioResource':c.resource(v['tts'],'speech')} if v.get('tts') else {})) for i,v in enumerate(raw['choices'])],answer_words=[str(i) for i in raw['correctIndices']],keyboardAnswer=r['input'],keyboardPrompt=heading(r['before'],1))
    else:
        tokens=raw['displayTokens'];i=next(i for i,t in enumerate(tokens) if t['isBlank']);assert r['input']==tokens[i]['text']
        q.update(explanation='意思是： '+raw['solutionTranslation'],answer=r['input'],completionPrefix=''.join(t['text'] for t in tokens[:i]),completionSuffix=''.join(t['text'] for t in tokens[i+1:]))
    if raw.get('character'): q['characterResource']=c.resource(raw['character']['image']['svg'],'image')
    questions.append(enrich(q,index,r['before'],r['feedback']))
for suffix,name,rawindex in [('q10-inserted','seventh-inserted-answer.json',None),('q11','seventh-q11-answer.json',11),('q12','seventh-q12-answer.json',12),('q13-replacement','seventh-q13-replacement-answer.json',None),('q14','seventh-q14-answer.json',14)]:
    r=read(EV/name);assert not r['rejected']
    q=dict(id='en-zh-l7-'+suffix,prompt=heading(r['before'],1),explanation='',correctFeedback=heading(r['feedback'],2))
    if suffix in ['q12','q14']:
        raw=session[rawindex]['content'];tokens=raw['displayTokens'];i=next(i for i,t in enumerate(tokens) if t['isBlank'])
        q.update(kind='text_entry',sourceType=raw['type'],answer=tokens[i]['text'],completionPrefix=''.join(t['text'] for t in tokens[:i]),completionSuffix=''.join(t['text'] for t in tokens[i+1:]),characterResource=c.resource(raw['character']['image']['svg'],'image'))
        if suffix=='q14':q.update(hint=raw['prompt'],keyboardAnswer=r['input'],keyboardPrompt=heading(r['before'],1))
        else:q['explanation']='意思是： '+raw['solutionTranslation']
        for key,out in [('tts','audioResource'),('slowTts','slowAudioResource')]:
            if raw.get(key):q[out]=c.resource(raw[key],'speech')
    else:
        words,ids=c.compile_word_bank([dict(text=t) for t in r['choices']],r['choices'],[a['word'] for a in r['clicks']]);q.update(kind='word_tiles',sourceType='translate',sourceLanguage='en',hint=r['prompts'][0],words=words,answer_words=ids)
        if rawindex is not None:
            raw=session[rawindex]['content'];assert q['hint']==raw['prompt'];q.update(characterResource=c.resource(raw['character']['image']['svg'],'image'),audioResource=c.resource(raw['tts'],'speech'))
    if 'button "跳过"' in r['before']:q['skipLabel']='跳过'
    questions.append(q)
assert len(questions)==15
speech=session[10]['content'];result=read(EV/'settlement-visual.json')
lesson=dict(id='lesson-7',title='第 3/4 单元',questions=questions,deferredSpeech=[dict(id='en-zh-l7-q10-speech',beforeQuestionID='en-zh-l7-q10-inserted',title='朗读下面的句子',phrase=speech['prompt'],audioResource=c.resource(speech['tts'],'speech'),declineLabel='现在不做口语题',closedTitle='麦克风已关闭',closedBody='将在 15 分钟后恢复')],reviewInterlude=dict(id='en-zh-l7-review-intro',afterQuestionID=questions[-1]['id'],text='一起来复习一下之前你不太熟练的部分吧！'),settlement=[dict(id='en-zh-l7-result',kind='result',title=result['title'],body=result['body'],continueLabel='继续',secondaryLabel='回顾本单元',experience=15,observedAccuracy=100,observedMistakes=0,accuracyLabel='超级棒'),dict(id='en-zh-l7-achievement',kind='achievement',title='先贤成就等级已提升！',levelLabel='第 2 级',body='你赚取了 100 经验',continueLabel='继续',secondaryLabel='回顾本单元'),dict(id='en-zh-l7-profile',kind='profile',title='来创建你的个人档案吧！',body='创建档案就能保存学习进度，随时都可以继续免费学习后续内容。',continueLabel='稍后再说',secondaryLabel='创建档案')])
course=fixture['data']['candidate_course'];course['lessons'].append(lesson);course['pathNodes'][1]['lessonIDs'].append('lesson-7');course['home']['progressSnapshots'].append(dict(course['home']['progressSnapshots'][-1],completedLessons=7,leagueCountdown='13 小时'))
fixture['provenance']['source'] += '; seventh actual 15 graded + speech-declined inserted/replaced translations + non-penalizing skipped q0 review + achievement/profile'
fixture['provenance']['evidence'] += ['projects/duolingo-web/evidence/english-seventh-v1/README.md','projects/duolingo-web/evidence/english-eighth-v1/retained-seventh-media.json']
fixture['provenance']['unknown']='Actual seventh skip + normal matching + radio2 + keyboard/harder + speech-declined + review + settlement path compiled. Radio1 sound, seventh listening-decline continuation, speech recording, external heart2->3 refresh, inserted/replacement character/audio bindings, full visual/acoustic equality and scoring formula remain unknown. Missing audio is not synthesized as an alternative.'
write(BASE/'fixture-reference-en-zh-v8.json',fixture);write(BASE/'reference-assets-en-zh-v8.json',list(c.resources.values()))
print('Compiled actual seventh, 15 graded + deferred speech + q0 review;',len(c.resources),'public resources')
