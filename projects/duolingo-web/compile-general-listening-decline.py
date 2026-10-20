"""Compile the executed listening/speech-decline instance, not adaptive rules."""
import hashlib
import importlib.util
import json
from pathlib import Path
import re

BASE = Path(__file__).resolve().parent
EV = BASE / 'evidence/english-general-listening-decline-v1'
spec = importlib.util.spec_from_file_location('english', BASE / 'compile-english-course.py')
c = importlib.util.module_from_spec(spec)
spec.loader.exec_module(c)


def read(name):
    return json.loads((EV / name).read_text())


def heading(snapshot, level):
    return re.search(r'heading "([^"\n]+)" \[level='+str(level)+r'\]', snapshot).group(1)


def effect(url):
    assert url.startswith(('https://d35aaqx5ub95lt.cloudfront.net/sounds/', 'https://simg-ssl.duolingo.com/videos/sound/Match_Correct_')) and '?' not in url
    name = 'en-effect-'+hashlib.sha256(url.encode()).hexdigest()[:20]
    c.resources[name] = dict(url=url, kind='feedback', name=name, source_file=name+'.mp3')
    return name+'.mp3'


source = read('session.json')['session']['challenges']
rows = read('replay-to-tap.json')['observed']
questions = []
for index in range(7):
    raw, row = source[index]['content'], rows[index]
    q = dict(id=f'general-listening-prefix-{index}', prompt=heading(row['before'], 1), sourceType=raw['type'], explanation='')
    if row.get('feedback'):
        assert row['identity']['matches']
        q['correctFeedback'] = heading(row['feedback'], 2)
    for field, target in [('tts', 'audioResource'), ('slowTts', 'slowAudioResource')]:
        if raw.get(field):
            q[target] = c.resource(raw[field], 'speech')
    if raw.get('character'):
        q['characterResource'] = c.resource(raw['character']['image']['svg'], 'image')
    if raw['type'] == 'listenMatch':
        pairs = [dict(id=str(p['left_index']), left=str(p['left_index']+1), right=p['translation'], audioResource=c.resource(p['played_audio'][0], 'speech')) for p in row['pair_audio_order']]
        q.update(kind='matching', pairs=pairs, rightOrder=[next(p['id'] for p in pairs if p['right']==text) for text in row['right_text']])
        q['matchedAudioResources'] = [effect(url) for url in dict.fromkeys(m['src'] for m in row['media'] if m['src'].startswith('https://simg-ssl.duolingo.com/videos/sound/Match_Correct_'))]
    elif raw['type'] == 'assist':
        q.update(kind='choice', hint=raw['prompt'], options=[dict(id=str(i), text=text) for i, text in enumerate(row['identity']['actual']['choices'])])
        q['answer'] = next(o['id'] for o in q['options'] if o['text']==raw['choices'][raw['correctIndex']])
    elif raw['type'] == 'listenIsolation':
        sentence = ''.join(t['value'] for t in raw['tokens'])
        blank = ''.join(t['value'] for t in raw['tokens'][raw['blankRangeStart']:raw['blankRangeEnd']])
        q.update(kind='choice', hint=sentence.replace(blank, '__'), explanation='意思是： '+raw['solutionTranslation'],
                 options=[dict(id=str(o['index']), text=str(o['index']+1), audioResource=c.resource(o['played_audio'][0], 'speech'), imageResource=f'en-seventh-isolation-wave-{o["index"]+1}') for o in row['audio_options']],
                 answer=str(next(o['index'] for o in row['audio_options'] if o['text']==raw['options'][raw['correctIndex']]['text'])))
    else:
        assert raw['type'] in ['translate', 'listenTap']
        choices = [dict(text=v) if isinstance(v, str) else v for v in raw['choices']]
        answer = [choices[i]['text'] for i in raw['correctIndices']]
        texts = row.get('word_bank') or re.findall(r'- button "([^"\n]+)"', read('tap-before.json')['snapshot'])[:len(choices)]
        words, ids = c.compile_word_bank(choices, texts, answer)
        q.update(kind='word_tiles', words=words, answer_words=ids)
        if raw['type'] == 'translate':
            q.update(hint=raw['prompt'], sourceLanguage=raw.get('sourceLanguage', 'en'))
        if 'button "使用键盘"' in row['before']:
            q.update(keyboardAnswer=raw.get('correctSolutions', [raw['prompt']])[0], keyboardPrompt='键入你听到的内容' if raw['type']=='listenTap' else q['prompt'])
    urls = list(dict.fromkeys(m['src'] for m in row.get('media', []) if m['src'].startswith('https://d35aaqx5ub95lt.cloudfront.net/sounds/')))
    if urls:
        assert len(urls) == 1
        q['correctFeedbackAudioResource'] = effect(urls[0])
    if 'button "跳过"' in row['before']:
        q['skipLabel'] = '跳过'
    questions.append(q)

questions[-1]['listeningDecline'] = dict(label='现在不做听力题', title='听力题已跳过', body='将在 15 分钟后恢复')
questions[-1]['listeningDecline']['imageResource'] = c.resource('https://d35aaqx5ub95lt.cloudfront.net/images/d01837d668b592b96aa33ecce8459d77.svg', 'home')
translated = []
for item in read('trace.json')['subsequent_graded']:
    row = read(item['receipt'])
    assert row['rejected'] is False
    q = dict(id=item['id'], prompt=heading(row['before'], 1), sourceType='translate', explanation='',
             hint=row['prompts'][0], sourceLanguage='en' if heading(row['before'], 1).startswith('用中文') else 'zh',
             correctFeedback=heading(row['feedback'], 2), skipLabel='跳过')
    if row.get('clicks'):
        q['sourceLanguage'] = 'en' if q['prompt'].startswith('用中文') else 'zh'
        q['words'], q['answer_words'] = c.compile_word_bank([dict(text=t) for t in row['choices']], row['choices'], [a['word'] for a in row['clicks']])
        q['kind'] = 'word_tiles'
    else:
        q.update(kind='text_entry', answer=row['input'])
    if item['id'].split('-')[-2:] in [['hot', 'tea'], ['ice', 'water'], ['no', 'water']]:
        q['indicator'] = '挑战题'
    matches = [s['content'] for s in source if s['content'].get('prompt') == q['hint']]
    if len(matches) == 1:
        raw = matches[0]
        if raw.get('character'):
            q['characterResource'] = c.resource(raw['character']['image']['svg'], 'image')
        if raw.get('tts'):
            q['audioResource'] = c.resource(raw['tts'], 'speech')
    translated.append(q)

speech = source[7]['content']
questions += translated[1:]
result = json.loads((BASE / 'fixture-reference-en-zh-general-practice-v2.json').read_text())['data']['candidate_course']['lessons'][0]['settlement']
pages = [dict(result[0], title='完美！', body='你练习全对，无错完成本单元', observedAccuracy=100, observedMistakes=0, accuracyLabel='超级棒'), result[-1]]
lesson = dict(id='general-listening-decline-1', title='英语练习', questions=questions,
    listeningDeclineReplacements={questions[6]['id']: translated[0]},
    deferredSpeech=[dict(id='general-listening-decline-speech', beforeQuestionID=translated[1]['id'],
        title='朗读下面的句子', phrase=speech['prompt'], audioResource=c.resource(speech['tts'], 'speech'),
        declineLabel='现在不做口语题', closedTitle='麦克风已关闭', closedBody='将在 15 分钟后恢复')],
    interludes=[dict(id='general-listening-decline-challenge', afterQuestionID='general-listening-decline-goodbye', text='哎哟不错哦！要不要玩点刺激的？')], settlement=pages)
fixture = dict(provenance=dict(source='Executed listenTap decline, inserted translation, speech decline and adaptive translation replacements',
    evidence=['projects/duolingo-web/evidence/english-general-listening-decline-v1/README.md'],
    unknown='Diagnostic observed-instance fixture; non-decline future, adaptive selection, replacement characters/audio not identified by exact source content, actual recovery timer and full pixels remain unverified.'),
    data=dict(candidate_course=dict(id='duolingo-en-zh-global-practice-listening-decline', title='英语练习', speechLanguage='en', interfaceLanguage='zh', mistakeHeartCost=0, lessons=[lesson])))
for path, value in [(BASE/'fixture-reference-en-zh-general-listening-decline-v1.json', fixture),
                    (BASE/'reference-assets-en-zh-general-listening-decline-v1.json', list(c.resources.values()))]:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n')
print(json.dumps(dict(questions=len(questions), replacement_count=1, resources=len(c.resources))))
