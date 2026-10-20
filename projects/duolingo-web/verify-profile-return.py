"""Check source-derived profile state, saved composition consumption and route outcomes."""
import argparse
import json
from pathlib import Path
BASE=Path(__file__).resolve().parent
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--native',required=True);p.add_argument('--out',required=True);a=p.parse_args()
native=Path(a.native);observed=json.loads((native/'observed.json').read_text());reference=json.loads((BASE/'evidence/english-profile-return-v1/reference-with-closure.json').read_text());rows=[]
def check(name,actual,expected):rows.append(dict(name=name,actual=actual,expected=expected,passed=actual==expected))
check('actual saved-profile journey',next((r['failure'] for r in observed['attempts'] if r['id']=='saved-profile-return'),'missing'),None)
for key,state in observed['states'].items():
    for field,expected in reference['states'][key]['interactions'].items():check(key+' '+field,state.get('interactions',{}).get(field),expected)
source=BASE/'evidence/english-avatar-composition-v1';tabs=json.loads((BASE/'evidence/english-avatar-categories-v1/renderer-config.json').read_text())['stateChooserTabs'];expected={}
for i,tab in enumerate(tabs):
    groups=json.loads((source/f'restored-{i}.json').read_text())['radio_groups']
    for section,group in zip(tab['sections'],groups):
        options=section['imageButtons'] if section['buttonType']=='IMAGE' else section['featureButtons']
        selected=[o for o,s in zip(options,group['options']) if s['checked']];assert len(selected)==1
        expected[selected[0]['state']]=selected[0]['value']
readbacks=[json.loads(line.split('avatar-runtime-inputs ',1)[1]) for line in (native/'child.log').read_text().splitlines() if line.startswith('avatar-runtime-inputs ')]
# The scenario first opens the profile, then later opens the editor. Check both actual consumers.
for name,value in expected.items():check('profile actual Rive '+name,readbacks[0].get(name) if readbacks else None,value)
check('profile asset default zoom',readbacks[0].get('ENG_ONLY_Zoom') if readbacks else None,1)
check('later editor zoom',readbacks[-1].get('ENG_ONLY_Zoom') if readbacks else None,3)
key='profile-return-profile';check('profile Canvas source bounds',observed['states'][key]['elements'].get('profile-avatar-canvas',{}).get('rect'),reference['states'][key]['elements']['profile-avatar-canvas']['rect'])
log=(native/'child.log').read_text()
for font in ['DINNextRoundedLTPro-Regular','DINNextRoundedLTPro-Bold']:check('actual 404 font '+font,'error-runtime-font '+font in log,True)
result=dict(kind='source-derived partial profile/return checks',rows=rows,passed=all(r['passed'] for r in rows),open_journeys=[r for r in observed['attempts'] if r['failure'] is not None],limits=['Only actually captured profile/return states checked','Missing home-section entry remains a failed journey, not cleared by these checks','No image, sound or arbitrary-avatar equivalence claim'])
with Path(a.out).open('x') as f:json.dump(result,f,ensure_ascii=False,indent=2);f.write('\n')
print(json.dumps({'pass':sum(r['passed'] for r in rows),'fail':sum(not r['passed'] for r in rows),'open_journeys':len(result['open_journeys'])}));raise SystemExit(0 if result['passed'] else 1)
