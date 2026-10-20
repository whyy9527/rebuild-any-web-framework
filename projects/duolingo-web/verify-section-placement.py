"""Check actual native accepted-question replay separately from visual acceptance."""
import argparse
import json
from pathlib import Path

BASE=Path(__file__).resolve().parent
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--native',required=True);p.add_argument('--out',required=True);p.add_argument('--with-outcome',action='store_true')
a=p.parse_args();native=Path(a.native);observed=json.loads((native/'observed.json').read_text())
fixture=json.loads((BASE/('fixture-reference-en-zh-section-placement-v2.json' if a.with_outcome else 'fixture-reference-en-zh-section-placement-v1.json')).read_text())
lesson=fixture['data']['candidate_course']['lessons'][0];rows=[]
def check(name,actual,expected):
    rows.append(dict(name=name,actual=actual,expected=expected,passed=actual==expected))
check('actual full native journey',observed['attempts'],[dict(id='observed-stage2-accepted-instance',failure=None)])
for q in lesson['questions']:
    state=observed['states'].get(q['id']+'-feedback',{})
    check(q['id']+' accepted',state.get('elements',{}).get('feedback',{}).get('value'),'correct')
    if q['kind']=='text_entry':
        check(q['id']+' actual text',state.get('elements',{}).get('answer-input',{}).get('value'),q['answer'])
for intro in lesson['interludes']:
    state=observed['states'].get(intro['id'],{})
    check(intro['id']+' actual message',intro['text'] in state.get('accessible_text',[]),True)
    check(intro['id']+' continue present','interlude-continue' in state.get('elements',{}),True)
for name in ['placement-result','placement-score','placement-quests','placement-gems','placement-profile','placement-return']:
    check(name+' actually captured',name in observed['states'],True)
if a.with_outcome:
    progress=json.loads((native/'progress.json').read_text())
    course=json.loads((BASE/'fixture-reference-en-zh-v14.json').read_text())['data']['candidate_course']['id']
    actual=progress.get('placementOutcomes',{}).get(course,{})
    for field in ['activeStage','completedStages','englishScore','sourceEvidence']:
        check('stored placement '+field,actual.get(field),lesson['placementOutcome'][field])
    check('stored source gems',actual.get('homeSnapshot',{}).get('gems'),530)
    check('independent global hearts',progress['hearts'],5)
    for name in ['sections-stage2-home','stage2-home-after-restart']:
        text=observed['states'].get(name,{}).get('accessible_text',[])
        for value in ['10','530','第 2 阶段，第 1 部分','购买食品杂货']:
            check(name+' actual '+value,value in text,True)
    check('restored active section continue','sections-continue-2' in observed['states'].get('stage2-sections-after-restart',{}).get('elements',{}),True)
result=dict(kind='partial actual accepted-placement replay',rows=rows,passed=all(r['passed'] for r in rows),
    limits=['These checks do not prove original adaptive question selection, exact visuals, general stage unlock/scoring rules or acoustic output. Daily quest refresh disagreement remains a frontend failure.',
            'Source-derived frontend contract independently retains those failures and uncovered states.'])
with Path(a.out).open('x') as f:json.dump(result,f,ensure_ascii=False,indent=2);f.write('\n')
print(json.dumps(dict(passed=sum(r['passed'] for r in rows),failed=sum(not r['passed'] for r in rows))))
raise SystemExit(0 if result['passed'] else 1)
