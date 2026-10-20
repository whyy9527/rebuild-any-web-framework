"""Append the actual Escape dismissal to the source frontend contract."""
import argparse
import json
from pathlib import Path

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[1]
EV = BASE/'evidence/english-home-frontier-v1'

def build():
    parent = json.loads((BASE/'frontend-english-v35.json').read_text())
    contract = json.loads(json.dumps(parent))
    contract.update(revision='english-v36',parent_revision='english-v35',changes=['Actual Escape dismisses the result-review modal without leaving settlement.'])
    reference = json.loads((BASE/'evidence/english-error-review-v1/reference.json').read_text())
    source = json.loads((EV/'source/review-escape.json').read_text())
    assert source['path']=='/practice'
    assert '查看你的成绩单！' not in source['snapshot']
    assert '你莫不是特工？' in source['snapshot'] and 'button "回顾本单元"' in source['snapshot']
    key='error-practice-review-escape'
    reference['states'][key]=dict(snapshot=source['snapshot'],accessible_text=['你莫不是特工？'],interactions=dict(review_closed='查看你的成绩单！' not in source['snapshot']))
    evidence=[str((EV/'source/review-escape.json').relative_to(ROOT))]
    contract['requirements'] += [
        dict(id=key+'-closed',state=key,kind='interaction_boolean',field='review_closed',expected=True,evidence=evidence),
        dict(id=key+'-settlement-title',state=key,kind='accessible_text',text='你莫不是特工？',evidence=evidence)]
    assert contract['requirements'][:2208]==parent['requirements']
    return contract,reference

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out-dir',required=True);a=p.parse_args()
    output=Path(a.out_dir);output.mkdir(parents=True,exist_ok=False)
    for name,value in zip(['contract.json','reference.json'],build()):
        (output/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
