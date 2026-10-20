"""Compile only this actually accepted unit-12 test, separate from section placement."""
import argparse,hashlib,importlib.util,json,re
from pathlib import Path
from review_instance_compiler import effect_resource
B=Path(__file__).resolve().parent;E=B/'evidence/english-unit-placement-v1';S=E/'source';R=B.parent/'education-swift/Sources/LingoSeed/Resources/Reference'
p=argparse.ArgumentParser();p.add_argument('--out-dir');a=p.parse_args();out=Path(a.out_dir) if a.out_dir else None
if out:out.mkdir(parents=True,exist_ok=False)
spec=importlib.util.spec_from_file_location('english',B/'compile-english-course.py');c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)
def read(n):return json.loads((S/n).read_text())
records=[];interludes=[]
for filename in ['unit12-batch02.json','unit12-batch04.json','unit12-batch05.json']:
 d=read(filename);raws={r['index']:r['content'] for r in d['session']['challenges']}
 events=[(r['index'],'q',r) for r in d['observed'] if r.get('feedback')]+[(r['index'],'i',r) for r in d['interludes']]
 for index,kind,row in sorted(events,key=lambda v:v[0]):
  if kind=='i':
   messages=row['facts']['encouragement_messages'];assert len(messages)==1
   interludes.append(dict(id='unit12-interlude-'+str(len(interludes)),afterQuestionID='unit12-q'+str(len(records)-1),text=messages[0]))
  else:assert row['rejected'] is False and row['identity']['matches'];records.append((raws[index],row))
cards=[r for r in read('unit12-review.json')['visible'] if r['tag']=='DIV' and r['role']=='button']
assert len(records)==len(cards)==18 and len(interludes)==4
questions=[]
for i,((raw,row),card) in enumerate(zip(records,cards)):
 q=dict(id='unit12-q'+str(i),prompt=row['heading'],sourceType=raw['type'],explanation='',sourceLanguage=raw.get('sourceLanguage','en'),correctFeedback=re.search(r'heading "([^"\n]+)" \[level=2\]',row['feedback']).group(1))
 for src,dst in [('tts','audioResource'),('slowTts','slowAudioResource')]:
  if raw.get(src):q[dst]=c.resource(raw[src],'speech')
 if raw.get('character'):q['characterResource']=c.resource(raw['character']['image']['svg'],'image')
 if raw['type'] in ['assist','gapFill']:
  texts=row['identity']['actual']['choices'];answer=raw['choices'][raw['correctIndex']]
  assert row['actions']==[{'select':answer}]
  q.update(kind='choice',options=[dict(id='option-'+str(j),text=t) for j,t in enumerate(texts)])
  q['answer']=next(o['id'] for o in q['options'] if o['text']==answer)
  if raw['type']=='assist':
   q['hint']=raw['prompt'];clips=list(dict.fromkeys(m['src'] for m in row['media'] if m['src'].startswith('https://d1vq87e9lcf771.cloudfront.net/')));assert len(clips)==1
   next(o for o in q['options'] if o['id']==q['answer'])['audioResource']=c.resource(clips[0],'speech')
  else:
   ts=raw['displayTokens'];blanks=[j for j,t in enumerate(ts) if t['isBlank']];assert len(blanks)==1
   q.update(completionPrefix=''.join(t['text'] for t in ts[:blanks[0]]),completionSuffix=''.join(t['text'] for t in ts[blanks[-1]+1:]))
   answer=''.join(t['text'] for t in ts)
 elif raw['type']=='tapComplete' or raw['type']=='translate' and raw.get('choices'):
  chosen=[raw['choices'][j]['text'] for j in raw['correctIndices']];assert [v['word'] for v in row['actions']]==chosen
  words,ids=c.compile_word_bank(raw['choices'],[t.strip() for t in row['word_bank']],chosen);q.update(kind='word_tiles',words=words,answer_words=ids)
  if raw['type']=='tapComplete':
   ts=raw['displayTokens'];blanks=[j for j,t in enumerate(ts) if t['isBlank']]
   q.update(completionPrefix=''.join(t['text'] for t in ts[:blanks[0]]),completionSuffix=''.join(t['text'] for t in ts[blanks[-1]+1:]));answer=''.join(t['text'] for t in ts)
   if raw.get('image'):q['promptImageResource']=c.resource(raw['image']['svg'],'image')
  else:q['hint']=raw['prompt'];answer=raw.get('correctSolutions',[raw['prompt']])[0]
 elif raw['type'] in ['listen','name','translate']:
  answer=row['text_input']['value'];assert answer in raw.get('correctSolutions',[raw.get('prompt')]);q.update(kind='text_entry',answer=answer)
  if raw['type']=='translate':q['hint']=raw['prompt']
  if raw['type']=='name':assert len(row['images'])==1;q['promptImageResource']=c.resource(row['images'][0]['src'],'image')
 else:raise ValueError(raw['type'])
 effects=list(dict.fromkeys(m['src'] for m in row['media'] if m['src'].startswith('https://d35aaqx5ub95lt.cloudfront.net/sounds/')));assert len(effects)<=1
 if effects:q['correctFeedbackAudioResource']=effect_resource(c,effects[0])
 title,_,prompt=card['text'].partition('\n');q['resultReview']=dict(title=title,prompt=prompt,correctAnswer=answer,audioResources=[q['audioResource']] if raw['type']=='listen' else [])
 questions.append(q)
# Exact original intro/unlock image; captured source result SVG is a frame, not proof of motion.
assets={}
for source,name in [('unit12-intro.json','intro'),('unit12-after-score.json','unlock')]:
 image=next(m for m in read(source)['media'] if m.get('src') and '/sessionSplash/' in m['src']);resource=c.resource(image['src'],'home');c.resources[resource].update(render_width=round(image['rect'][2]),render_height=round(image['rect'][3]),inline_svg=True);assets[name]=resource
svg=next(m for m in read('unit12-current-after05.json')['media'] if len(m.get('svg') or '')>10000)
name='en-unit12-result-'+hashlib.sha256(svg['svg'].encode()).hexdigest()[:16];(out/(name+'.svg') if out else R/(name+'.svg')).write_text(svg['svg'])
c.resources[name]=dict(name=name,url='https://www.duolingo.com/lesson/unit/12/test',kind='image',source_file=name+'.svg',render_width=310,render_height=329,inline_svg=True);assets['result']=name
lesson=dict(id='unit-placement-12',title='第 2 部分通关测试',questions=questions,interludes=interludes,settlement=[dict(id='unit12-result',kind='result',title='测试完成！',continueLabel='继续',secondaryLabel='回顾本单元',experience=50,observedAccuracy=100,observedMistakes=0,accuracyLabel='超级棒'),dict(id='unit12-score',kind='score_progress',title='离提升你的英语分数又近了一步！',continueLabel='继续',scoreValue=10),dict(id='unit12-unlock',kind='unit_unlock',title='你解锁了第 2 部分！',continueLabel='继续',secondaryLabel='回顾本单元'),dict(id='unit12-profile',kind='profile',title='来创建你的个人档案吧！',body='创建档案就能保存学习进度，随时都可以继续免费学习后续内容。',continueLabel='稍后再说',secondaryLabel='创建档案')])
prior=json.loads((E/'prepared-progress.json').read_text())['placementOutcomes']['duolingo-en-zh-unit-1'];outcome={**prior,'activeUnit':12,'sectionTitle':'第 2 阶段，第 2 部分','courseTitle':'描述你的家居布局','sourceEvidence':'projects/duolingo-web/evidence/english-unit-placement-v1/source/unit12-home-after.json','observedMistakes':0};lesson['placementOutcome']=outcome
fixture=dict(data=dict(candidate_course=dict(id='duolingo-en-zh-unit-placement-12',title=lesson['title'],speechLanguage='en',interfaceLanguage='zh',lessons=[lesson])),provenance=dict(source='18 actual accepted current-renderer questions, four interludes, 18 real review cards and observed50XP/100% outcome',unknown='Adaptive selection, different errors/rewards, full source animations and acoustic equality remain unverified'))
for path,data in [(R/'unit-placement-12.json',fixture),(B/'fixture-reference-en-zh-unit-placement-v1.json',fixture),(B/'reference-assets-en-zh-unit-placement-v1.json',list(c.resources.values())),(R/'unit-placement-presentation.json',assets)]:
 (out/path.name if out else path).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(dict(questions=len(questions),interludes=len(interludes),resources=len(c.resources))))
