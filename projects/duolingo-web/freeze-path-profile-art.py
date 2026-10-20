"""Append an actual CSS background geometry omitted by the earlier media mold."""
import argparse,json
from pathlib import Path
BASE=Path(__file__).resolve().parent
ROOT=BASE.parents[1]
EV=BASE/'evidence/english-path-profile-v1'
def build():
    contract=json.loads((BASE/'frontend-english-v41.json').read_text());old=contract['requirements'][:]
    contract.update(revision='english-v42',parent_revision='english-v41',changes=['Actual CSS background Duo missing from old media mold; freeze its geometry before implementing path profile.'])
    source=json.loads((EV/'source/profile.json').read_text());art=next(r for r in source['background_media'] if 'efff73c7255e0a6eff22f1ddc22b087b.svg' in r['backgroundImage']);assert art['backgroundSize']=='auto 250px'
    evidence=[str((EV/'source/profile.json').relative_to(ROOT))]
    contract['requirements'].append(dict(id='path-profile-background-geometry',state='chest-practice-start-profile',kind='element_geometry',element='path-profile-art',rect=art['rect'],tolerance_points=0,evidence=evidence))
    reference=json.loads((BASE/'evidence/english-chest-v1/reference-v41.json').read_text());reference['states']['chest-practice-start-profile']['elements']['path-profile-art']=dict(rect=art['rect'])
    assert contract['requirements'][:-1]==old
    return contract,reference
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out-dir',required=True);a=p.parse_args();out=Path(a.out_dir);out.mkdir(parents=True,exist_ok=False)
    for name,value in zip(['contract.json','reference.json'],build()):(out/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
