"""Expose actual home/profile controls and executed edges, including offscreen inventory."""
import argparse
import json
from pathlib import Path
from capabilities.rebuild.discovery import frontier
ROOT=Path.cwd(); E=Path('projects/duolingo-web/evidence/english-profile-return-v1')
parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--out-dir',required=True);args=parser.parse_args();out=Path(args.out_dir);out.mkdir(parents=True,exist_ok=False)
files=sorted((E/'source').glob('*.json'));states=[]
for f in files:
    source=json.loads(f.read_text()); actions=source['actions'][:]
    # Preserve pointer candidates; add rendered canonical controls omitted by viewport clipping.
    for c in source.get('control_inventory',[]):
        if any(a['rect']==c['rect'] and a.get('href')==c.get('href') and a.get('tag')==c.get('tag') for a in actions):continue
        actions.append(dict(c,id='inventory-'+str(c['index']),kind='rendered_inventory_only',limitations='Not executed; viewport and center-hit facts are separate'))
    states.append(dict(id=f.stem,evidence=str(f),actions=actions))
by={s['id']:s for s in states}; transitions=[]
def edge(start,end,**match):
    candidates=[a for a in by[start]['actions'] if all(a.get(k)==v for k,v in match.items())]
    assert len(candidates)==1,(start,match,candidates)
    transitions.append(dict(**{'from':start},action=candidates[0]['id'],to=end,outcome='observed',evidence=str(E/'transitions.json')))
edge('home','sections',href='/sections')
edge('profile','languages',rect=[721,276,39,43.9140625])
edge('profile','edit-from-pencil',rect=[696,40,48,48])
edge('languages-after-escape-visible','languages-close-button',rect=[380,280,32,32])
edge('languages','enrollment-return',href='/enroll/en/zh/%E5%AD%A6%E4%B9%A0-%E8%8B%B1%E8%AF%AD')
edge('clean-back','home-return',name='duolingo.com')
edge('sections','section-test-intro',name='跳至第 2 阶段')
edge('section-test-intro','section-test-first',name='继续')
edge('section-test-first','sections-return',rect=[100,52,18,18])
edge('sections-return','home-return',name='继续')
history=dict(kind='actual source controls and executed grouped edges',states=states,transitions=transitions,limitations=['Not every recorded duplicate state/action was re-executed','Escape negative outcome is separately recorded; no fabricated DOM control','No inferred destination for offscreen stage3..8 or daily review'])
for name,data in [('history.json',history),('frontier.json',frontier(ROOT,history))]:
    with (out/name).open('x') as f:json.dump(data,f,ensure_ascii=False,indent=2);f.write('\n')
print(json.dumps({'states':len(states),'executed_edges':len(transitions),'pending':len(frontier(ROOT,history)['pending'])}))
