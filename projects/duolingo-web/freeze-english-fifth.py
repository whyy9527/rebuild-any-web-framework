"""Append source-derived fifth-lesson requirements; preserve incomplete dimensions."""
import json
from pathlib import Path
BASE = Path(__file__).resolve().parent
fixture = json.loads((BASE/'fixture-reference-en-zh-v6.json').read_text())
lesson = fixture['data']['candidate_course']['lessons'][4]
EV = 'projects/duolingo-web/evidence/english-next-node-v1/'
trajectory = json.loads((BASE/'evidence/english-next-node-v1/trajectory.json').read_text())
requirements = []
def add(state, suffix, kind, evidence, **fields):
    requirements.append(dict(id=state+'-'+suffix, state=state, kind=kind,
                             evidence=[EV+n for n in evidence], **fields))
for q, source in zip(lesson['questions'], [s for s in trajectory['observed_states'] if s['kind'] != 'speaking_deferred']):
    refs = [source['evidence']]+([source['acceptance_evidence']] if source.get('acceptance_evidence') else [])
    add(q['id'], 'heading', 'accessible_text', refs, text=q['prompt'])
    if q.get('hint'): add(q['id'], 'prompt', 'accessible_text', refs, text=q['hint'])
    for j, word in enumerate(q.get('words', [])):
        add(q['id'], 'word-'+str(j), 'accessible_text', refs, text=word['text'])
    if q['kind'] == 'text_entry':
        for field in ['completionPrefix', 'completionSuffix']:
            if q[field].strip(): add(q['id'], field, 'accessible_text', refs, text=q[field].strip())
    # q7 is rejected on its first presentation; accepted feedback only on review.
    feedbackState = q['id']+'-review-feedback' if source['id'] == 'q7' else q['id']+'-feedback'
    if q.get('correctFeedback'):
        add(feedbackState, 'feedback', 'accessible_text', refs+([source['review_evidence']] if source.get('review_evidence') else []), text=q['correctFeedback'])
    for dimension in ['visual', 'interaction-branches', 'actual-audio']:
        add(q['id'], dimension, 'pending', refs,
            description='Full source/native '+dimension+' equality not established by text or path completion')
speech = lesson['deferredSpeech'][0]
for field in ['title', 'phrase', 'declineLabel']:
    add(speech['id'], field, 'accessible_text', ['speak-entry.json'], text=speech[field])
for field in ['closedTitle', 'closedBody']:
    add(speech['id']+'-closed', field, 'accessible_text', ['speak-declined.json'], text=speech[field])
add(speech['id'], 'recording-recognition', 'pending', ['speak-entry.json'], description='Recording, recognition and timer expiry unobserved/unimplemented; deferred speech must not be counted correct')
add(lesson['reviewInterlude']['id'], 'text', 'accessible_text', ['after-original14.json'], text=lesson['reviewInterlude']['text'])
for field in ['heart_decremented_once', 'unmatched_remains_available', 'wrong_pair_marked_incorrect']:
    add('en-zh-l5-q8-wrong', field, 'interaction_boolean', ['listen-match8.json'], field=field, expected=True)
for page, refs in zip(lesson['settlement'], [['complete.json'], ['after-complete-settled.json'], ['five-gems.json'], ['five-gems.json']]):
    for field in ['title', 'body']:
        if page.get(field): add(page['id'], field, 'accessible_text', refs, text=page[field])
    add(page['id'], 'next', 'interaction_boolean', refs, field='next_state_reached', expected=True)
    if page.get('secondaryLabel'):
        add(page['id'], 'secondary', 'interaction_boolean', refs, field='secondary_action_available', expected=True)
    add(page['id'], 'visual-audio', 'pending', refs, description='Same-state source/native image and actual acoustic equality remain unverified')
contract = dict(revision='actual-en-zh-fifth-v1', scope='Full captured fifth trajectory; source formulas and unvisited branches remain unknown', requirements=requirements)
(BASE/'frontend-english-fifth-v1.json').write_text(json.dumps(contract, ensure_ascii=False, indent=2)+'\n')
previous = json.loads((BASE/'frontend-english-v9.json').read_text())
previous.update(revision='actual-en-zh-frontends-v10', scope='Preserves v9; adds full captured fifth trajectory including ungraded deferred speech, typed review and settlement', requirements=previous['requirements']+requirements)
(BASE/'frontend-english-v10.json').write_text(json.dumps(previous, ensure_ascii=False, indent=2)+'\n')
print(len(requirements), 'fifth requirements;', len(previous['requirements']), 'product requirements (not a product result)')
