"""Compile actual en/zh observations, not a synthetic Swift course or coverage claim."""
import json
from pathlib import Path

BASE = Path(__file__).resolve().parent
EVIDENCE = BASE / 'evidence/english-v1'

def read(name):
    return json.loads((EVIDENCE / name).read_text())

def write(name, value):
    (BASE / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')

def evidence(name):
    return 'projects/duolingo-web/evidence/english-v1/' + name

source = read('first-session.json')['session']
assert (source['learningLanguage'], source['fromLanguage']) == ('en', 'zh')
# Keep the failed observations in their original files; choose the final submitted
# observation for each question, never turn an unexecuted question into a pass.
observed = {}
interludes = []
for number in (1, 2, 3):
    name = f'replay-{number:02}.json'
    run = read(name)
    assert run['session'] == source
    interludes.extend(dict(row, evidence=evidence(name)) for row in run['interludes'])
    for row in run['observed']:
        if 'feedback' in row:
            assert 'screenshot_feedback' in row
            observed[row['index']] = dict(row, evidence=evidence(name))
assert set(observed) == set(range(1, 15))
states = []
requirements = []
for record in source['challenges']:
    index = record['index']
    sid = f'en-zh-q{index}'
    if index == 0:
        snapshot = read('first-session.json')['initial']
        refs = [evidence('first-session.json')]
        heading = '哪个是“咖啡”呢？'
        actions = []  # Actual wrong submission is represented separately below.
    else:
        row = observed[index]
        snapshot, heading, actions = row['before'], row['heading'], row['actions']
        refs = [row['evidence'], evidence(row['screenshot_before'])]
    assert heading in snapshot
    states.append({'id': sid, 'source_type': record['content']['type'],
                   'public_content': record['content'], 'reference_snapshot': snapshot,
                   'observed_actions': actions, 'evidence': refs,
                   'candidate_status': 'not_run'})
    requirements.append({'id': sid+'-heading', 'state': sid, 'kind': 'accessible_text',
                         'text': heading, 'evidence': refs})
    for dimension in ('visual', 'interaction', 'audio'):
        requirements.append({'id': sid+'-'+dimension, 'state': sid, 'kind': 'pending',
                             'description': f'Compare actual same-state {dimension}; source observation is not candidate verification',
                             'evidence': refs})
for name in ('first-wrong-and-hearts-intro', 'review-intro', 'review-answer',
             'completion', 'score', 'score-progress', 'streak', 'streak-goal',
             'daily-quest', 'gem-reward', 'profile-prompt', 'home'):
    sid = 'en-zh-'+name
    states.append({'id': sid, 'observation': read(name+'.json'),
                   'evidence': [evidence(name+'.json')], 'candidate_status': 'not_run'})
    requirements.append({'id': sid+'-equivalence', 'state': sid, 'kind': 'pending',
                         'description': 'Business, frontend and sound equivalence for this observed state remain unverified',
                         'evidence': [evidence(name+'.json')]})
for number, row in enumerate(interludes):
    sid = f'en-zh-interlude-{number}'
    states.append({'id': sid, 'observation': row, 'candidate_status': 'not_run'})
    requirements.append({'id': sid+'-equivalence', 'state': sid, 'kind': 'pending',
                         'description': 'Observed encouragement state; visual, timing and audio equivalence not verified',
                         'evidence': [row['evidence']]})
unknowns = [
    'Listening slow playback, keyboard mode and skip-hearing branches',
    'Dialogue hint hover and deliberate wrong dialogue/listening/matching submissions',
    'Reload/resume and abandoning an unfinished lesson',
    'English Guidebook, pronunciation, navigation destinations and subsequent lessons',
    'Original and native acoustic output aligned with real actions',
    'Full screenshot/geometry/font/assets equality; rolling completion digits are not final numeric values',
    'All-correct completion compared with this first-wrong/review trajectory',
]
write('reference-case-en-zh-v1.json', {
    'revision': 'actual-en-zh-first-lesson-v1', 'viewport': {'width': 1200, 'height': 732},
    'scope': 'Actual observed trajectory, not the complete app or a native-ready fixture',
    'states': states, 'interludes': interludes, 'unknowns': unknowns,
    'limitations': ['Dialogue body omitted by original API sanitizer; actual frontend snapshot is retained',
                    'Audio play invocations do not prove acoustic output',
                    'Question 0 deliberately wrong; questions 1..14 accepted; additional retry answered correctly',
                    'Transition after snapshots can contain outgoing animation; stable before snapshots and PNGs are the visual references']})
write('frontend-english-v1.json', {'revision': 'actual-en-zh-frontends-v1',
    'scope': 'Shared reference/native requirements; native English driver not implemented yet',
    'requirements': requirements})
print(f'Compiled {len(states)} source states, {len(requirements)} requirements; native status not_run')
