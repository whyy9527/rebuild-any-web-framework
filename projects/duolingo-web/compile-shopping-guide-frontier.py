"""Append actual guide observations; retain no-popup hint attempts as unresolved."""
import argparse,json
from pathlib import Path
from capabilities.rebuild.discovery import frontier
B=Path('projects/duolingo-web');E=B/'evidence/english-shopping-guide-v1';S=E/'source'
p=argparse.ArgumentParser();p.add_argument('--out-dir',required=True);out=Path(p.parse_args().out_dir);out.mkdir(parents=True,exist_ok=False)
h=json.loads((B/'evidence/english-stage2-path-v1/history.json').read_text())
for path in sorted(S.glob('*.json')):
 d=json.loads(path.read_text())
 if 'actions' not in d:continue
 h['states'].append(dict(id='shopping-guide-'+path.stem,evidence=str(path),actions=d['actions']))
states={s['id']:s for s in h['states']}
def edge(start,end,action,receipt,outcome='observed'):
 start='shopping-guide-'+start;end='shopping-guide-'+end
 assert action in {a['id'] for a in states[start]['actions']}
 h['transitions'].append(dict(**{'from':start},to=end,action=action,outcome=outcome,evidence=str(S/receipt)))
edge('grocery-guide-v2-top','grocery-guide-v2-hat-hover','test:hint-token#6','grocery-guide-hat-hover.raw.txt','unavailable')
edge('grocery-guide-v2-hat-hover','grocery-guide-v2-hat-click','test:hint-token#6','grocery-guide-hat-click.raw.txt','unavailable')
edge('grocery-guide-v2-top','grocery-guide-v2-return','href:/learn#1','grocery-guide-return.raw.txt')
h['limitations']+=['Guide hint hover/click/Enter produced no visible popup; lexical meaning behavior remains unresolved.','Five actual speech triggers are in source/grocery-guide-all-five-audio.raw.txt; not five invented destination states.','Current grocery replay failed before scaffold identity, then was rejected by wrong gap driver; later actual orderTapComplete accepted after scoped bank/gap fix.','No matched-budget RSI effect demonstrated; current UI instances and history guide next exploration.']
f=frontier(Path.cwd(),h)
for name,data in [('history.json',h),('frontier.json',f)]: (out/name).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(dict(states=len(h['states']),edges=len(h['transitions']),pending=len(f['pending']))))
