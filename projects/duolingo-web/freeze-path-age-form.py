"""Freeze the actual empty age step reached through profile Create; do not infer signup."""
import argparse,json
from pathlib import Path
BASE=Path(__file__).resolve().parent
ROOT=BASE.parents[1]
EV=BASE/'evidence/english-path-profile-v1'
def build():
    contract=json.loads((BASE/'frontend-english-v42.json').read_text());old=contract['requirements'][:]
    contract.update(revision='english-v43',parent_revision='english-v42',changes=['Actual Create reaches empty age step; Next disabled. Candidate has not implemented this step.'])
    reference=json.loads((EV/'reference.json').read_text());source=json.loads((EV/'source/age-form.json').read_text());key='path-age-form'
    assert 'textbox "年龄"' in source['snapshot'] and 'button "下一步" [disabled]' in source['snapshot']
    path=str((EV/'source/age-form.json').relative_to(ROOT));png=str((EV/'source/age-form.png').relative_to(ROOT))
    state=dict(snapshot=source['snapshot'],accessible_text=['你的年龄是……'],elements={},capture=dict(path=png,content_rect_points=[0,0,1200,732],backing_scale=1,window_points=[1200,732]));reference['states'][key]=state
    def add(label,kind,**fields):contract['requirements'].append(dict(id=key+'-'+label+'-'+kind,state=key,kind=kind,evidence=[path],**fields))
    add('title','accessible_text',text='你的年龄是……')
    for test,identifier,role in [('age-input','path-age-input','textbox'),('continue-button','path-age-next','button')]:
        node=next(r for r in source['visible'] if r.get('test')==test);state['elements'][identifier]=dict(rect=node['rect'],role=role,enabled=node['enabled'])
        add(identifier,'element_geometry',element=identifier,rect=node['rect'],tolerance_points=0);add(identifier,'element_role',element=identifier,role=role);add(identifier,'element_boolean',element=identifier,field='enabled',expected=node['enabled'])
    add('whole','image_pixels',reference_image=png,pixels=[1200,732]);assert contract['requirements'][:len(old)]==old
    return contract,reference
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out-dir',required=True);a=p.parse_args();out=Path(a.out_dir);out.mkdir(parents=True,exist_ok=False)
    for name,value in zip(['contract.json','reference.json'],build()):(out/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
