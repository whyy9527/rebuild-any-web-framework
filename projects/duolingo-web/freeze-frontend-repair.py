"""Extend v79 with named noninteractive geometry from its frozen source evidence.

This diagnostic extension was added during repair, not preregistered as an RSI
effect metric. Original whole-image requirements and all tolerances are retained.
"""
import argparse
import json
from pathlib import Path

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--out-dir', required=True)
a = p.parse_args()
out = Path(a.out_dir)
out.mkdir(parents=True, exist_ok=False)
base = Path('projects/duolingo-web')
source = base / 'evidence/english-unit12-lesson4-v1'
contract = json.loads((base / 'frontend-english-v79.json').read_text())
aliases = json.loads((source / 'aliases.json').read_text())
prior = contract['requirements'][:]
added = []
for name in ['q6-before', 'q12-before', 'q12-feedback', 'after-achievement']:
    evidence = source / 'source' / (name + '.json')
    observed = json.loads(evidence.read_text())
    state = 'unit12-l4-' + name
    title = next(t for t in observed['text_runs'] if t['text'].startswith('用中文') or t['text'] == '来创建你的个人档案吧！')
    facts = [('heading-run', 'settlement-title' if name == 'after-achievement' else 'question-title', title['rect'])]
    canvas = next((m for m in observed['media'] if m['tag'] == 'CANVAS'), None)
    if canvas:
        facts.append(('character-canvas', 'question-character', canvas['rect']))
    if name == 'after-achievement':
        facts.append(('profile-art', 'settlement-profile-art', observed['background_media'][0]['rect']))
    for suffix, native, rect in facts:
        key = state + '-' + suffix
        aliases[state][key] = native
        added.append(dict(id=key, state=state, kind='element_geometry', element=key,
                          rect=rect, tolerance_points=0, evidence=[str(evidence)]))
contract['requirements'] += added
contract.update(revision='english-v80', parent_revision='english-v79', changes=[
    'Retain all v79 requirements; expose noninteractive heading glyph, actual transformed character canvas and CSS background profile art geometry, previously only covered by failing whole images.'])
assert contract['requirements'][:len(prior)] == prior
assert len(added) == 8
for name, data in [('contract.json', contract), ('aliases.json', aliases)]:
    (out / name).write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')
print(json.dumps(dict(inherited=len(prior), added=len(added))))
