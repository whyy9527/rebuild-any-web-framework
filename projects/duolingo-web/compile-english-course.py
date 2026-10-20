"""Compile UI-confirmed English source into a Swift-readable fixture and asset manifest."""
import hashlib
import json
from pathlib import Path
import re
from collections import Counter, defaultdict, deque

BASE = Path(__file__).resolve().parent
EV = BASE / 'evidence/english-v1'
def read(name): return json.loads((EV / name).read_text())
def label(text): return re.sub(r'^\d\s*|\s*\d$', '', text).strip()
resources = {}
def resource(url, kind):
    assert url.startswith('https://') and '?' not in url
    domains = {'speech': 'https://d1vq87e9lcf771.cloudfront.net/',
               'image': 'https://d2pur3iezf4d1j.cloudfront.net/images/',
               'avatar': 'https://simg-ssl.duolingo.com/world-characters/avatars/',
               'home': 'https://d35aaqx5ub95lt.cloudfront.net/'}
    assert url.startswith(domains[kind])
    stem = 'en-' + kind + '-' + hashlib.sha256(url.encode()).hexdigest()[:20]
    resources[stem] = {'url': url, 'kind': kind, 'name': stem,
                       'source_file': stem + ('.mp3' if kind == 'speech' else '.svg')}
    return stem + '.mp3' if kind == 'speech' else stem
def compile_word_bank(choices, texts, answer):
    assert Counter(texts) == Counter(v['text'] for v in choices)
    source_items = defaultdict(deque)
    for choice in choices: source_items[choice['text']].append(choice)
    words = []
    available = defaultdict(deque)
    for j, text in enumerate(texts):
        choice = source_items[text].popleft()
        item = {'id': f'word-{j}', 'text': text}
        if choice.get('tts'): item['audioResource'] = resource(choice['tts'], 'speech')
        words.append(item); available[text].append(item['id'])
    # Equal text can occur twice in the visible bank. Each occurrence has its
    # own identity and can be selected once; never collapse it to a dictionary.
    return words, [available[text].popleft() for text in answer]

def compile_questions(source, rows, dialogues, prefix='en-zh-q'):
    questions = []
    for record in source['challenges']:
        i, c = record['index'], record['content']; row = rows[i]
        q = {'id': f'{prefix}{i}', 'prompt': row['heading'], 'sourceType': c['type'],
             'newWord': '新单词' in row['before'], 'explanation': c.get('solutionTranslation', ''),
             'sourceLanguage': c.get('sourceLanguage', 'en')}
        if c.get('tts'): q['audioResource'] = resource(c['tts'], 'speech')
        if c.get('slowTts'): q['slowAudioResource'] = resource(c['slowTts'], 'speech')
        if c.get('character'): q['characterResource'] = resource(c['character']['image']['svg'], 'image')
        if c['type'] in ('select', 'assist', 'dialogue'):
            q['kind'] = 'choice'
            texts = [label(t) for t in re.findall(r'- radio "([^"]+)"', row['before'])]
            choices = {v if isinstance(v, str) else v['phrase']: v for v in c['choices']}
            assert len(texts) == len(choices) and set(texts) == set(choices)
            answer = c['choices'][c['correctIndex']]
            answer = answer if isinstance(answer, str) else answer['phrase']
            checked = [label(t) for t in re.findall(r'- radio "([^"]+)" \[checked\]', row['feedback'])]
            assert checked == [answer] and '正确答案：' not in row['feedback']
            q['options'] = []
            for j, text in enumerate(texts):
                item = {'id': f'option-{j}', 'text': text}; value = choices[text]
                if isinstance(value, dict):
                    if value.get('tts'): item['audioResource'] = resource(value['tts'], 'speech')
                    if value.get('svg'): item['imageResource'] = resource(value['svg'], 'image')
                q['options'].append(item)
            q['answer'] = next(v['id'] for v in q['options'] if v['text'] == answer)
            if c['type'] == 'assist':
                q['hint'] = c['prompt']
                clips = list(dict.fromkeys(m['src'] for m in row.get('media', []) if m['src'].startswith('https://d1vq87e9lcf771.cloudfront.net/')))
                assert len(clips) == 1
                next(v for v in q['options'] if v['id'] == q['answer'])['audioResource'] = resource(clips[0], 'speech')
            if c['type'] == 'dialogue':
                d = dialogues[str(i)]; q['hint'] = d['prompt']
                q['dialogueAvatars'] = [resource(a['src'], 'avatar') for a in row['images']]
                clip = row['media_before'][-1]['src']; assert clip == d['observed_speech']
                q['audioResource'] = resource(clip, 'speech')
        elif c['type'] == 'orderTapComplete':
            q['kind'] = 'word_tiles'
            texts = [v.strip() for v in row['word_bank']]
            answer = [t['text'] for t in c['displayTokens'] if t['isBlank']]
            assert [a['word'] for a in row['actions']] == answer
            q['words'], q['answer_words'] = compile_word_bank(c['choices'], texts, answer)
            blanks = [j for j,t in enumerate(c['displayTokens']) if t['isBlank']]
            q['completionPrefix'] = ''.join(t['text'] for t in c['displayTokens'][:blanks[0]])
            q['completionSuffix'] = ''.join(t['text'] for t in c['displayTokens'][blanks[-1]+1:])
            q['indicator'] = '新词形'
        elif c['type'] in ('translate', 'listenTap'):

            q['kind'] = 'word_tiles'
            if c['type'] == 'translate': q['hint'] = c['prompt']
            texts = [v.strip() for v in row['word_bank']]
            answer = [c['choices'][j]['text'] for j in c['correctIndices']]
            assert [a['word'] for a in row['actions']] == answer
            q['words'], q['answer_words'] = compile_word_bank(c['choices'], texts, answer)
        elif c['type'] == 'match':
            q['kind'] = 'matching'
            controls = [label(t) for t in re.findall(r'- button "(\d[^"\n]+)"', row['before'])]
            pairs = {p['fromToken']: p for p in c['pairs']}; assert len(controls) == len(pairs)*2
            q['pairs'] = [{'id': f'pair-{j}', 'left': t, 'right': pairs[t]['learningToken'],
                           'audioResource': resource(pairs[t]['tts'], 'speech')} for j, t in enumerate(controls[:len(pairs)])]
            q['rightOrder'] = [next(p['id'] for p in q['pairs'] if p['right'] == t) for t in controls[len(pairs):]]
        else: raise ValueError(c['type'])
        questions.append(q)
    return questions

def build_first_fixture():
    source = read('first-session.json')['session']
    rows = {}
    for n in (1, 2, 3):
        for row in read(f'replay-{n:02}.json')['observed']:
            if 'feedback' in row: rows[row['index']] = row
    # Actual initial choice order plus the separately accepted retry, not a fake
    # positive submission of question 0 on the original first attempt.
    rows[0] = {'before': read('first-session.json')['initial'],
               'heading': '哪个是“咖啡”呢？', 'feedback': read('review-answer.json')['feedback']}
    dialogues = read('dialogue-public-ui.json')['questions']
    questions = compile_questions(source, rows, dialogues)
    course = {'id': 'duolingo-en-zh-unit-1', 'title': '提供或接受饮料', 'speechLanguage': 'en',
              'interfaceLanguage': 'zh', 'lessons': [{'id': 'lesson-1', 'title': 'Lesson 1 of 4', 'questions': questions}]}
    home_source = json.loads((BASE/'evidence/english-home-v2/configuration-source.json').read_text())
    course['home'] = {k: v for k, v in home_source.items() if k != 'resources'}
    course['home']['flagResource'] = resource(home_source['resources']['flag'], 'home')
    course['home']['pronunciationResource'] = resource(home_source['resources']['pronunciation'], 'home')
    course['pathNodes'] = [{'kind': 'lesson', 'lessonIDs': ['lesson-1'], 'lessonCount': 4}] + [
        {'kind': kind, 'lessonIDs': []} for kind in home_source['pathKinds'][1:]]
    fixture = {'data': {'candidate_course': course}, 'provenance': {
        'source': 'Actual anonymous en/zh first lesson; option order, answers and word banks UI-confirmed; question 0 accepted on mistake review',
        'evidence': ['projects/duolingo-web/evidence/english-v1/first-session.json',
                     'projects/duolingo-web/evidence/english-v1/dialogue-public-ui.json',
                     'projects/duolingo-web/evidence/english-home-v2/configuration-source.json'] +
                    [f'projects/duolingo-web/evidence/english-v1/replay-{n:02}.json' for n in (1,2,3)],
        'unknown': 'Later lessons, homepage migration, full completion chain, first-error tutorial, encouragement scheduling, animation and sound output remain incomplete; no fake later lessons added'}}
    return fixture

if __name__ == '__main__':
    fixture = build_first_fixture()
    (BASE/'fixture-reference-en-zh-v1.json').write_text(json.dumps(fixture, ensure_ascii=False, indent=2)+'\n')
    (BASE/'reference-assets-en-zh-v1.json').write_text(json.dumps(list(resources.values()), ensure_ascii=False, indent=2)+'\n')
    print(f"Compiled {len(fixture['data']['candidate_course']['lessons'][0]['questions'])} actual questions and {len(resources)} source resources; full frontend equivalence pending")
