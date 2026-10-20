"""Extract choice mappings from positive reference feedback, not candidate data."""
import json
from pathlib import Path
import re

base = Path('projects/duolingo-web/evidence/exploration-v4')
entries = {}
for name in ['curriculum-first.json', 'curriculum-second-01.json', 'sound-effects-speech-green.json']:
    source = json.loads((base / name).read_text())
    rows = source.get('observed', [source])
    for index, row in enumerate(rows):
        feedback = row.get('feedback', '')
        checked = re.findall(r'- radio "([^"]+)" \[checked\]', feedback)
        if len(checked) != 1 or 'Correct solution:' in feedback:
            continue
        prompt = row.get('prompt', row.get('before', ''))
        quoted = re.search('“(.+?)”', prompt)
        if quoted:
            english = quoted.group(1)
        elif prompt.startswith('Select the correct meaning: '):
            english = prompt.split(': ', 1)[1]
        else:
            continue
        spanish = re.sub(r'(^\d\s+|\s+\d$)', '', checked[0])
        if english in entries and entries[english]['spanish'] != spanish:
            raise ValueError('Conflicting reference mapping: ' + english)
        entries[english] = {'spanish': spanish, 'evidence': str(base / name), 'step': index}
output = {'source': 'Actual checked choice in positive reference feedback', 'entries': entries,
          'limitations': ['Vocabulary learning is not exploration-policy self-improvement',
                          'Unknown prompts remain unresolved; no candidate answers are read']}
Path('projects/duolingo-web/reference-vocabulary.json').write_text(json.dumps(output, ensure_ascii=False, indent=2) + '\n')
print('Reference-confirmed vocabulary:', len(entries))
