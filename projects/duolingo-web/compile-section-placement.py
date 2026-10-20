"""Compile only actually accepted current-renderer placement questions.

The instance is evidence, not an adaptive selection model or a blind RSI score.
Raw ungraded stops remain in the receipts; no future challenge list is read.
"""
import hashlib
import argparse
import importlib.util
import json
from pathlib import Path
import re

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--without-outcome',action='store_true',help='Reproduce the prior v1 fixture without post-placement outcome')
parser.add_argument('--out-dir',help='Write compiler products into a fresh directory instead of the working bundle')
args=parser.parse_args()
version=1 if args.without_outcome else 2
BASE = Path(__file__).resolve().parent
EV = BASE / 'evidence/english-sections-v1'
BUNDLE = BASE.parent / 'education-swift/Sources/LingoSeed/Resources/Reference'
spec = importlib.util.spec_from_file_location('english', BASE / 'compile-english-course.py')
c = importlib.util.module_from_spec(spec)
spec.loader.exec_module(c)
questions, interludes, provenance = [], [], []


def heading(snapshot):
    return re.search(r'heading "([^"\n]+)" \[level=2\]', snapshot).group(1)


for filename in sorted(EV.glob('placement-batch*.json')):
    receipt = json.loads(filename.read_text())
    source = {r['index']: r['content'] for r in receipt['session']['challenges']}
    # Interludes and questions share the actual step order within each batch.
    events = [(r['index'], 'question', r) for r in receipt['observed'] if 'feedback' in r]
    events += [(r['index'], 'interlude', r) for r in receipt['interludes']]
    for local_index, kind, row in sorted(events, key=lambda v: v[0]):
        if kind == 'interlude':
            assert questions
            text = row['facts'].get('encouragement_messages', [])
            if not text:
                text = [row['facts']['body_text'].removesuffix('\n继续')]
            assert len(text) == 1
            interludes.append(dict(id=f'placement-encouragement-{len(interludes)}',
                                   afterQuestionID=questions[-1]['id'], text=text[0]))
            continue
        assert not row['rejected'] and row['identity']['matches']
        raw = source[local_index]
        index = len(questions)
        q = dict(id=f'placement-2-q{index}', prompt=row['heading'], sourceType=raw['type'],
                 explanation='', sourceLanguage=raw.get('sourceLanguage', 'en'),
                 correctFeedback=heading(row['feedback']))
        for field, target in [('tts', 'audioResource'), ('slowTts', 'slowAudioResource')]:
            if raw.get(field):
                q[target] = c.resource(raw[field], 'speech')
        if raw.get('character'):
            q['characterResource'] = c.resource(raw['character']['image']['svg'], 'image')
        if raw['type'] == 'assist':
            texts = row['identity']['actual']['choices']
            answer = raw['choices'][raw['correctIndex']]
            assert row['actions'] == [dict(select=answer)]
            options = [dict(id=f'option-{i}', text=t) for i,t in enumerate(texts)]
            clips = list(dict.fromkeys(m['src'] for m in row['media']
                         if m['src'].startswith('https://d1vq87e9lcf771.cloudfront.net/')))
            assert len(clips) == 1
            target = next(o for o in options if o['text'] == answer)
            target['audioResource'] = c.resource(clips[0], 'speech')
            q.update(kind='choice', hint=raw['prompt'], options=options, answer=target['id'])
        elif raw['type'] == 'tapComplete' or (raw['type'] == 'translate' and raw.get('choices')):
            answer = [raw['choices'][i]['text'] for i in raw['correctIndices']]
            assert [a['word'] for a in row['actions']] == answer
            words, ids = c.compile_word_bank(raw['choices'], [t.strip() for t in row['word_bank']], answer)
            q.update(kind='word_tiles', words=words, answer_words=ids)
            if raw['type'] == 'tapComplete':
                tokens = raw['displayTokens']
                blanks = [i for i,t in enumerate(tokens) if t['isBlank']]
                q.update(completionPrefix=''.join(t['text'] for t in tokens[:blanks[0]]),
                         completionSuffix=''.join(t['text'] for t in tokens[blanks[-1]+1:]),
                         promptImageResource=c.resource(raw['image']['svg'], 'image'))
                assert raw['image']['svg'] in [v['src'] for v in row['images']]
            else:
                q['hint'] = raw['prompt']
        elif raw['type'] in ('listen', 'name', 'translate'):
            answer = row['text_input']['value']
            assert answer in raw.get('correctSolutions', [raw.get('prompt')])
            q.update(kind='text_entry', answer=answer)
            if raw['type'] == 'translate':
                q['hint'] = raw['prompt']
            elif raw['type'] == 'name':
                assert len(row['images']) == 1
                q['promptImageResource'] = c.resource(row['images'][0]['src'], 'image')
        else:
            raise ValueError(raw['type'])
        effects = list(dict.fromkeys(m['src'] for m in row['media']
                       if m['src'].startswith('https://d35aaqx5ub95lt.cloudfront.net/sounds/')))
        assert len(effects) <= 1
        if effects:
            name = 'en-effect-' + hashlib.sha256(effects[0].encode()).hexdigest()[:20]
            c.resources[name] = dict(name=name, url=effects[0], kind='feedback', source_file=name+'.mp3')
            q['correctFeedbackAudioResource'] = name+'.mp3'
        questions.append(q)
        provenance.append(dict(question=q['id'], receipt=filename.name, local_index=local_index,
                               screenshot=row['screenshot_before']))

assert len(questions) == 15 and len(interludes) == 3
lesson = dict(id='section-placement-2', title='第 2 阶段通关测试', questions=questions,
              interludes=interludes, settlement=[
    dict(id='placement-result', kind='result', title='完美！', body='你练习全对，无错完成本单元',
         continueLabel='继续', secondaryLabel='回顾本单元', experience=50,
         observedAccuracy=100, observedMistakes=0, accuracyLabel='超级棒'),
    dict(id='placement-score', kind='score', title='你成功提升了你的英语分数！', continueLabel='继续',
         scoreValue=10),
    dict(id='placement-quests', kind='daily_quests', title='所有每日特别任务都完成啦！',
         body='获取 50 经验', questTarget=50, continueLabel='继续', secondaryLabel='回顾本单元'),
    dict(id='placement-gems', kind='gems', title='你赚取了 5 颗宝石！',
         body='完成每日目标真不容易哦！', continueLabel='继续', secondaryLabel='回顾本单元'),
    dict(id='placement-profile', kind='profile', title='来创建你的个人档案吧！',
         body='创建档案就能保存学习进度，随时都可以继续免费学习后续内容。',
         continueLabel='稍后再说', secondaryLabel='创建档案')])
if not args.without_outcome:
    # This is the actually observed post-test state, not a reward/unlock formula.
    post=json.loads((EV/'source/sections-stage2-home.json').read_text())
    assert all(any(a.get('name')==t for a in post['actions']) for t in ['10','2','530','5'])
    league=next(m for m in post['media'] if '/images/leagues/' in (m.get('src') or ''))
    league_resource=c.resource(league['src'],'home')
    c.resources[league_resource].update(render_width=70,render_height=50)
    lesson['placementOutcome']=dict(activeStage=2,completedStages=[1],englishScore=10,
        sectionTitle='第 2 阶段，第 1 部分',courseTitle='购买食品杂货',observedMistakes=0,
        sourceEvidence='projects/duolingo-web/evidence/english-sections-v1/source/sections-stage2-home.json',
        homeSnapshot=dict(completedLessons=8,gems=530,streak=2,leagueTitle='青铜等级',leagueLink='查看排行榜',
          leagueMessage='学个单元就能上本周排行榜，跟其他小伙伴一决高低！',leagueResource=league_resource,
          questTarget=50,questProgress=50))
    assert all(t in [r['text'] for r in post['text_runs']] for t in [lesson['placementOutcome']['sectionTitle'],lesson['placementOutcome']['courseTitle'],lesson['placementOutcome']['homeSnapshot']['leagueMessage']])
fixture = dict(data=dict(candidate_course=dict(id='duolingo-en-zh-section-placement-2',
    title=lesson['title'], speechLanguage='en', interfaceLanguage='zh', lessons=[lesson])),
    provenance=dict(source='15 actual current-renderer questions accepted in stage2 placement',
    questions=provenance, unknown='Adaptive selection, wrong-answer/quit-after-answer rules, stage unlock persistence, exact pixels/animation/audio output remain unverified. Result score is this observed all-correct instance, not a scoring formula.'))
heart_source=json.loads((BASE/'evidence/english-profile-return-v1/source/section-test-first.json').read_text())
heart=next(m['src'] for m in heart_source['media'] if '/hearts/c5e896836d874aac0c0196a41cf9411b.svg' in m.get('src',''))
c.resources['en-placement-heart']=dict(name='en-placement-heart',url=heart,kind='image',source_file='en-placement-heart.svg',render_width=25,render_height=22)
filled=next(m['src'] for m in heart_source['media'] if '/hearts/5622d0c47ee5b3c9f2bda53b1a18d59b.svg' in m.get('src',''))
c.resources['en-placement-heart-filled']=dict(name='en-placement-heart-filled',url=filled,kind='image',source_file='en-placement-heart-filled.svg',render_width=25,render_height=22)
if args.out_dir: Path(args.out_dir).mkdir(parents=True,exist_ok=False)
for path, data in [(BUNDLE/'section-placement-2.json', fixture),
                   (BASE/f'fixture-reference-en-zh-section-placement-v{version}.json', fixture),
                   (BASE/f'reference-assets-en-zh-section-placement-v{version}.json', list(c.resources.values()))]:
    if args.out_dir: path=Path(args.out_dir)/path.name
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2)+'\n')
print(json.dumps(dict(accepted=len(questions), interludes=len(interludes), resources=len(c.resources))))
