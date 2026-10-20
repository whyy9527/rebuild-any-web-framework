"""Advance discovery from actual lesson receipts, retaining unknown successors."""
import argparse,json
from pathlib import Path
from capabilities.rebuild.discovery import frontier
B=Path('projects/duolingo-web');E=B/'evidence/english-unit12-lesson2-v1';S=E/'source'
p=argparse.ArgumentParser();p.add_argument('--out-dir',required=True);out=Path(p.parse_args().out_dir);out.mkdir(parents=True,exist_ok=False)
h=json.loads((B/'evidence/english-unit12-content-v1/history.json').read_text());index=0
for name in ['unit12-lesson2-surface-probe','unit12-lesson2-batch01','unit12-lesson2-batch02']:
 d=json.loads((S/(name+'.json')).read_text());raws={r['index']:r['content'] for r in d['session']['challenges']}
 for row in d['observed']:
  if raws[row['index']]['type']=='speak':index+=1;continue
  if not row.get('feedback'):continue
  if index>0:
   fr=f'unit12-lesson2-q{index}-before';to=f'unit12-lesson2-q{index}-feedback'
   for state,key in [(fr,'frontend_before'),(to,'frontend_feedback')]:h['states'].append(dict(id=state,evidence=str(S/(name+'.json')),actions=row[key]['actions']))
   checks=[a for a in row['frontend_before']['actions'] if a['name']=='检查'];assert len(checks)==1
   h['transitions'].append(dict(**{'from':fr,'to':to},action=checks[0]['id'],outcome='observed',evidence=str(S/(name+'.json')),observed_steps=row['actions'],limits='Actual answer entry plus grading; not an empty check action'))
  index+=1
assert index==13
for name in ['unit12-lesson2-oral-before','unit12-lesson2-oral-closed','unit12-lesson2-result','unit12-lesson2-review','unit12-lesson2-after-result','unit12-lesson2-home-after','unit12-lesson2-home-reloaded','unit12-lesson3-notification','unit12-lesson3-popup']:
 d=json.loads((S/(name+'.json')).read_text());h['states'].append(dict(id=name,evidence=str(S/(name+'.json')),actions=d['actions']))
states={s['id']:s for s in h['states']}
for fr,to,label,receipt,outcome in [('unit12-lesson2-home-reloaded','unit12-lesson3-notification','Lesson 3 of 6','unit12-lesson3-popup-scoped.raw.txt','unavailable'),('unit12-lesson3-notification','unit12-lesson3-popup','下次再说','unit12-lesson3-notification-declined-popup.raw.txt','observed')]:
 actions=[a for a in states[fr]['actions'] if a['name']==label];assert len(actions)==1,(fr,label)
 h['transitions'].append(dict(**{'from':fr,'to':to},action=actions[0]['id'],outcome=outcome,evidence=str(S/receipt),limits='Notification dismissal then active-node click is composite; blocked click did not open lesson'))
h['limitations']+=['Lesson2 actual full trajectory discovered orderTapComplete and independently changing lesson content.','Reload and active-node popup receipts preserve real home3of6; no unexecuted lesson3 questions or transitions are inferred.','Native coach prepared pending state differs from source archived background scroll by493.5points; not a matching visual prestate.','No new matched-budget RSI causal experiment in this batch.']
f=frontier(Path.cwd(),h)
feedback=dict(prior='english-unit12-content-v1/exploration-feedback.json',resolved_discoveries=['Completed distinct ordinary Lesson2:12accepted,1oraldeclined,2interludes,13reviewcards','Captured every graded frontend before/feedback including control CSS/text geometry/hit/clipping','Source reload persists home3of6 without coach reappearance'],next_exploration=['Explore actual Lesson3 content and progression rather than repeat known lesson2','Guide12 token hover/click/Enter outcomes','Normal oral grading, wrong answer repair and unobserved audio invocation windows','Source-matched coach background scroll and original result/interlude animation','New preregistered04 matched-budget real-model experiment;02 and03 remain inconclusive'],causal_status='History selects observed omissions; this is not evidence of RSI causal improvement')
for name,data in [('history.json',h),('frontier.json',f),('exploration-feedback.json',feedback)]:(out/name).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(dict(states=len(h['states']),edges=len(h['transitions']),pending=len(f['pending']))))
