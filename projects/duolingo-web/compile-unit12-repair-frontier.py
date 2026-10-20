"""Keep real third-lesson/skip discoveries separate from existing model gains."""
import argparse,json
from pathlib import Path
from capabilities.rebuild.discovery import frontier
B=Path('projects/duolingo-web');E=B/'evidence/english-unit12-frontend-repair-v1';S=E/'source'
p=argparse.ArgumentParser();p.add_argument('--out-dir',required=True);out=Path(p.parse_args().out_dir);out.mkdir(parents=True,exist_ok=False)
h=json.loads((B/'evidence/english-unit12-lesson2-v1/history.json').read_text())
for name in ['unit12-lesson3-first-question','unit12-lesson3-skip-feedback']:
 d=json.loads((S/(name+'.json')).read_text());h['states'].append(dict(id=name,evidence=str(S/(name+'.json')),actions=d['actions']))
states={s['id']:s for s in h['states']}
for fr,to,label,receipt in [('unit12-lesson3-popup','unit12-lesson3-first-question','开始 +10 经验','unit12-lesson3-start.raw.txt'),('unit12-lesson3-first-question','unit12-lesson3-skip-feedback','跳过','unit12-lesson3-skip.raw.txt')]:
 actions=[a for a in states[fr]['actions'] if a['name']==label];assert len(actions)==1
 h['transitions'].append(dict(**{'from':fr,'to':to},action=actions[0]['id'],outcome='observed',evidence=str(S/receipt)))
h['limitations']+=['Third-lesson first empty skip shows correct sentence and unchanged4hearts; no mid-streak or every-skip formula inferred.','Native geometry repair and owned output recordings verify implementation, not RSI causal effects.']
f=frontier(Path.cwd(),h)
feedback=dict(prior='english-unit12-lesson2-v1/exploration-feedback.json',discoveries=['Ordinary assist used old button layout instead of source radio layout','Observed source heart image32x32 identifies original public resource and header geometry','Skip action absent from compiled frontend although observed enabled','Third actual lesson starts Is the kitchen clean?; empty skip shows厨房干净吗？and4hearts'],next_exploration=['Continue third actual lesson after captured skip feedback, then its review/settlement','Implement and verify reminder; trigger scheduling remains unknown','Expand text/CSS fidelity and whole-image differences beyond repaired radio geometry','Original animation and source acoustic comparison','Preregister and execute matched-budget model04, preserving02/03 inconclusive'],causal_status='No new real model experiment and no RSI causal improvement claim')
for name,data in [('history.json',h),('frontier.json',f),('exploration-feedback.json',feedback)]:(out/name).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(dict(states=len(h['states']),edges=len(h['transitions']),pending=len(f['pending']))))
