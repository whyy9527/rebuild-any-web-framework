"""Compile actual reference trajectories into the Swift course fixture.

Choice answers come from checked controls in positive reference feedback.
Matching translations are learned from those choices; possessives were then
confirmed by the separately recorded successful phrase-matching run.
"""
import json
from pathlib import Path
import re

BASE = Path('projects/duolingo-web/evidence/exploration-v4')


def label(text):
    return re.sub(r'(^\d\s+|\s+\d$)', '', text)


def main():
    first = json.loads((BASE / 'curriculum-first.json').read_text())
    second = json.loads((BASE / 'curriculum-second-01.json').read_text())
    repaired = json.loads((BASE / 'curriculum-second-02.json').read_text())
    assert first['complete'] and repaired['complete']
    lessons = [first['observed'], second['observed'][:-1] + repaired['observed']]
    vocabulary = {}
    for rows in lessons:
        for row in rows:
            if row['kind'] != 'choice':
                continue
            checked = re.findall(r'- radio "([^"]+)" \[checked\]', row['feedback'])
            assert len(checked) == 1 and 'Correct solution:' not in row['feedback']
            word = re.search('“(.+?)”', row['prompt'])
            word = word.group(1) if word else row['text'].splitlines()[1]
            vocabulary[word] = label(checked[0])
    vocabulary.update({'my ' + key: 'mi ' + value for key, value in list(vocabulary.items())})
    compiled = []
    for lesson, rows in enumerate(lessons, 1):
        questions = []
        for index, row in enumerate(rows, 1):
            assert 'feedback' in row
            lines = row['text'].splitlines()
            heading = next(line for line in lines if line.startswith(('Which one', 'Select the', 'Write this')))
            kind = row['kind']
            question = {'id': f'l{lesson}-q{index}', 'kind': kind, 'prompt': heading,
                        'newWord': 'NEW WORD' in lines, 'explanation': ''}
            if kind == 'choice':
                options = [label(text) for text in re.findall(r'- radio "([^"]+)"', row['before'])]
                assert len(options) == 3
                question['options'] = [{'id': 'option-' + str(i + 1), 'text': text} for i, text in enumerate(options)]
                answer = label(re.findall(r'- radio "([^"]+)" \[checked\]', row['feedback'])[0])
                question['answer'] = next(item['id'] for item in question['options'] if item['text'] == answer)
                if heading == 'Select the correct meaning':
                    question['hint'] = lines[lines.index(heading) + 1]
            elif kind == 'matching':
                controls = re.findall(r'- button "\d (.+?)"', row['before'])
                assert len(controls) == 10
                question['pairs'] = [{'id': 'pair-' + str(i + 1), 'left': text, 'right': vocabulary[text]}
                                     for i, text in enumerate(controls[:5])]
                question['rightOrder'] = [next(pair['id'] for pair in question['pairs'] if pair['right'] == text)
                                          for text in controls[5:]]
            elif kind == 'word_tiles':
                hint = ' '.join(row['hints'])
                question['hint'] = hint
                words = [text for text in re.findall(r'- button "([^"\n]+)"', row['before']) if text not in ['Skip', 'Check']]
                question['words'] = [{'id': 'word-' + str(i + 1), 'text': text} for i, text in enumerate(words)]
                answer = next(english for english, spanish in vocabulary.items() if spanish == hint).split()
                question['answer_words'] = [next(word['id'] for word in question['words'] if word['text'] == text) for text in answer]
            questions.append(question)
        compiled.append({'id': f'lesson-{lesson}', 'title': f'Lesson {lesson} of 3', 'questions': questions})
    fixture = {'data': {'candidate_course': {'id': 'duolingo-es-unit-1', 'title': 'Order at a café', 'speechLanguage': 'es', 'lessons': compiled}},
               'initial_state': {'screen': 'course_entry', 'authenticated': False},
               'provenance': {'evidence': [str(BASE / name) for name in ['curriculum-first.json', 'curriculum-second-01.json', 'curriculum-second-02.json']],
                              'source': 'Actual anonymous English-to-Spanish reference, two complete lesson instances',
                              'unknown': 'Third lesson, later units and original randomization remain to explore and rebuild; not excluded from the goal'}}
    fixture['data']['candidate_course']['pathNodes'] = [
        {'kind': 'lesson', 'lessonIDs': ['lesson-1', 'lesson-2', 'lesson-3']},
        {'kind': 'lesson', 'lessonIDs': []}, {'kind': 'lesson', 'lessonIDs': []},
        {'kind': 'chest', 'lessonIDs': []}, {'kind': 'practice', 'lessonIDs': []},
        {'kind': 'review', 'lessonIDs': []}]
    Path('projects/duolingo-web/fixture-reference-v4.json').write_text(json.dumps(fixture, ensure_ascii=False, indent=2) + '\n')
    print('Compiled observed questions:', [len(lesson['questions']) for lesson in compiled])


if __name__ == '__main__':
    main()
