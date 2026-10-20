"""Compare executed avatar persistence/selection facts with actually observed source states."""
import argparse
import json
from pathlib import Path

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--observed', required=True)
parser.add_argument('--preferences', required=True)
parser.add_argument('--out', required=True)
args = parser.parse_args()
base = Path(__file__).resolve().parent / 'evidence/english-avatar-save-v1'
native = json.loads(Path(args.observed).read_text())
prefs = json.loads(Path(args.preferences).read_text())
rows = []


def check(name, expected, actual):
    rows.append(dict(id=name, expected=expected, actual=actual,
                     status='pass' if actual == expected else 'fail'))


check('driver_completed', None, native.get('failure'))
for stem in ['saved', 'reloaded', 'back-confirm']:
    source = json.loads((base / 'source' / (stem + '.json')).read_text())
    state = native.get('states', {}).get('avatar-save-' + stem, {})
    elements = state.get('elements', {})
    radios = [a for a in source['actions'] if a['role'] == 'radio']
    for i, radio in enumerate(radios):
        check(stem + '-checked-' + str(i), radio['checked'],
              elements.get('avatar-skin-' + str(i), {}).get('checked'))
    done = next(a for a in source['actions'] if a['name'] == '完成')
    check(stem + '-done-enabled', done['enabled'], elements.get('avatar-done', {}).get('enabled'))
    for label, identifier in [('继续编辑虚拟头像', 'avatar-keep'), ('放弃编辑虚拟头像', 'avatar-discard')]:
        check(stem + '-' + identifier, any(a['name'] == label for a in source['actions']), identifier in elements)
    title = next(t['text'] for t in source['text_runs'] if '虚拟头像' in t['text'] and '修改' in t['text'])
    check(stem + '-edit-title', True, title in state.get('accessible_text', []))
source_reload = json.loads((base / 'source/reloaded.json').read_text())
selected = [i for i, a in enumerate(a for a in source_reload['actions'] if a['role'] == 'radio') if a['checked']]
assert len(selected) == 1
check('saved-value-survives-restart-and-discard', selected[0], prefs.get('avatarSkin'))
source_discard = json.loads((base / 'source/discarded.json').read_text())
check('discard-source-is-404', True, 'Error 404' in source_discard['snapshot'])
check('discard-native-is-404', True, 'Error 404' in native.get('states', {}).get('avatar-save-discarded', {}).get('accessible_text', []))
canvas = json.loads((base / 'canvas/observation.json').read_text())
for source in canvas['rows']:
    index = source['index']
    check('actual-selection-' + str(index), source['checked'] == 'true',
          native.get('states', {}).get('avatar-native-skin-' + str(index), {}).get('elements', {}).get('avatar-skin-' + str(index), {}).get('checked'))
result = dict(kind='source_derived_avatar_flow', rows=rows,
              limits=['Selected/dirty/save/reload/discard facts only; not visual/audio/motion equality or other avatar categories'])
with Path(args.out).open('x') as stream:
    json.dump(result, stream, ensure_ascii=False, indent=2)
    stream.write('\n')
print(json.dumps({'pass': sum(r['status'] == 'pass' for r in rows), 'fail': sum(r['status'] == 'fail' for r in rows)}))
raise SystemExit(0 if all(r['status'] == 'pass' for r in rows) else 1)
