"""Append the source reward graphics/footer, preserving all v28 requirements."""
import copy
import json
from pathlib import Path
BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[1]
EV = BASE/'evidence/english-general-practice-v1'
OUT = BASE/'evidence/english-general-practice-presentation-v1'
OUT.mkdir(exist_ok=True)
contract = copy.deepcopy(json.loads((BASE/'frontend-english-v28.json').read_text()))
parent = copy.deepcopy(contract['requirements'])
source = copy.deepcopy(json.loads((EV/'reference.json').read_text()))
state = source['states']['general-practice-heart-reward']
row = json.loads((EV/'after-settlement.json').read_text())
refs = [str((EV/'after-settlement.json').relative_to(ROOT)), str((EV/'heart-reward-continue.json').relative_to(ROOT))]
for i, media in enumerate(row['media']):
    assert media['tag']=='IMG' and '/images/hearts/' in media['src']
    element=f'settlement-heart-{i}'
    state['elements'][element]={'rect':media['rect']}
    contract['requirements'].append(dict(id='general-practice-reward-'+element, state='general-practice-heart-reward',kind='element_geometry',element=element,rect=media['rect'],tolerance_points=0,evidence=refs))
for label, element in [('回顾本单元','settlement-secondary'),('重新练习','settlement-retry'),('继续','settlement-continue')]:
    button=next(v for v in row['visible'] if v['tag']=='BUTTON' and v['text']==label)
    state['elements'][element]={'rect':button['rect'],'role':'button','enabled':button['enabled']}
    prefix='general-practice-reward-'+element
    for kind, extra in [('element_geometry',dict(rect=button['rect'],tolerance_points=0)),('element_role',dict(role='button')),('element_boolean',dict(field='enabled',expected=button['enabled']))]:
        contract['requirements'].append(dict(id=prefix+'-'+kind,state='general-practice-heart-reward',kind=kind,element=element,evidence=refs,**extra))
    if label!='继续':contract['requirements'].append(dict(id=prefix+'-copy',state='general-practice-heart-reward',kind='accessible_text',text=label,evidence=refs))
assert contract['requirements'][:len(parent)]==parent
contract.update(revision='english-v29',parent_revision='english-v28',scope='Actual general practice reward hearts and retained result footer; all v28 requirements unchanged.',changes={'added':len(contract['requirements'])-len(parent),'source':'Existing actual fixed reference, including footer confirmed in a second source snapshot'})
(BASE/'frontend-english-v29.json').write_text(json.dumps(contract,ensure_ascii=False,indent=2)+'\n')
(OUT/'reference.json').write_text(json.dumps(source,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'requirements':len(contract['requirements']),'added':len(contract['requirements'])-len(parent)}))
