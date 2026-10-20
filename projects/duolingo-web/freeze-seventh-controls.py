"""Preserve v13, adding actual radio semantics/disabled facts and skip geometry.

Source snapshot [disabled] wins over the old serializer's !n.disabled for
ARIA-disabled controls. Both original contradictory receipts remain untouched.
"""
import json
from pathlib import Path
BASE=Path(__file__).resolve().parent
OLD=BASE/'evidence/english-secondary-actions-v1'
EV=BASE/'evidence/english-eighth-v1'
def read(p):return json.loads(p.read_text())
def write(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
c=read(BASE/'frontend-english-v13.json');c['revision']='english-v14-actual-seventh-controls';c['scope']='Preserves all v13 assertions, adds observed skip geometry and radio role/disabled state; no pixel or acoustic assertion promoted.'
s=read(BASE/'evidence/english-seventh-v1/source-full-observed.json')
for phase,name in [('', 'secondary-listen-isolation-before.json'),('-feedback','secondary-listen-isolation-feedback.json')]:
    path=OLD/name;d=read(path);state='en-zh-l7-q3'+phase;s['states'][state]['elements']={}
    for i,control in enumerate(x for x in d['visible'] if x.get('role')=='radio'):
        element='option-'+str(i);label=str(i+1);line=next(x for x in d['snapshot'].splitlines() if f'radio "{label}"' in x)
        enabled='[disabled]' not in line
        assert control['role']=='radio'
        evidence=['projects/duolingo-web/evidence/english-secondary-actions-v1/'+name]
        s['states'][state]['elements'][element]=dict(role='radio',enabled=enabled,rect=control['rect'])
        c['requirements'] += [dict(id=state+'-'+element+'-role',state=state,kind='element_role',element=element,role='radio',evidence=evidence),dict(id=state+'-'+element+'-enabled',state=state,kind='element_boolean',element=element,field='enabled',expected=enabled,evidence=evidence)]
p=OLD/'secondary-reset-q0.json';control=next(x for x in read(p)['visible'] if x.get('test')=='player-skip');state='en-zh-l7-q0'
s['states'][state]['elements']={'skip':dict(rect=control['rect'])}
c['requirements'].append(dict(id=state+'-skip-geometry',state=state,kind='element_geometry',element='skip',rect=control['rect'],tolerance_points=0,evidence=['projects/duolingo-web/evidence/english-secondary-actions-v1/secondary-reset-q0.json']))
write(BASE/'frontend-english-v14.json',c)
write(EV/'source-seventh-controls-observed.json',s)
