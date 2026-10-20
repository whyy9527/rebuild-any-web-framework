"""Freeze newly explored level-review cards before implementing that instance."""
import argparse
import json
from pathlib import Path

BASE=Path(__file__).resolve().parent
ROOT=BASE.parents[1]
EV=BASE/'evidence/english-home-frontier-v1'

def build():
    parent=json.loads((BASE/'frontend-english-v36.json').read_text())
    contract=json.loads(json.dumps(parent))
    contract.update(revision='english-v37',parent_revision='english-v36',changes=['Actual 13-card level review and long typed-answer tooltip; candidate not yet implemented.'])
    reference=json.loads((EV/'reference.json').read_text())
    for suffix,stem in [('open','lesson-review-open'),('long-expanded','lesson-review-long-expanded')]:
        source=json.loads((EV/'source'/(stem+'.json')).read_text())
        cards=[r for r in source['visible'] if r['tag']=='DIV' and r['role']=='button']
        assert len(cards)==13 and cards[7]['text']=='完成翻译\n我想要加牛奶和糖的咖啡。'
        key='level-practice-review-'+suffix
        state=dict(snapshot=source['snapshot'],accessible_text=[],elements={},capture=dict(path=str((EV/'source'/(stem+'.png')).relative_to(ROOT)),content_rect_points=[0,0,1200,732],backing_scale=1,window_points=[1200,732]))
        reference['states'][key]=state
        evidence=[str((EV/'source'/(stem+'.json')).relative_to(ROOT))]
        def add(label,kind,**fields):
            contract['requirements'].append(dict(id=key+'-'+label+'-'+kind,state=key,kind=kind,evidence=evidence,**fields))
        for i,card in enumerate(cards):
            element='review-card-'+str(i)
            state['elements'][element]=dict(rect=card['rect'],role=card['role'],enabled=card['enabled'])
            add(element,'element_geometry',element=element,rect=card['rect'],tolerance_points=0)
            add(element,'element_role',element=element,role=card['role'])
            add(element,'element_boolean',element=element,field='enabled',expected=card['enabled'])
        texts=['查看你的成绩单！','点击下面的小方块来浏览答案吧！']
        if suffix=='long-expanded':
            texts+=['你的答案：','正确答案：',"I'd like coffee with milk and sugar."]
            layout=json.loads((EV/'source/long-tooltip-css.json').read_text())[1]
            assert layout['rect']==[710,467,274.0703125,136]
            state['elements']['result-review-answer']=dict(rect=layout['rect'])
            add('answer','element_geometry',element='result-review-answer',rect=layout['rect'],tolerance_points=0)
        for i,text in enumerate(texts):
            assert text in source['snapshot'],text
            state['accessible_text'].append(text);add('text-'+str(i),'accessible_text',text=text)
        add('whole-image','image_pixels',reference_image=state['capture']['path'],pixels=[1200,732])
    assert contract['requirements'][:2210]==parent['requirements']
    return contract,reference

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out-dir',required=True);a=p.parse_args()
    output=Path(a.out_dir);output.mkdir(parents=True,exist_ok=False)
    for name,value in zip(['contract.json','reference.json'],build()):
        (output/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
