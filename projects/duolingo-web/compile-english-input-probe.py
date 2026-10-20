"""Compile two actually accepted input states, not a shortened replacement lesson."""
from pathlib import Path
import json, hashlib, re
BASE=Path(__file__).resolve().parent
EV=BASE/'evidence/english-next-node-v1'
def read(name):return json.loads((EV/name).read_text())
source=read('session.json')['session']; listen=read('listen-complete-response.json');reverse=read('reverse-response.json')
assert '太棒了！' in listen['feedback'] and 'Tea' in listen['feedback']
assert '你太棒了！' in reverse['feedback'] and 'tea' in reverse['feedback']
assert listen['steps']==[{'action':'fill Te','check_enabled':True},{'action':'clear','check_enabled':False},{'action':'fill Tea','check_enabled':True}]
resources=[]
def speech(url):
 assert url.startswith('https://d1vq87e9lcf771.cloudfront.net/') and '?' not in url
 stem='en-speech-'+hashlib.sha256(url.encode()).hexdigest()[:20];name=stem+'.mp3'
 resources.append(dict(url=url,kind='speech',name=stem,source_file=name));return name
questions=[]
for index,answer,response in [(3,'Tea',listen),(5,'tea',reverse)]:
 c=source['challenges'][index]['content'];tokens=c['displayTokens'];blank=[i for i,t in enumerate(tokens) if t['isBlank']];assert len(blank)==1
 assert tokens[blank[0]]['text']==answer
 questions.append(dict(id=f'en-zh-node2-q{index}',kind='text_entry',prompt='输入所缺单词',answer=answer,
  sourceType=c['type'],sourceLanguage='en' if c['type']=='listenComplete' else 'zh',
  hint=c.get('prompt'),completionPrefix=''.join(t['text'] for t in tokens[:blank[0]]),
  completionSuffix=''.join(t['text'] for t in tokens[blank[0]+1:]),
  correctFeedback=re.search(r'heading \"([^\"]+)\" \[level=2\]',response['feedback']).group(1),
  explanation='意思是： '+c['solutionTranslation'] if c.get('solutionTranslation') else '',
  audioResource=speech(c['tts']) if c.get('tts') else None,slowAudioResource=speech(c['slowTts']) if c.get('slowTts') else None))
fixture=dict(data={'candidate_course':dict(id='english-node2-input-probe',title='提供或接受饮料',speechLanguage='en',interfaceLanguage='zh',
 lessons=[dict(id='input-probe',title='输入题验证',questions=questions)],pathNodes=[dict(kind='star',lessonIDs=['input-probe'],lessonCount=4)])},
 provenance=dict(source='Two actual second-node states with source accepted input/feedback',evidence=[str((EV/n).relative_to(BASE.parent.parent)) for n in ['session.json','listen-complete-response.json','reverse-response.json']],
 scope='Isolated input component probe, not full original lesson or new default curriculum',unknown='Full source grading, wrong-input/review, speech recognition, entire second-node lesson, graphics/animation/audio equality pending'))
(BASE/'fixture-english-input-probe.json').write_text(json.dumps(fixture,ensure_ascii=False,indent=2)+'\n')
(BASE/'reference-assets-english-input-probe.json').write_text(json.dumps(resources,ensure_ascii=False,indent=2)+'\n')
print('Compiled 2 observed input states; full lesson not compiled')
