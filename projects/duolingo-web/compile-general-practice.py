"""Compile executed GLOBAL_PRACTICE receipts into a separate Swift course.

This is the observed instance, including actual replacements, not an inferred
adaptive selection algorithm. Main-course fixtures are not modified.
"""
import importlib.util
import hashlib
import json
from pathlib import Path
import re

BASE = Path(__file__).resolve().parent
EV = BASE / 'evidence/english-general-practice-v1'
BUNDLE = BASE.parent / 'education-swift/Sources/LingoSeed/Resources/Reference'
spec = importlib.util.spec_from_file_location('english', BASE / 'compile-english-course.py')
c = importlib.util.module_from_spec(spec)
spec.loader.exec_module(c)


def read(name):
    return json.loads((EV / name).read_text())


def heading(snapshot, level):
    return re.search(r'heading "([^"\n]+)" \[level='+str(level)+r'\]', snapshot).group(1)


def effect(url):
    assert url.startswith(('https://d35aaqx5ub95lt.cloudfront.net/sounds/', 'https://simg-ssl.duolingo.com/videos/sound/')) and '?' not in url
    name = 'en-effect-' + hashlib.sha256(url.encode()).hexdigest()[:20]
    c.resources[name] = dict(url=url, kind='feedback', name=name, source_file=name+'.mp3')
    return name+'.mp3'


source = read('session.json')['session']['challenges']
rows = {}
for filename in ['replay.json', 'replay-from-5.json', 'replay-from-6.json', 'replay-from-8-after-inserted.json', 'replay-from-11.json']:
    for row in read(filename)['observed']:
        if 'feedback' in row:
            assert row['identity']['matches']
            rows[row['index']] = row
wrong_media = json.loads((BASE/'evidence/english-general-practice-native-v1/source-probe/media-after-wrong.json').read_text())
incorrect_urls = list(dict.fromkeys(m['src'] for m in wrong_media['media'] if m['src'].startswith('https://d35aaqx5ub95lt.cloudfront.net/sounds/')))
assert len(incorrect_urls) == 1
questions = []
for index in [0, 1, 2, 3, 4, 5, 6, 8, 9, 10, 11, 12]:
    raw = source[index]['content']
    row = rows.get(index)
    if index == 10:
        row = read('complete-answer.json')
        assert not row['rejected']
    q = dict(id=f'general-practice-q{index}', prompt=heading(row['before'], 1), sourceType=raw['type'], explanation='', correctFeedback=heading(row['feedback'], 2))
    for field, target in [('tts', 'audioResource'), ('slowTts', 'slowAudioResource')]:
        if raw.get(field):
            q[target] = c.resource(raw[field], 'speech')
    if raw.get('character'):
        q['characterResource'] = c.resource(raw['character']['image']['svg'], 'image')
    if raw['type'] == 'listenMatch':
        pairs = []
        for p in row['pair_audio_order']:
            assert len(p['played_audio']) == 1
            pairs.append(dict(id=str(p['left_index']), left=str(p['left_index']+1), right=p['translation'], audioResource=c.resource(p['played_audio'][0], 'speech')))
        q.update(kind='matching', pairs=pairs, rightOrder=[next(p['id'] for p in pairs if p['right']==text) for text in row['right_text']])
        q['matchedAudioResources'] = [effect(url) for url in dict.fromkeys(m['src'] for m in row['media'] if m['src'].startswith('https://simg-ssl.duolingo.com/videos/sound/Match_Correct_'))]
        assert len(q['matchedAudioResources']) == 4
        q['listeningDecline'] = dict(label='现在不做听力题', title='听力练习已关闭', body='将在 15 分钟后恢复')
    elif raw['type'] == 'assist':
        correct = raw['choices'][raw['correctIndex']]
        options = [dict(id=str(i), text=text) for i, text in enumerate(row['identity']['actual']['choices'])]
        q.update(kind='choice', hint=raw['prompt'], options=options, answer=next(o['id'] for o in options if o['text']==correct))
        clips = list(dict.fromkeys(m['src'] for m in row['media'] if m['src'].startswith('https://d1vq87e9lcf771.cloudfront.net/')))
        assert len(clips) == 1
        next(o for o in options if o['id']==q['answer'])['audioResource'] = c.resource(clips[0], 'speech')
        q['incorrectFeedbackAudioResource'] = effect(incorrect_urls[0])
    elif raw['type'] == 'listenIsolation':
        blank = raw['tokens'][raw['blankRangeStart']:raw['blankRangeEnd']]
        sentence = ''.join(t['value'] for t in raw['tokens'])
        q.update(kind='choice', hint=sentence.replace(''.join(t['value'] for t in blank), '__'),
                 options=[dict(id=str(o['index']), text=str(o['index']+1), audioResource=c.resource(o['played_audio'][0], 'speech'), imageResource=f'en-seventh-isolation-wave-{o["index"]+1}') for o in row['audio_options']],
                 answer=str(next(o['index'] for o in row['audio_options'] if o['text']==raw['options'][raw['correctIndex']]['text'])), explanation='意思是： '+raw['solutionTranslation'])
        q['isolationPromptTokens'] = [dict(text=t['value'], isBlank=raw['blankRangeStart'] <= i < raw['blankRangeEnd'], underlined=bool(t.get('tts'))) for i, t in enumerate(raw['tokens'])]
    elif raw['type'] in ['translate', 'listenTap']:
        choices = [dict(text=v) if isinstance(v, str) else v for v in raw['choices']]
        answer = [choices[i]['text'] for i in raw['correctIndices']]
        assert [a['word'] for a in row['actions']] == answer
        words, ids = c.compile_word_bank(choices, [t.strip() for t in row['word_bank']], answer)
        q.update(kind='word_tiles', words=words, answer_words=ids)
        if raw['type'] == 'translate':
            q.update(hint=raw['prompt'], sourceLanguage=raw.get('sourceLanguage', 'en'))
        if any('button "'+label+'"' in row['before'] for label in ['使用键盘', '使用词库']):
            q.update(keyboardAnswer=raw.get('correctSolutions', [raw['prompt']])[0], keyboardPrompt='键入你听到的内容' if raw['type']=='listenTap' else q['prompt'])
    elif raw['type'] == 'listen':
        assert row['text_input']['value'] == raw['prompt']
        q.update(kind='text_entry', answer=raw['prompt'])
    elif raw['type'] == 'listenComplete':
        tokens = raw['displayTokens']
        blanks = [i for i,t in enumerate(tokens) if t['isBlank']]
        assert len(blanks) == 1
        b = blanks[0]
        answer = row.get('input', row.get('text_input', {}).get('value'))
        assert answer == tokens[b]['text']
        q.update(kind='text_entry', answer=answer, completionPrefix=''.join(t['text'] for t in tokens[:b]), completionSuffix=''.join(t['text'] for t in tokens[b+1:]), explanation='意思是： '+raw['solutionTranslation'])
    else:
        raise ValueError(raw['type'])
    if 'button "跳过"' in row['before']:
        q['skipLabel'] = '跳过'
    feedback_urls = list(dict.fromkeys(m['src'] for m in row.get('media', []) if m['src'].startswith('https://d35aaqx5ub95lt.cloudfront.net/sounds/')))
    assert len(feedback_urls) <= 1
    if feedback_urls:
        q['correctFeedbackAudioResource'] = effect(feedback_urls[0])
    questions.append(q)

# Actual inserted translation. Playback was explicitly observed at the stopped
# replacement boundary, and the character is visually Oscar in the source frame.
inserted = read('inserted-answer.json')
assert not inserted['rejected']
speech = source[7]['content']
assert speech['tts'] in [m['src'] for m in read('replay-from-8.json')['observed'][0]['identity_playback']]
words, ids = c.compile_word_bank([dict(text=t) for t in inserted['choices']], inserted['choices'], [a['word'] for a in inserted['clicks']])
questions.insert(7, dict(id='general-practice-inserted', kind='word_tiles', sourceType='translate', sourceLanguage='en', prompt=heading(inserted['before'],1), hint=inserted['prompts'][0], words=words, answer_words=ids, explanation='', correctFeedback=heading(inserted['feedback'],2), audioResource=c.resource(speech['tts'],'speech'), characterResource=c.resource(speech['character']['image']['svg'],'image'), skipLabel='跳过'))
for number, filename, character_index in [(13,'replacement-answer.json',15),(14,'replacement14-answer.json',3),(15,'review-answer.json',9)]:
    row = read(filename)
    assert not row['rejected']
    questions.append(dict(id=f'general-practice-replacement{number}', kind='text_entry', sourceType='translate', sourceLanguage='zh', prompt=heading(row['before'],1), hint=row['prompts'][0], answer=row['input'], explanation='', correctFeedback=heading(row['feedback'],2), indicator='挑战题', skipLabel='跳过', characterResource=c.resource(source[character_index]['content']['character']['image']['svg'],'image')))
assert len(questions) == 16
reward = read('after-settlement.json')
heart_resources = [c.resource(m['src'], 'home') for m in reward['media']]
assert len(heart_resources) == 5
result = read('settlement-visual.json')
lesson = dict(id='general-practice-1', title='英语练习', questions=questions, initialKeyboardForTiles=True,
    deferredSpeech=[dict(id='general-practice-speech', beforeQuestionID='general-practice-inserted', title='朗读下面的句子', phrase=speech['prompt'], audioResource=c.resource(speech['tts'],'speech'), declineLabel='现在不做口语题', closedTitle='麦克风已关闭', closedBody='将在 15 分钟后恢复')],
    interludes=[dict(id='general-practice-challenge-intro', afterQuestionID='general-practice-q12', text='哎哟不错哦！要不要玩点刺激的？')],
    reviewInterlude=dict(id='general-practice-review-intro', afterQuestionID=questions[-1]['id'], text='一起来复习一下之前你不太熟练的部分吧！'),
    settlement=[dict(id='general-practice-result', kind='result', title=result['title'], body=result['body'], continueLabel='继续', secondaryLabel='回顾本单元', retryLabel='重新练习', experience=result['experience'], observedAccuracy=result['accuracy'], observedMistakes=1, accuracyLabel='棒棒哒！'),
                dict(id='general-practice-heart', kind='practice_heart', title='你又获取了一颗红心！', body='学习新单元需要红心！', continueLabel='继续', secondaryLabel='回顾本单元', retryLabel='重新练习', heartResources=heart_resources),
                dict(id='general-practice-profile', kind='profile', title='来创建你的个人档案吧！', body='创建档案就能保存学习进度，随时都可以继续免费学习后续内容。', continueLabel='稍后再说', secondaryLabel='创建档案')])
fixture = dict(provenance=dict(source='Actual GLOBAL_PRACTICE 16 graded, speech-decline insertion, challenge replacements, one wrong and review, result and heart reward', evidence=['projects/duolingo-web/evidence/english-general-practice-v1/README.md','projects/duolingo-web/evidence/english-general-practice-native-v1/source-probe/wrong-assist-exit.json'], unknown='Adaptive selection, normal oral, new instances, general reward cap/score rules, full pixels and actual acoustic equality; original SVGs for visually identified inserted/replacement characters are not proof of exact animation frames.'),
    data=dict(candidate_course=dict(id='duolingo-en-zh-global-practice', title='英语练习', speechLanguage='en', interfaceLanguage='zh', mistakeHeartCost=0, lessons=[lesson])))
for path, value in [(BASE/'fixture-reference-en-zh-general-practice-v3.json',fixture), (BUNDLE/'general-practice.json',fixture), (BASE/'reference-assets-en-zh-general-practice-v3.json',list(c.resources.values()))]:
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(dict(graded_questions=len(questions), resources=len(c.resources))))
