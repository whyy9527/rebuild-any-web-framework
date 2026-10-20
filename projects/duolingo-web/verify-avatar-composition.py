"""Check source-observed composition against actual saved bytes and runtime readback."""
import argparse
import json
from pathlib import Path
BASE = Path(__file__).resolve().parent
p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--native', required=True)
p.add_argument('--source', default=str(BASE/'evidence/english-avatar-composition-v1'))
p.add_argument('--out', required=True)
a = p.parse_args()
native, source = Path(a.native), Path(a.source)
config = json.loads((BASE/'evidence/english-avatar-categories-v1/renderer-config.json').read_text())['stateChooserTabs']
expected = {}
for i, tab in enumerate(config):
    groups = json.loads((source/f'restored-{i}.json').read_text())['radio_groups']
    assert len(groups) == len(tab['sections'])
    for section, group in zip(tab['sections'], groups):
        assert section['header'] == group['label']
        options = section['imageButtons'] if section['buttonType']=='IMAGE' else section['featureButtons']
        assert len(options) == len(group['options'])
        selected = [o for o, s in zip(options, group['options']) if s['checked']]
        assert len(selected) == 1
        expected[selected[0]['state']] = selected[0]['value']
observed = json.loads((native/'observed.json').read_text())
prefs = json.loads((native/'progress.json.preferences.json').read_text())
readbacks = [json.loads(line.split('avatar-runtime-inputs ',1)[1]) for line in (native/'child.log').read_text().splitlines() if line.startswith('avatar-runtime-inputs ')]
rows = []
def check(name, actual, expected):
    rows.append(dict(name=name, actual=actual, expected=expected, passed=actual==expected))
check('completed journey', observed.get('attempts'), [{'id':'avatar-composition','failure':None}])
check('captured state count', len(observed['states']), 15)
check('stored composition', prefs.get('avatarState'), expected)
check('legacy skin compatibility', prefs.get('avatarSkin'), 15-expected['SkinTone'])
for name,value in expected.items():
    check('final live Rive '+name, readbacks[-1].get(name) if readbacks else None, value)
check('preview zoom', readbacks[-1].get('ENG_ONLY_Zoom') if readbacks else None, 3)
scrolls = json.loads((native/'scroll.json').read_text())
check('two actual scrolls',len(scrolls),2)
for i,scroll in enumerate(scrolls):
    check(f'scroll {i} survived',scroll.get('child_running'),True)
    check(f'scroll {i} measured movement', bool(scroll.get('before') and scroll.get('after') and scroll['before']!=scroll['after']),True)
result = dict(rows=rows, passed=all(r['passed'] for r in rows), limits=['Readback and storage are not pixel/audio equivalence','Only this observed combination, not arbitrary combinations','Use verify-avatar-inventory.py separately for restored AX selection states'])
with Path(a.out).open('x') as f: json.dump(result,f,ensure_ascii=False,indent=2); f.write('\n')
print(json.dumps({'pass':sum(r['passed'] for r in rows),'fail':sum(not r['passed'] for r in rows)}))
raise SystemExit(0 if result['passed'] else 1)
