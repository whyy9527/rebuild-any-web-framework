"""Freeze actual post-eighth settlement; preserve every earlier frontend requirement."""
import argparse
import json
from pathlib import Path
BASE=Path(__file__).resolve().parent
ROOT=BASE.parents[1]
EV=BASE/'evidence/english-eighth-integration-v1'
PAGES=[('score-progress','离提升你的英语分数又近了一步！',None,'继续'),
       ('boost-reward','到手一个经验宝！','恭喜你完成了这个等级！接下来 15 分钟里，做单元练习可得双倍经验！','继续'),
       ('legendary-offer','来向我们展示你的传奇实力吧','完成这个超硬核挑战，晋升到传奇等级！','不，谢谢'),
       ('profile','来创建你的个人档案吧！','创建档案就能保存学习进度，随时都可以继续免费学习后续内容。','稍后再说')]
def build():
    parent=json.loads((BASE/'frontend-english-v37.json').read_text())
    contract=json.loads(json.dumps(parent))
    contract.update(revision='english-v38',parent_revision='english-v37',changes=['Actual default eighth lesson settlement: score progress, experience boost, legendary offer and profile; all prior requirements retained.'])
    reference=json.loads((BASE/'evidence/english-home-frontier-v1/reference-v37.json').read_text())
    for stem,title,body,label in PAGES:
        source=json.loads((EV/'source'/f'{stem}.json').read_text())
        assert title in source['snapshot']
        buttons=[r for r in source['visible'] if r['tag']=='BUTTON' and r.get('text')==label]
        assert len(buttons)==1
        button=buttons[0]; key='eighth-'+stem
        evidence=[str((EV/'source'/f'{stem}.json').relative_to(ROOT))]
        png=str((EV/'source'/f'{stem}.png').relative_to(ROOT))
        texts=[title]+([body] if body else [])
        reference['states'][key]=dict(snapshot=source['snapshot'],accessible_text=texts,elements={'settlement-continue':dict(rect=button['rect'],role='button',enabled=button['enabled'])},capture=dict(path=png,content_rect_points=[0,0,1200,732],backing_scale=1,window_points=[1200,732]))
        def add(kind,**fields):
            suffix=str(len(contract['requirements'])) if kind=='accessible_text' else ''
            contract['requirements'].append(dict(id=key+'-'+kind+('-'+suffix if suffix else ''),state=key,kind=kind,evidence=evidence,**fields))
        for text in texts:add('accessible_text',text=text)
        add('element_geometry',element='settlement-continue',rect=button['rect'],tolerance_points=0)
        add('element_role',element='settlement-continue',role='button')
        add('element_boolean',element='settlement-continue',field='enabled',expected=True)
        add('image_pixels',reference_image=png,pixels=[1200,732])
    assert contract['requirements'][:2298]==parent['requirements']
    assert len(contract['requirements'])==2321
    return contract,reference
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out-dir',required=True);a=p.parse_args()
    output=Path(a.out_dir);output.mkdir(parents=True,exist_ok=False)
    for name,value in zip(['contract.json','reference.json'],build()):
        (output/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
