"""Compile actual first-wrong and separate corrected result cards, retaining both."""
import importlib.util
import json
from pathlib import Path
import re
from review_instance_compiler import compile_question, effect_resource

BASE = Path(__file__).resolve().parent
EV = BASE/'evidence/english-error-review-v1/source'
spec = importlib.util.spec_from_file_location('english', BASE/'compile-english-course.py')
c = importlib.util.module_from_spec(spec)
spec.loader.exec_module(c)
def read(name): return json.loads((EV/name).read_text())
def effect(url): return effect_resource(c, url)
records = []
for name in ['start.json', 'after-wrong.json', 'after-speech.json']:
    data = read(name)
    records += [(r['content'], row) for r, row in zip(data['session']['challenges'], data['observed'])]
cards = [r for r in read('review-cards.json')['visible'] if r['tag'] == 'DIV' and r['role'] == 'button']
assert len(records) == len(cards) == 18
wrong = read('wrong-assist.json')
assert wrong['rejected'] and wrong['selected'] == 'coffee' and 'hot' in wrong['feedback']
assert records[-1][0] == records[1][0]
assert records[-1][1]['identity']['matches'] and records[-1][1]['rejected'] is False
assert cards[1]['css']['backgroundColor'] == 'rgb(255, 223, 224)' and cards[-1]['css']['backgroundColor'] == 'rgb(215, 255, 184)'
assert cards[1]['text'] == cards[-1]['text'] == '"热" 该怎么说？'
questions, speeches = [], []
for i, ((raw, observed), card) in enumerate(zip(records[:-1], cards[:-1])):
    title, _, prompt = card['text'].partition('\n')
    if raw['type'] in ('translate', 'speak'): assert prompt == raw['prompt']
    if raw['type'] == 'speak':
        assert not observed.get('feedback') and raw['prompt'] == 'More milk?'
        speeches.append(dict(id='error-review-speech', beforeQuestionID=f'error-review-q{i+1}', title=observed['heading'],
            phrase=raw['prompt'], audioResource=c.resource(raw['tts'],'speech'), declineLabel='现在不做口语题',
            closedTitle='麦克风已关闭', closedBody='将在 15 分钟后恢复',
            resultReview=dict(title=title,prompt=prompt,correctAnswer=raw['prompt'],declinedAnswer=raw['prompt'],audioResources=[])))
        continue
    row = observed
    if i == 1:
        # The first attempt was wrong. Its visible choices identify the same
        # question later corrected; only correct-feedback presentation is taken
        # from the actually accepted correction, not asserted for the first try.
        order = [c.label(t) for t in re.findall(r'- radio "([^"\n]+)"', observed['before'])]
        assert order == records[-1][1]['identity']['actual']['choices']
        row = dict(records[-1][1], before=observed['before'])
    q = compile_question(c,effect,raw,row,card,f'error-review-q{i}')
    if raw['type'] == 'listen':
        assert q['kind'] == 'text_entry'
    questions.append(q)
assert len(questions) == 16 and len(speeches) == 1
lesson = dict(id='error-review-practice', title='英语练习', questions=questions, deferredSpeech=speeches,
    interludes=[dict(id='error-review-challenge-intro',afterQuestionID='error-review-q15',text='哎哟不错哦！要不要玩点刺激的？')],
    reviewInterlude=dict(id='error-review-correction-intro',afterQuestionID='error-review-q16',text='一起来复习一下之前你不太熟练的部分吧！'),
    settlement=[dict(id='error-review-result',kind='result',title='你莫不是特工？',body='本单元中，你完成了 6 项听力挑战',
                     observedMistakes=1,continueLabel='继续',secondaryLabel='回顾本单元',retryLabel='重新练习')])
fixture = dict(provenance=dict(source='Actually wrong coffee for hot, later accepted hot and two separate result cards',
    evidence=[str(EV.relative_to(BASE.parents[1]))],unknown='Adaptive selection, reward/score, other error and card types, acoustic equality'),
    data=dict(candidate_course=dict(id='duolingo-error-review-instance',title='英语练习',speechLanguage='en',interfaceLanguage='zh',mistakeHeartCost=0,lessons=[lesson])))
stem='en-result-review-wrong'
c.resources[stem]=dict(name=stem,source_file=stem+'.svg',kind='home',url='https://d35aaqx5ub95lt.cloudfront.net/images/9a4bf74a74e801ca35402f2c2837e24c.svg')
for path,value in [(BASE/'fixture-reference-en-zh-error-review-v1.json',fixture),(BASE/'reference-assets-en-zh-error-review-v1.json',list(c.resources.values()))]:
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(dict(graded_questions=len(questions),review_cards=len(cards),resources=len(c.resources))))
