"""Compare actual AX inventories and selections to source UI groups (not interactions)."""
import argparse
import json
from pathlib import Path
BASE=Path(__file__).resolve().parent
p=argparse.ArgumentParser(description=__doc__)
for n in ['observed','source-pattern','state-prefix','out']:p.add_argument('--'+n,required=True)
a=p.parse_args();native=json.loads(Path(a.observed).read_text())['states']
config=json.loads((BASE/'evidence/english-avatar-categories-v1/renderer-config.json').read_text())['stateChooserTabs'];rows=[]
for i,tab in enumerate(config):
    source=json.loads(Path(a.source_pattern.format(i=i)).read_text());assert len(source['radio_groups'])==len(tab['sections'])
    state=native.get(a.state_prefix+str(i),{});elements=state.get('elements',{})
    for section,group in zip(tab['sections'],source['radio_groups']):
        options=section['imageButtons'] if section['buttonType']=='IMAGE' else section['featureButtons'];assert section['header']==group['label'] and len(options)==len(group['options'])
        ids=['avatar-skin-'+str(15-o['value']) if o['state']=='SkinTone' else 'avatar-choice-'+o['state']+'-'+str(o['value']) for o in options]
        expected=[o['value'] for o,s in zip(options,group['options']) if s['checked']]
        actual=[o['value'] for o,k in zip(options,ids) if elements.get(k,{}).get('checked') is True]
        missing=[k for k in ids if k not in elements]
        checked_match=all(type(elements.get(k,{}).get('checked')) is bool and elements[k]['checked']==s['checked'] for k,s in zip(ids,group['options']))
        roles=all(elements.get(k,{}).get('role')=='AXRadioButton' for k in ids)
        rows.append({'category':i,'group':group['label'],'source_options':len(options),'actual_present':sum(k in elements for k in ids),'expected_selected_values':expected,'actual_selected_values':actual,'missing':missing,'pass':not missing and checked_match and roles})
result={'kind':'source grouped inventory versus actual AX','rows':rows,'options':sum(r['source_options'] for r in rows),'pass':all(r['pass'] for r in rows),'limits':['Inventories/selected states do not prove every option was clicked','Not a screenshot, sound, SMButtons rendering or arbitrary-combination equivalence check']}
with Path(a.out).open('x') as f:json.dump(result,f,ensure_ascii=False,indent=2);f.write('\n')
print(json.dumps({'groups_pass':sum(r['pass'] for r in rows),'groups_fail':sum(not r['pass'] for r in rows),'options':result['options']}))
raise SystemExit(0 if result['pass'] else 1)
