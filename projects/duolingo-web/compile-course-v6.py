"""Extend frozen v5 with observed interludes and exact source character resources."""
import json
from pathlib import Path
import re

base = Path('projects/duolingo-web')
fixture = json.loads((base / 'fixture-reference-v5.json').read_text())
source = json.loads((base / 'evidence/exploration-v5/third-lesson.json').read_text())
assets = json.loads((base / 'evidence/exploration-v6/character-resources.json').read_text())
by_url = {row['url']: row['name'] for row in assets['resources']}
lesson = fixture['data']['candidate_course']['lessons'][2]
for record, observed, question in zip(source['session']['challenges'], source['observed'], lesson['questions'], strict=True):
    url = record['content'].get('character', {}).get('image', {}).get('svg')
    if url:
        question['characterResource'] = by_url[url]
    question['newWord'] = 'text: New word' in observed['before']
lesson['interludes'] = []
for index, row in enumerate(source['interludes']):
    text = re.search(r'- text: 5 (.+)', row['snapshot']).group(1)
    lesson['interludes'].append({'id': f'third-interlude-{index}',
        'afterQuestionID': f"l3-q{row['before_index']}", 'text': text})
fixture['provenance']['source'] += '; v6 includes actual third-lesson interludes, UI new-word labels and source characters'
fixture['provenance']['evidence'].append('projects/duolingo-web/evidence/exploration-v6/character-resources.json')
fixture['provenance']['unknown'] = 'Interlude schedule observed on one all-correct trajectory; other trajectories, later path, original cues and full frontend fidelity remain open'
(base / 'fixture-reference-v6.json').write_text(json.dumps(fixture, ensure_ascii=False, indent=2) + '\n')
print('Compiled source characters and two observed interludes; v5 remains unchanged')
