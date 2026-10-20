"""Compile the actual six-lesson quests snapshot without changing prior fixtures."""
import json
import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
source = ROOT / 'projects/duolingo-web/evidence/english-quests-v1/source'
layout = json.loads((source / 'layout.raw.json').read_text())
countdowns = [row['text'] for row in layout['text'] if row['text'].endswith(' 小时')]
assert len(countdowns) == 1
progress = layout['progress']
assert len(progress) == 1
fixture = json.loads((ROOT / 'projects/duolingo-web/fixture-reference-en-zh-v10.json').read_text())
course = fixture['data']['candidate_course']
seed = json.loads((ROOT / 'projects/duolingo-web/evidence/english-pronunciation-v2/progress-source.json').read_text())
completed = len(seed['completedLessons'][course['id']])
snapshot = next(row for row in course['home']['progressSnapshots'] if row['completedLessons'] == completed)
assert snapshot['questProgress'] == int(progress[0]['value'])
assert snapshot['questTarget'] == int(progress[0]['max'])
snapshot['questCountdown'] = countdowns[0]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--out', default='projects/duolingo-web/fixture-reference-en-zh-v11.json')
out = ROOT / parser.parse_args().out
out.parent.mkdir(parents=True, exist_ok=True)
with out.open('x') as stream:
    json.dump(fixture, stream, ensure_ascii=False, indent=2)
    stream.write('\n')
print(json.dumps({'completed_lessons': completed, 'countdown': countdowns[0], 'limitation': 'Observed snapshot; no timer/reset algorithm inferred'}))
