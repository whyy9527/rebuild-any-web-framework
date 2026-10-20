from pathlib import Path
import json,re,hashlib,urllib.request
root=Path('projects/duolingo-web/evidence/english-pronunciation-practice-v1');bundle=Path('projects/education-swift/Sources/LingoSeed/Resources/Reference')
def readraw(name):return json.loads((root/name.replace('.raw.txt','.json')).read_text())
steps={}
for name in ['walk01','walk02','walk03']:
 for s in json.loads((root/name/'walk.json').read_text())['steps']:
  if 'feedback' in s:steps[s['index']]=s
history=readraw('media-history.raw.txt');q0url=history['events'][0]['src'];questions=[];urls=set()
for i in range(10):
 if i==0:
  s={'before':json.loads((root/'q0-before.json').read_text())['snapshot'],'feedback':readraw('q0-submit.raw.txt')['feedback'],'labels':[{'label':'1\ndock'},{'label':'2\ndeck'}],'media':[{'src':q0url}]}
 else:s=steps[i]
 options=[{'id':f'p{i}-o{n}','text':row['label'].split('\n',1)[1]} for n,row in enumerate(s['labels'])]
 same='先听后答' in s['before'];clips=[[x['src'] for x in segment] for segment in s.get('speakers',[])]
 if not clips:clips=[[x['src'] for x in s['media']]]
 clips=[list(dict.fromkeys(segment))[0] for segment in clips];urls.update(clips)
 heading=re.search(r'- heading "([^"]+)" \[level=2\]',s['feedback']).group(1)
 extra=re.findall(r'^- text: (.+)$',s['feedback'],re.M);correct=1 if '还不太准确' in heading else 0
 questions.append({'id':f'p{i}','kind':'choice','prompt':'先听后答' if same else '你听到了什么？','options':options,'answer':options[correct]['id'],'explanation':extra[-1] if extra else '', 'sourceType':'sameDifferent' if same else 'selectPronunciation','practiceAudioResources':clips,'correctFeedback':heading if correct==0 else None,'skipLabel':'跳过'})
 # These are actual disabled speaker labels revealed by feedback, not guesses from audio URLs.
 if same:
  questions[-1]['practiceAudioLabels']=re.findall(r'^- button "([^"]+)" \[disabled\]:$',s['feedback'],re.M)
# Current matching's public DOM data-test identities and accepted actual pairs.
pairs_raw=readraw('q11-pairs.raw.txt');pair_clips={r['left']:r['media'][0]['src'] for r in pairs_raw['rows']}
urls.update(pair_clips.values())
pairs=[{'id':f'pair{i}','left':str(i),'right':word,**({'audioResource':pair_clips[str(i)]} if str(i) in pair_clips else {})} for i,word in enumerate(['deck','dock','got','get'],1)]
feedback=json.loads((root/'q11-feedback.json').read_text())['snapshot'];titles=re.findall(r'- heading "([^"]+)" \[level=2\]',feedback)
questions.append({'id':'p11','kind':'matching','prompt':'选择配对','options':[],'answer':'','pairs':pairs,'rightOrder':['pair1','pair4','pair3','pair2'],'explanation':'','sourceType':'listenMatch','correctFeedback':titles[0] if titles else None,'skipLabel':'跳过'})
# Later practices are compiled from source receipts, never generated from word lists.
later_root=Path('projects/duolingo-web/evidence/english-pronunciation-matching-v1')
later_lessons=[]
for number,folder,matching_name in [(2,'source-second','matching-action.json'),(3,'source-third','third-matching.json')]:
 directory=later_root/folder
 walk=json.loads((directory/'walk01/walk.json').read_text())
 compiled=[]
 for row in walk['steps']:
  if row['index']>=10 or 'feedback' not in row:continue
  i=row['index'];qid=f'p{i}'
  options=[{'id':f'{qid}-o{n}','text':label['label'].split('\n',1)[1]} for n,label in enumerate(row['labels'])]
  heading=re.search(r'- heading "([^"\n]+)" \[level=2\]',row['feedback']).group(1)
  answer=1-row['chosen'] if '还不太准确' in heading else row['chosen']
  clips=[]
  for segment in row['speakers']:
   unique=list(dict.fromkeys(event['src'] for event in segment))
   if len(unique)!=1:raise ValueError(f'Ambiguous playback: {folder}/{i}')
   clips.append(unique[0])
  urls.update(clips)
  same='sameDifferent' in row['source_type']
  question={'id':qid,'kind':'choice','prompt':'先听后答' if same else '你听到了什么？','options':options,'answer':options[answer]['id'],'explanation':'','sourceType':'sameDifferent' if same else 'selectPronunciation','practiceAudioResources':clips,'correctFeedback':heading if answer==row['chosen'] else None,'skipLabel':'跳过'}
  if same:question['practiceAudioLabels']=re.findall(r'^- button "([^"\n]+)" \[disabled\]:$',row['feedback'],re.M)
  compiled.append(question)
 if len(compiled)!=10:raise ValueError(f'Incomplete choice observations: {folder}')
 matching=json.loads((directory/matching_name).read_text())
 accepted=matching.get('pairs',matching.get('rows'))
 # Accepted pair order is the actual left-button traversal order; right labels come from DOM.
 words=[row['word'] for row in accepted]
 right_words=re.findall(r'^- button "[5-8] ([^"\n]+)":$',matching['before'],re.M)
 if len(words)!=4 or set(words)!=set(right_words):raise ValueError('Matching evidence inconsistent')
 pairs=[]
 for i,row in enumerate(accepted,1):
  pair={'id':f'pair{i}','left':str(i),'right':row['word']}
  clips=list(dict.fromkeys(event['src'] for event in row.get('media',[])))
  if len(clips)>1:raise ValueError('Ambiguous matching audio')
  if clips:pair['audioResource']=clips[0];urls.add(clips[0])
  pairs.append(pair)
 match_id='p11' if number==3 else 'p10'
 headings=re.findall(r'- heading "([^"\n]+)" \[level=2\]',accepted[-1]['snapshot'])
 compiled.append({'id':match_id,'kind':'matching','prompt':'选择配对','options':[],'answer':'','pairs':pairs,'rightOrder':[f'pair{words.index(word)+1}' for word in right_words],'explanation':'','sourceType':'listenMatch','correctFeedback':headings[-1],'skipLabel':'跳过'})
 lesson={'id':f'pronunciation-{number}','title':'英语发音','questions':compiled}
 if number==3:
  speech=json.loads((directory/'third-speech-decline02.json').read_text())
  clip=speech['speech_media'][0]['src'];urls.add(clip)
  heading=re.search(r'- heading "([^"\n]+)" \[level=2\]',speech['declined']).group(1)
  lesson['deferredSpeech']=[{'id':'p10','beforeQuestionID':'p11','title':'朗读下面的句子','phrase':'tell','audioResource':clip,'declineLabel':'现在不做口语题','closedTitle':heading,'closedBody':''}]
 # These are observed settlement examples, not an inferred time/score selection formula.
 title='你莫不是特工？' if number==2 else '真投入！'
 body='本单元中，你完成了 11 项听力挑战' if number==2 else '你花了超过 7 分钟完成本单元，坚持就是胜利！'
 lesson['settlement']=[{'id':'practice-result','kind':'complete','title':title,'body':body,'continueLabel':'继续'}]
 if number in (2,3):
  lesson['settlement'].append({'id':'practice-profile','kind':'profile','title':'来创建你的个人档案吧！','body':'创建档案就能保存学习进度，随时都可以继续免费学习后续内容。','continueLabel':'稍后再说','secondaryLabel':'创建档案'})
 later_lessons.append(lesson)
manifest=[]
for url in sorted(urls):
 name='pronunciation-word-'+hashlib.sha256(url.encode()).hexdigest()[:20]+'.mp3';data=(bundle/name).read_bytes() if (bundle/name).exists() else urllib.request.urlopen(url,timeout=30).read();(bundle/name).write_bytes(data);manifest.append({'url':url,'resource':name,'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data)})
lookup={x['url']:x['resource'] for x in manifest}
for q in questions+[q for lesson in later_lessons for q in lesson['questions']]:
 if 'practiceAudioResources' in q:q['practiceAudioResources']=[lookup[u] for u in q['practiceAudioResources']]
 for pair in q.get('pairs',[]):
  if 'audioResource' in pair:pair['audioResource']=lookup[pair['audioResource']]
for lesson in later_lessons:
 for speech in lesson.get('deferredSpeech',[]):speech['audioResource']=lookup[speech['audioResource']]
c=json.loads(Path('projects/duolingo-web/fixture-reference-en-zh-v10.json').read_text())['data']['candidate_course'];c['id']='duolingo-en-zh-pronunciation';c['title']='英语发音';c.pop('questions',None);c.pop('pathNodes',None);c.pop('home',None);c['lessons']=[{'id':'pronunciation-1','title':'英语发音','questions':questions,'deferredSpeech':[{'id':'p10','beforeQuestionID':'p11','title':'朗读下面的句子','phrase':'got','audioResource':'','declineLabel':'现在不做口语题','closedTitle':'你说英语越来越有自信啦！','closedBody':''}],'settlement':[{'id':'practice-result','kind':'complete','title':'真投入！','continueLabel':'继续'},{'id':'practice-profile','kind':'profile','title':'来创建你的个人档案吧！','body':'创建档案就能保存学习进度，随时都可以继续免费学习后续内容。','continueLabel':'稍后再说','secondaryLabel':'创建档案'}]}]
c['lessons'].extend(later_lessons)
(bundle/'pronunciation-practice.json').write_text(json.dumps(c,ensure_ascii=False,indent=2)+'\n')
Path('projects/duolingo-web/reference-pronunciation-practice-audio-v2.json').write_text(json.dumps({'resources':manifest,'unknown':['First speech prompt playback','First matching left1 playback','Second practice matching playback identities','Adaptive practice selection and phoneme progress rules']},ensure_ascii=False,indent=2)+'\n')
print('lessons',len(c['lessons']),'graded_questions',[len(lesson['questions']) for lesson in c['lessons']],'resources',len(manifest))
