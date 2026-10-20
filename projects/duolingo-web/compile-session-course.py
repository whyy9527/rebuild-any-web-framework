"""Append a UI-confirmed public session to the existing frozen course.

API answers and UI order remain separate sources. Missing/rejected feedback,
unknown types or mismatched word sets stop compilation rather than invent data.
Run from repository root; v4 stays immutable.
"""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import re


def label(text):
    return re.sub(r'^\d\s*|\s*\d$', '', text).strip()


def compile_lesson(observation, resource):
    rows = {row['index']: row for row in observation['observed']}
    questions = []
    for record in observation['session']['challenges']:
        c, row = record['content'], rows[record['index']]
        assert row.get('feedback') and 'Correct solution' not in row['feedback']
        assert '- heading ' in row['feedback'], 'Feedback confirmation missing'
        q = {'id': f"l3-q{record['index'] + 1}", 'prompt': row['heading'],
             'newWord': bool(c.get('newWords')), 'explanation': ''}
        if c.get('tts'):
            q['audioResource'] = resource(c['tts'])
        q['sourceLanguage'] = c.get('sourceLanguage', observation['session']['fromLanguage'])
        if c['type'] in ('select', 'assist'):
            q['kind'] = 'choice'
            texts = [label(text) for text in re.findall(r'- radio "([^"]+)"', row['before'])]
            source = {v if isinstance(v, str) else v['phrase']: v for v in c['choices']}
            assert set(texts) == set(source) and len(texts) == len(source)
            answer = c['choices'][c['correctIndex']]
            answer = answer if isinstance(answer, str) else answer['phrase']
            checked = re.findall(r'- radio "([^"]+)" \[checked\]', row['feedback'])
            assert len(checked) == 1 and label(checked[0]) == answer
            q['options'] = []
            for index, text in enumerate(texts, 1):
                item = {'id': f'option-{index}', 'text': text}
                value = source[text]
                if isinstance(value, dict) and value.get('tts'):
                    item['audioResource'] = resource(value['tts'])
                # Assist uses a voice clip absent from the sanitized API; retain only actual invocation.
                if c['type'] == 'assist' and text == answer and len(row['media']) == 1:
                    item['audioResource'] = resource(row['media'][0]['src'])
                q['options'].append(item)
            q['answer'] = next(v['id'] for v in q['options'] if v['text'] == answer)
            if c['type'] == 'assist':
                q['hint'] = c['prompt']
        elif c['type'] == 'translate':
            q.update(kind='word_tiles', hint=c['prompt'])
            texts = [v.strip() for v in row['word_bank']]
            source = {v['text']: v for v in c['choices']}
            assert len(source) == len(c['choices']), 'Duplicate word handling not yet observed'
            assert sorted(texts) == sorted(source)
            q['words'] = []
            for index, text in enumerate(texts, 1):
                item = {'id': f'word-{index}', 'text': text}
                if source[text].get('tts'):
                    item['audioResource'] = resource(source[text]['tts'])
                q['words'].append(item)
            answer = [c['choices'][i]['text'] for i in c['correctIndices']]
            assert [a['word'] for a in row['actions']] == answer
            q['answer_words'] = [next(v['id'] for v in q['words'] if v['text'] == text) for text in answer]
        elif c['type'] == 'match':
            q['kind'] = 'matching'
            controls = [label(t) for t in re.findall(r'- button "(\d[^"\n]+)"', row['before'])]
            assert len(controls) == 2 * len(c['pairs'])
            source = {p['fromToken']: p for p in c['pairs']}
            q['pairs'] = [{'id': f'pair-{i + 1}', 'left': text, 'right': source[text]['learningToken'],
                           'audioResource': resource(source[text]['tts'])} for i, text in enumerate(controls[:len(source)])]
            q['rightOrder'] = [next(p['id'] for p in q['pairs'] if p['right'] == text) for text in controls[len(source):]]
        else:
            raise ValueError('Uncovered challenge type: ' + c['type'])
        questions.append(q)
    return {'id': 'lesson-3', 'title': 'Lesson 3 of 3', 'questions': questions}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--observation', default='projects/duolingo-web/evidence/exploration-v5/third-lesson.json')
    parser.add_argument('--out', default='projects/duolingo-web/fixture-reference-v5.json')
    args = parser.parse_args()
    resources = {}
    def resource(url):
        assert url.startswith('https://d1vq87e9lcf771.cloudfront.net/') and '?' not in url
        name = 'speech-' + hashlib.sha256(url.encode()).hexdigest()[:20] + '.mp3'
        resources[name] = url
        return name
    observation = json.loads(Path(args.observation).read_text())
    fixture = copy.deepcopy(json.loads(Path('projects/duolingo-web/fixture-reference-v4.json').read_text()))
    fixture['data']['candidate_course']['lessons'].append(compile_lesson(observation, resource))
    fixture['provenance']['evidence'].append(args.observation)
    fixture['provenance']['source'] = 'Actual first three lesson instances, third compiled from public session fields AND UI feedback/order'
    fixture['provenance']['unknown'] = 'Later path, randomized instances, interlude implementation, original cue output and full frontend fidelity remain open'
    Path(args.out).write_text(json.dumps(fixture, ensure_ascii=False, indent=2) + '\n')
    Path('projects/duolingo-web/reference-speech-v5.json').write_text(json.dumps(resources, indent=2) + '\n')
    print(json.dumps({'questions': [len(l['questions']) for l in fixture['data']['candidate_course']['lessons']], 'speech_resources': len(resources)}))


if __name__ == '__main__':
    main()
