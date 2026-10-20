"""Compile the actually accepted current walk and its observed 17-card review.

An explicit instance fixture, never an adaptive selection algorithm or a change
to the default main/practice courses. All answers are tied to source feedback.
"""
import importlib.util
import json
from pathlib import Path
import re
from review_instance_compiler import compile_question, effect_resource

BASE = Path(__file__).resolve().parent
OLD = BASE / 'evidence/english-isolation-presentation-v1/source-probe'
EV = BASE / 'evidence/english-current-walk-v1/source'
spec = importlib.util.spec_from_file_location('english', BASE / 'compile-english-course.py')
c = importlib.util.module_from_spec(spec)
spec.loader.exec_module(c)


def read(path):
    return json.loads(path.read_text())


def heading(snapshot, level):
    return re.search(r'heading "([^"\n]+)" \[level='+str(level)+r'\]', snapshot).group(1)


def effect(url):
    return effect_resource(c, url)


records = []
for i in range(14):
    data = read(OLD/f'replay-{i}.json')
    records.append((data['session']['challenges'][0]['content'], data['observed'][0]))
tail = read(EV/'challenges.json')
records += [(record['content'], row) for record, row in zip(tail['session']['challenges'], tail['observed'])]
cards = [r for r in read(EV/'review-open-roles.json')['visible'] if r['tag'] == 'DIV' and r['role'] == 'button']
assert len(records) == len(cards) == 17
questions, speeches = [], []
for i, ((raw, row), card) in enumerate(zip(records, cards)):
    title, _, prompt = card['text'].partition('\n')
    if raw['type'] in ('translate', 'speak'):
        assert prompt == raw['prompt']
    elif raw['type'] == 'assist':
        assert raw['prompt'] in title
    elif raw['type'] in ('listenMatch', 'listenTap'):
        assert title == '选择你听到的内容：'
    elif raw['type'] == 'listenComplete':
        assert title == '输入所缺单词'
    if raw['type'] == 'speak':
        assert raw['prompt'] == 'Hot, please.' and not row.get('feedback')
        speeches.append(dict(id='current-review-speech', beforeQuestionID=f'current-review-q{i+1}',
            title=row['heading'], phrase=raw['prompt'], audioResource=c.resource(raw['tts'], 'speech'),
            declineLabel='现在不做口语题', closedTitle='麦克风已关闭', closedBody='将在 15 分钟后恢复',
            resultReview=dict(title=title, prompt=prompt, correctAnswer=raw['prompt'],
                              declinedAnswer=raw['prompt'], audioResources=[])))
        continue
    q = compile_question(c, effect, raw, row, card, f'current-review-q{i}')
    questions.append(q)
assert len(questions) == 16 and len(speeches) == 1
lesson = dict(id='current-review-practice', title='英语练习', questions=questions, deferredSpeech=speeches,
              interludes=[dict(id='current-review-intro', afterQuestionID='current-review-q13', text='哎哟不错哦！要不要玩点刺激的？')],
              settlement=[dict(id='current-review-result', kind='result', title='完美！', body='你练习全对，无错完成本单元',
                               continueLabel='继续', secondaryLabel='回顾本单元', retryLabel='重新练习')])
fixture = dict(provenance=dict(source='Actually accepted current-instance walk and observed 17-card review',
               evidence=[str(OLD.relative_to(BASE.parents[1])), str(EV.relative_to(BASE.parents[1]))],
               unknown='Wrong-answer review deduplication, adaptive retry selection, reward/XP and normal speech grading'),
               data=dict(candidate_course=dict(id='duolingo-current-review-instance', title='英语练习', speechLanguage='en',
                         interfaceLanguage='zh', mistakeHeartCost=0, lessons=[lesson])))
# Actual public source identities read from the review DOM, not replacements.
for name, asset in [('check', 'bed2a542bc7eddc78e75fbe85260b89e'), ('close', 'ed25a8cf69261b0c1e25b147f369f74a')]:
    stem = 'en-result-review-'+name
    c.resources[stem] = dict(name=stem, source_file=stem+'.svg', kind='home',
                            url='https://d35aaqx5ub95lt.cloudfront.net/images/'+asset+'.svg')
for path, value in [(BASE/'fixture-reference-en-zh-current-review-v1.json', fixture),
                    (BASE/'reference-assets-en-zh-current-review-v1.json', list(c.resources.values()))]:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n')
print(json.dumps(dict(graded_questions=len(questions), review_cards=len(cards), resources=len(c.resources))))
