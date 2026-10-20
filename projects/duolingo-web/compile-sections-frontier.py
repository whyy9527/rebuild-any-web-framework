"""Carry real exploration history forward and expose newly uncovered home paths."""
import argparse
import json
from pathlib import Path
from capabilities.rebuild.discovery import frontier

BASE=Path('projects/duolingo-web');E=BASE/'evidence/english-sections-v1'
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out-dir',required=True)
out=Path(p.parse_args().out_dir);out.mkdir(parents=True,exist_ok=False)
history=json.loads((BASE/'evidence/english-profile-return-v1/history.json').read_text())
for f in sorted((E/'source').glob('*.json')):
    source=json.loads(f.read_text());actions=source['actions'][:]
    for c in source.get('control_inventory',[]):
        if any(a['rect']==c['rect'] and a.get('href')==c.get('href') and a.get('tag')==c.get('tag') for a in actions):
            continue
        actions.append(dict(c,id='inventory-'+str(c['index']),kind='rendered_inventory_only',
            limitations='Not executed; viewport, center-hit and actual outcomes remain separate'))
    history['states'].append(dict(id=f.stem,evidence=str(f),actions=actions))
by={s['id']:s for s in history['states']}
def edge(start,end,label,evidence):
    actions=[a for a in by[start]['actions'] if a.get('name')==label]
    assert len(actions)==1,(start,label)
    history['transitions'].append(dict(**{'from':start},action=actions[0]['id'],to=end,
        outcome='observed',evidence=str(E/evidence)))
edge('sections-placement-result','sections-placement-score','继续','sections-placement-after-result.raw.txt')
edge('sections-placement-score','sections-placement-quests','继续','sections-after-score.raw.txt')
edge('sections-placement-quests','sections-placement-gems','继续','sections-after-quests.raw.txt')
edge('sections-placement-gems','sections-placement-profile','继续','sections-after-gems.raw.txt')
edge('sections-placement-profile','sections-after-unlock','稍后再说','sections-placement-return.raw.txt')
edge('sections-lower-end','sections-stage2-home','继续','sections-stage2-home-snapshot.raw.txt')
history['limitations'] += [
    'Current 15 accepted challenge steps are separately recorded in placement-batch01..08; not promoted to blind RSI score',
    'Lower-section scrolling proves viewport reachability, not execution of every card',
    'Failed button-role wait after stage2 Continue is retained; independent next snapshot proves /learn navigation',
    'Source progressed to stage2; old prepared-state fixtures remain distinct and server reset is unverified']
for name,data in [('history.json',history),('frontier.json',frontier(Path.cwd(),history))]:
    (out/name).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(dict(states=len(history['states']),executed_edges=len(history['transitions']),
    pending=len(frontier(Path.cwd(),history)['pending']))))
