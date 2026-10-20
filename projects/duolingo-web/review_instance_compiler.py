"""Compile one UI-confirmed result-review question; source instances own ordering."""
import re
import hashlib

def effect_resource(c, url):
    assert url.startswith(('https://d35aaqx5ub95lt.cloudfront.net/sounds/', 'https://simg-ssl.duolingo.com/videos/sound/')) and '?' not in url
    stem = 'en-effect-'+hashlib.sha256(url.encode()).hexdigest()[:20]
    c.resources[stem] = dict(url=url, kind='feedback', name=stem, source_file=stem+'.mp3')
    return stem+'.mp3'

def heading(snapshot, level):
    return re.search(r'heading "([^"\n]+)" \[level='+str(level)+r'\]', snapshot).group(1)

def compile_question(c, effect, raw, row, card, question_id):
    title, _, prompt = card['text'].partition('\n')
    assert row.get('feedback') and not row.get('rejected') and row['identity']['matches']
    q = dict(id=question_id, prompt=row['heading'], sourceType=raw['type'], explanation='',
             correctFeedback=heading(row['feedback'], 2))
    sounds = list(dict.fromkeys(m['src'] for m in row.get('media', []) if m['src'].startswith('https://d35aaqx5ub95lt.cloudfront.net/sounds/')))
    assert len(sounds) <= 1
    if sounds:
        q['correctFeedbackAudioResource'] = effect(sounds[0])
    for src, dst in [('tts', 'audioResource'), ('slowTts', 'slowAudioResource')]:
        if raw.get(src):
            q[dst] = c.resource(raw[src], 'speech')
    if raw.get('character'):
        q['characterResource'] = c.resource(raw['character']['image']['svg'], 'image')
    if raw['type'] == 'listenMatch':
        q.update(kind='matching', pairs=[dict(id=str(p['left_index']), left=str(p['left_index']+1), right=p['translation'],
                    audioResource=c.resource(p['played_audio'][0], 'speech')) for p in row['pair_audio_order']])
        q['rightOrder'] = [next(p['id'] for p in q['pairs'] if p['right'] == text) for text in row['right_text']]
        matched = list(dict.fromkeys(m['src'] for m in row.get('media', []) if m['src'].startswith('https://simg-ssl.duolingo.com/videos/sound/Match_Correct_')))
        if matched:
            assert len(matched) == 4
            q['matchedAudioResources'] = [effect(url) for url in matched]
        answer = ''
        audio = [p['audioResource'] for p in q['pairs']]
    elif raw['type'] == 'assist':
        q.update(kind='choice', hint=raw['prompt'], options=[dict(id=str(j), text=text) for j, text in enumerate(row['identity']['actual']['choices'])])
        q['answer'] = next(o['id'] for o in q['options'] if o['text'] == raw['choices'][raw['correctIndex']])
        answer = raw['choices'][raw['correctIndex']]
        audio = []
    elif raw['type'] == 'select':
        choices=raw['choices'];actual=row['identity']['actual']['choices']
        assert set(actual)=={v['phrase'] for v in choices}
        q.update(kind='choice',options=[])
        for j,text in enumerate(actual):
            v=next(v for v in choices if v['phrase']==text)
            q['options'].append(dict(id=str(j),text=text,imageResource=c.resource(v['svg'],'image'),audioResource=c.resource(v['tts'],'speech')))
        answer=choices[raw['correctIndex']]['phrase'];q['answer']=next(v['id'] for v in q['options'] if v['text']==answer)
        assert row['actions']==[dict(select=answer)]
        audio=[]
    elif raw['type'] == 'dialogue':
        assert prompt.startswith('A：') and '\nB：___' in prompt
        hint = prompt[2:].split('\nB：___')[0]
        visible = row['identity']['actual']['text'].replace('\n', '')
        assert hint.replace(' ', '') in visible.replace(' ', '')
        choices = row['identity']['actual']['choices']
        assert choices == raw['choices']
        q.update(kind='choice', hint=hint, explanation=raw.get('solutionTranslation',''),
                 options=[dict(id=str(j),text=text) for j,text in enumerate(choices)],
                 answer=str(raw['correctIndex']),
                 dialogueAvatars=[c.resource(v['src'],'avatar') for v in row['images']])
        clips=list(dict.fromkeys(m['src'] for m in row.get('media_before',[]) if m.get('src','').startswith('https://d1vq87e9lcf771.cloudfront.net/')))
        assert len(clips)<=1
        if clips:q['audioResource']=c.resource(clips[0],'speech')
        answer=raw['choices'][raw['correctIndex']]
        audio=[]
    elif raw['type'] in ['translate', 'listenTap']:
        if raw['type'] == 'translate':
            q.update(hint=raw['prompt'], sourceLanguage=raw['sourceLanguage'])
        if row.get('text_input'):
            q.update(kind='text_entry', answer=row['text_input']['value'])
            answer = q['answer']
        else:
            choices = [dict(text=v) if isinstance(v, str) else v for v in raw['choices']]
            chosen = [a['word'] for a in row['actions']]
            assert chosen == [choices[j]['text'] for j in raw['correctIndices']]
            words, ids = c.compile_word_bank(choices, [t.strip() for t in row['word_bank']], chosen)
            q.update(kind='word_tiles', words=words, answer_words=ids)
            # Exact canonical answer, including punctuation, comes from current public data.
            answer = raw.get('correctSolutions', [raw['prompt']])[0]
        audio = [q['audioResource']] if raw['type'] == 'listenTap' else []
    elif raw['type'] in ['tapComplete','orderTapComplete']:
        tokens = raw['displayTokens']
        blanks = [i for i, t in enumerate(tokens) if t['isBlank']]
        assert blanks
        chosen = [a['word'] for a in row['actions'] if 'word' in a]
        expected=[t['text'] for t in tokens if t['isBlank']] if raw['type']=='orderTapComplete' else [raw['choices'][i]['text'] for i in raw['correctIndices']]
        assert chosen == expected
        words, ids = c.compile_word_bank(raw['choices'], [t.strip() for t in row['word_bank']], chosen)
        q.update(kind='word_tiles', words=words, answer_words=ids,
                 completionPrefix=''.join(t['text'] for t in tokens[:blanks[0]]),
                 completionSuffix=''.join(t['text'] for t in tokens[blanks[-1]+1:]))
        if raw.get('image'):
            assert raw['image']['svg'] in [v['src'] for v in row['images']]
            q['promptImageResource'] = c.resource(raw['image']['svg'], 'image')
        answer = ''.join(t['text'] for t in tokens)
        audio = []
    elif raw['type'] == 'completeReverseTranslation':
        answer = ''.join(t['text'] for t in raw['displayTokens'])
        assert row['text_input']['value'] == answer and title == '完成翻译' and prompt == raw['prompt']
        q.update(kind='text_entry', hint=raw['prompt'], answer=answer)
        audio = []
    elif raw['type'] == 'listen':
        assert row['text_input']['value'] == raw['prompt']
        q.update(kind='text_entry', answer=raw['prompt'])
        answer = raw['prompt']
        audio = [q['audioResource']]
    elif raw['type'] == 'listenComplete':
        tokens = raw['displayTokens']; blanks = [j for j, t in enumerate(tokens) if t['isBlank']]
        assert len(blanks) == 1
        j = blanks[0]
        q.update(kind='text_entry', answer=row['text_input']['value'],
                 completionPrefix=''.join(t['text'] for t in tokens[:j]),
                 completionSuffix=''.join(t['text'] for t in tokens[j+1:]))
        assert q['answer'] == tokens[j]['text']
        answer = ''.join(t['text'] for t in tokens)
        audio = [q['audioResource']]
    else:
        raise ValueError(raw['type'])
    skips=[a for a in row.get('frontend_before',{}).get('actions',[]) if a['name']=='跳过']
    if skips:
        assert len(skips)==1 and skips[0]['enabled']
        q['skipLabel']=skips[0]['name']
    q['resultReview'] = dict(title=title, prompt=prompt, correctAnswer=answer, audioResources=audio)
    return q
