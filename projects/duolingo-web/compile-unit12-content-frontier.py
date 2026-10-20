"""Carry forward actual source failures and discoveries; never invent RSI gains."""
import argparse,json
from pathlib import Path
from capabilities.rebuild.discovery import frontier
B=Path('projects/duolingo-web');E=B/'evidence/english-unit12-content-v1';S=E/'source'
p=argparse.ArgumentParser();p.add_argument('--out-dir',required=True);out=Path(p.parse_args().out_dir);out.mkdir(parents=True,exist_ok=False)
h=json.loads((B/'evidence/english-unit-placement-v1/history.json').read_text())
names=['unit12-guide-ready-top','unit12-guide-ready-bottom','unit12-current-lesson-popup','unit12-lesson-oral-before','unit12-lesson-oral-closed','unit12-lesson-result-stable','unit12-lesson-review','unit12-lesson-after-result','unit12-home-after-lesson','unit12-radio-intercepted','unit12-coach-pronunciation','unit12-radio-popover','unit12-lesson2-popup']
for name in names:
 path=S/(name+'.json');d=json.loads(path.read_text());h['states'].append(dict(id=name,evidence=str(path),actions=d['actions']))
batch=json.loads((S/'unit12-lesson2-surface-probe.json').read_text());row=batch['observed'][0]
for suffix,key in [('before','frontend_before'),('feedback','frontend_feedback')]:
 h['states'].append(dict(id='unit12-next-q0-'+suffix,evidence=str(S/'unit12-lesson2-surface-probe.json'),actions=row[key]['actions']))
states={s['id']:s for s in h['states']}
def link(fr,to,label,receipt,outcome='observed',test=None):
 actions=[a for a in states[fr]['actions'] if a.get('test')==test] if test else [a for a in states[fr]['actions'] if a['name']==label]
 assert len(actions)==1,(fr,label,test,len(actions))
 h['transitions'].append({'from':fr,'to':to,'action':actions[0]['id'],'outcome':outcome,'evidence':str(S/receipt)})
link('unit12-lesson-oral-before','unit12-lesson-oral-closed','现在不做口语题','unit12-lesson-oral-declined.raw.txt')
link('unit12-lesson-result-stable','unit12-lesson-review','回顾本单元','unit12-lesson-review-open.raw.txt')
link('unit12-lesson-result-stable','unit12-lesson-after-result','继续','unit12-lesson-result-continued.raw.txt')
link('unit12-lesson-after-result','unit12-home-after-lesson','稍后再说','unit12-profile-declined.raw.txt')
link('unit12-home-after-lesson','unit12-radio-intercepted','电台','unit12-radio-open.raw.txt',outcome='unavailable',test='skill-path-level-2 skill-path-level-duo_radio')
link('unit12-radio-intercepted','unit12-coach-pronunciation','发音','unit12-coach-pronunciation-open.raw.txt')
link('unit12-coach-pronunciation','unit12-coach-pronunciation','学习','unit12-coach-home-return.raw.txt',outcome='unavailable')
link('unit12-radio-popover','unit12-lesson2-popup',None,'unit12-lesson2-popup-open.raw.txt',test='skill-path-level-0 skill-path-level-skill')
link('unit12-lesson2-popup','unit12-next-q0-before','开始 +10 经验','unit12-lesson2-start.raw.txt')
chosen=row['actions'][0]['select'];actions=[a for a in states['unit12-next-q0-before']['actions'] if a['name'].split('\n')[0]==chosen];assert len(actions)==1
h['transitions'].append({'from':'unit12-next-q0-before','to':'unit12-next-q0-feedback','action':actions[0]['id'],'outcome':'observed','evidence':str(S/'unit12-lesson2-surface-probe.json'),'observed_steps':[{'select':chosen},{'click':'检查'}],'limits':'Composite actual selection and grading; not a claim that selecting alone shows feedback'})
h['limitations'] += ['17 accepted questions, deferred oral and two interludes are batch receipts; no fictitious navigation edges.','Coach overlay intercepts actual radio/home/tooltip actions; inaccessible actions stay pending.','History-directed discoveries are real, but no new matched-budget model selection benefit has been measured.']
f=frontier(Path.cwd(),h)
feedback=dict(prior='english-unit-placement-v1/exploration-feedback.json',resolved_discoveries=['Independent guide12 with five phrases/audio and25token targets','Current unit12 home lesson17accepted+oraldecline+18cards','Correct feedback gain0.35 and completion0.5 actual source invocations','Post-lesson Lesson2of6 persists in source home'],next_exploration=['Implement actual delayed pronunciation coach; outside click dismisses, Escape and tooltip click did not','Implement observed locked apartment-tour radio; explore lower units and unit13 independent jump','Current lesson2 starts with select living-room; do not repeat lesson1. Continue full trajectory with new frontend surface capture','Unit12 guide token click/Enter and delayed hover outcomes','Normal oral grading, wrong answers, dialogue speech with missed event window','Original result/interlude animation and original source acoustic alignment','Real matched-budget model ablation with current source readiness, distinct from existing03 repeat measurement'],causal_status='No RSI gain claim; discovery history is used to choose omissions, not to prove self-improvement')
for name,data in [('history.json',h),('frontier.json',f),('exploration-feedback.json',feedback)]:(out/name).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(dict(states=len(h['states']),edges=len(h['transitions']),pending=len(f['pending']))))
