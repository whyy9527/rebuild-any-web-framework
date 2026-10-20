"""Keep actual new branches and unavailable actions in the exploration queue."""
import argparse,json
from pathlib import Path
from capabilities.rebuild.discovery import frontier
B=Path('projects/duolingo-web');E=B/'evidence/english-stage2-path-v1';S=E/'source'
p=argparse.ArgumentParser();p.add_argument('--out-dir',required=True);out=Path(p.parse_args().out_dir);out.mkdir(parents=True,exist_ok=False)
h=json.loads((B/'evidence/english-stage2-home-v1/history.json').read_text())
for path in sorted(S.glob('*.json')):
 d=json.loads(path.read_text())
 if 'actions' not in d:continue
 h['states'].append(dict(id='grocery-'+path.stem,evidence=str(path),actions=d['actions']))
states={s['id']:s for s in h['states']}
def edge(start,end,key,value,receipt,outcome='observed'):
 start='grocery-'+start;end='grocery-'+end
 a=[v for v in states[start]['actions'] if v.get(key)==value];assert len(a)==1,(start,key,value,len(a))
 h['transitions'].append(dict(**{'from':start},to=end,action=a[0]['id'],outcome=outcome,evidence=str(S/receipt)))
edge('persistent-grocery-speech-before','persistent-grocery-speech-closed','test','player-skip','persistent-grocery-speech-closed.json')
edge('persistent-grocery-result','persistent-grocery-review','name','回顾本单元','persistent-grocery-review.json')
edge('persistent-grocery-review','persistent-grocery-review-fill','name','填空\nThis store is very ___.','persistent-grocery-review-fill.raw.txt')
edge('grocery-return-profile','grocery-home-after','name','稍后再说','grocery-home-after.json')
edge('persistent-grocery-home-popup-after','persistent-grocery-guide-coach-open','name','打开这个部分的指南','persistent-grocery-guide-coach-open.raw.txt')
edge('grocery-home-after','persistent-grocery-home-popup-after','test','skill-path-level-0 skill-path-level-skill','persistent-grocery-home-popup-after.raw.txt',outcome='unavailable')
h['limitations'] += ['Fresh505gems/1streak preparation is separate from older530gems/2streak source state.','Delayed guide coach blocked an actual node click; unavailable stays pending.','Review fill answer expansion was executed; the other ten cards remain separate unknown branches.','Actual accepted grocery sequence is not an adaptive-selection algorithm or matched-budget RSI gain.']
for name,d in [('history.json',h),('frontier.json',frontier(Path.cwd(),h))]:(out/name).write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(dict(states=len(h['states']),executed_edges=len(h['transitions']),pending=len(frontier(Path.cwd(),h)['pending']))))
