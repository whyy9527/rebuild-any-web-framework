"""Extend real exploration history; no simulated model improvement claim."""
import argparse,json
from pathlib import Path
from capabilities.rebuild.discovery import frontier
B=Path('projects/duolingo-web');E=B/'evidence/english-unit-placement-v1';S=E/'source'
p=argparse.ArgumentParser();p.add_argument('--out-dir',required=True);out=Path(p.parse_args().out_dir);out.mkdir(parents=True,exist_ok=False)
h=json.loads((B/'evidence/english-home-scroll-v1/history.json').read_text())
names=['unit12-first-question','unit12-before-exit','unit12-exit-confirm','unit12-gap-first','unit12-result-stable','unit12-review','unit12-after-result','unit12-after-score','unit12-after-unlock','unit12-home-after','unit12-home-uncovered']
for name in names:
 path=S/(name+'.json');d=json.loads(path.read_text());h['states'].append({'id':name,'evidence':str(path),'actions':d['actions']})
states={s['id']:s for s in h['states']}
def link(fr,to,label,record,test=None):
 candidates=[a for a in states[fr]['actions'] if (a.get('test')==test if test else a.get('name')==label)]
 assert len(candidates)==1,(fr,label,test,len(candidates))
 h['transitions'].append(dict(from_=fr,to=to,action=candidates[0]['id'],outcome='observed',evidence=str(S/record)))
 h['transitions'][-1]['from']=h['transitions'][-1].pop('from_')
link('home-scroll-unit-jump','unit12-first-question',None,'unit12-start.raw.txt','player-next')
link('unit12-before-exit','unit12-exit-confirm',None,'unit12-exit-confirm.raw.txt','quit-button')
link('unit12-exit-confirm','unit12-gap-first','继续努力','unit12-exit-cancel-recovered.raw.txt')
link('unit12-result-stable','unit12-review','回顾本单元','unit12-review-open.raw.txt')
link('unit12-result-stable','unit12-after-result','继续','unit12-result-continued.raw.txt')
link('unit12-after-result','unit12-after-score','继续','unit12-score-continued.raw.txt')
link('unit12-after-score','unit12-after-unlock','继续','unit12-unlock-continued.raw.txt')
link('unit12-after-unlock','unit12-home-after','稍后再说','unit12-profile-later.raw.txt')
link('unit12-home-after','unit12-home-uncovered','下次再说','unit12-notification-later.raw.txt')
h['limitations'] += ['18 accepted questions/four interludes are in current-question batch receipts, not invented state-action edges.','Unit12 global4 hearts and independent5 hearts are different observed state; source state not reset.','New discovery follows prior feedback, but no matched-budget RSI causal benefit is established.']
f=frontier(Path.cwd(),h)
feedback=dict(source='english-home-scroll-v1/exploration-feedback.json',actual_discoveries=[dict(id=k,evidence=str(S/v)) for k,v in [('independent-unit-route','unit12-batch01.json'),('gapFill','unit12-batch03.json'),('roleless-quit','unit12-exit-confirm.json'),('unpromoted-score','unit12-after-result.json'),('unlocked-home','unit12-home-uncovered.json'),('notification-after-unlock','unit12-home-after.json')]],mechanism_changes=['Structural exercised route guard','Explicit quit-confirmation observation before answering','GapFill current-context and complete-choice identity checks','Full49-state frontend freeze instead of representative question'],next_exploration=['Unit12 active lesson and guidebook/en/12; do not reuse grocery lesson/guide','Unit13 jump, unit2 radio and lower-unit branch outcomes','Original score/interlude/Oscar animation resources and actual sound triggers','Roleless overlay/hidden animated text regression observations'],experiment='Matched-budget real-model history replay and live held-out rollout remains unexecuted; no RSI gain claim')
for name,data in [('history.json',h),('frontier.json',f),('exploration-feedback.json',feedback)]:(out/name).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(dict(states=len(h['states']),edges=len(h['transitions']),pending=len(f['pending']))))
