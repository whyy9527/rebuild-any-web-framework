"""Preserve v39 and add the actual next Practice start control omitted there."""
import json,argparse
from pathlib import Path
BASE=Path(__file__).resolve().parent
ROOT=BASE.parents[1]
EV=BASE/'evidence/english-chest-v1'
def build():
    contract=json.loads((BASE/'frontend-english-v39.json').read_text());parent=contract['requirements'][:]
    contract.update(revision='english-v40',parent_revision='english-v39',changes=['Actual next Practice start link geometry/role/enabled; v39 omitted this frontend control.'])
    reference=json.loads((EV/'reference.json').read_text());source=json.loads((EV/'source/practice-entry-settled.json').read_text());key='chest-practice-entry-settled'
    link=next(r for r in source['visible'] if r['tag']=='A' and r.get('text')=='开始 +10 经验');assert link['enabled']
    path=str((EV/'source/practice-entry-settled.json').relative_to(ROOT));png=str((EV/'source/practice-entry-settled.png').relative_to(ROOT))
    reference['states'][key]=dict(snapshot=source['snapshot'],accessible_text=['第 1/2 单元','开始 +10 经验'],elements={'start-lesson-confirm':dict(rect=link['rect'],role='link',enabled=True)},capture=dict(path=png,content_rect_points=[0,0,1200,732],backing_scale=1,window_points=[1200,732]))
    def add(label,kind,**fields):contract['requirements'].append(dict(id=key+'-'+label+'-'+kind,state=key,kind=kind,evidence=[path],**fields))
    for text in ['第 1/2 单元','开始 +10 经验']:add('text-'+str(len(contract['requirements'])),'accessible_text',text=text)
    add('start','element_geometry',element='start-lesson-confirm',rect=link['rect'],tolerance_points=0)
    add('start','element_role',element='start-lesson-confirm',role='link')
    add('start','element_boolean',element='start-lesson-confirm',field='enabled',expected=True)
    add('whole','image_pixels',reference_image=png,pixels=[1200,732])
    assert contract['requirements'][:len(parent)]==parent
    return contract,reference
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out-dir',required=True);a=p.parse_args();out=Path(a.out_dir);out.mkdir(parents=True,exist_ok=False)
    for name,value in zip(['contract.json','reference.json'],build()):(out/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
