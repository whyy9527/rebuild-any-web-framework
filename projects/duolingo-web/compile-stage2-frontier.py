"""Merge actual stage2 exploration, retaining inventories and unfinished actions."""
import argparse
import json
from pathlib import Path
from capabilities.rebuild.discovery import frontier

BASE = Path('projects/duolingo-web')
E = BASE / 'evidence/english-stage2-home-v1'
p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--out-dir', required=True)
out = Path(p.parse_args().out_dir)
out.mkdir(parents=True, exist_ok=False)
history = json.loads((BASE / 'evidence/english-sections-v1/history.json').read_text())
for path in sorted((E / 'source').glob('*.json')):
    source = json.loads(path.read_text())
    actions = source['actions'][:]
    for control in source.get('control_inventory', []):
        if any(a['rect'] == control['rect'] and a.get('href') == control.get('href')
               and a.get('tag') == control.get('tag') for a in actions):
            continue
        actions.append(dict(control, id='inventory-' + str(control['index']),
                            kind='rendered_inventory_only'))
    history['states'].append(dict(id=path.stem, evidence=str(path), actions=actions))
states = {s['id']: s for s in history['states']}
prefix = 'stage2-home-source-02-'

def edge(start, end, key, value, raw, inventory=False):
    start, end = prefix + start, prefix + end
    candidates = [a for a in states[start]['actions'] if a.get(key) == value
                  and (inventory or a.get('kind') != 'rendered_inventory_only')]
    assert len(candidates) == 1, (start, key, value, len(candidates))
    history['transitions'].append(dict(**{'from': start}, to=end,
        action=candidates[0]['id'], outcome='observed', evidence=str(E / raw)))

for start, end, key, value in [
    ('home-before', 'lesson-popover', 'test', 'skill-path-level-0 skill-path-level-skill'),
    ('lesson-popover', 'sections-after-lesson', 'href', '/sections'),
    ('sections-after-lesson', 'lesson-dismiss', 'name', '返回'),
    ('lesson-dismiss', 'story-entry', 'test', 'skill-path-level-1 skill-path-level-story'),
    ('story-entry', 'story-return', 'test', 'home-nav'),
    ('story-return', 'guide', 'test', 'guidebook-button-11'),
    ('guide', 'guide-return', 'test', 'home-nav'),
    ('guide-return', 'radio-entry', 'test', 'skill-path-level-2 skill-path-level-duo_radio'),
    ('radio-entry', 'radio-return', 'test', 'home-nav'),
]:
    edge(start, end, key, value, prefix + end + '.raw.txt', inventory=end == 'radio-entry')

history['limitations'] += [
    'Radio click produced scrolling and additional virtualized inventory, not an observed player.',
    'Reload is a real client action, not server reset. Daily 50/50 to 0/50 cause remains unknown.',
    'Repeated controls in distinct states remain separate; frontier count is not unique requirements.',
    'This recorded adaptive exploration is not matched-budget RSI causal evidence.',
]
for name, data in [('history.json', history), ('frontier.json', frontier(Path.cwd(), history))]:
    (out / name).write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')
print(json.dumps(dict(states=len(history['states']), executed_edges=len(history['transitions']),
                     pending=len(frontier(Path.cwd(), history)['pending']))))
