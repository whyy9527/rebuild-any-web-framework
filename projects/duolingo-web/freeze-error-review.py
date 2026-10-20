"""Append actual 18-card error/correction states and exact screenshot colors."""
import argparse
import json
from pathlib import Path
from PIL import Image

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[1]
EV = BASE/'evidence/english-error-review-v1'

def build():
    parent = json.loads((BASE/'frontend-english-v34.json').read_text())
    contract = json.loads(json.dumps(parent))
    contract.update(revision='english-v35',parent_revision='english-v34',changes=['Actual first-wrong red card and distinct corrected green card, retained answers and scroll.'])
    reference = json.loads((BASE/'evidence/english-result-review-native-v1/reference.json').read_text())
    for suffix,stem in [('open','review-cards'),('wrong-expanded','review-wrong-expanded'),('correction-expanded','review-correction-expanded')]:
        key='error-practice-review-'+suffix
        source=json.loads((EV/'source'/(stem+'.json')).read_text())
        cards=[r for r in source['visible'] if r['tag']=='DIV' and r['role']=='button']
        assert len(cards)==18 and cards[1]['text']==cards[17]['text']=='"热" 该怎么说？'
        evidence=[str((EV/'source'/(stem+'.json')).relative_to(ROOT))]
        state=dict(snapshot=source['snapshot'],accessible_text=[],elements={},capture=dict(path=str((EV/'source'/(stem+'.png')).relative_to(ROOT)),content_rect_points=[0,0,1200,732],backing_scale=1,window_points=[1200,732]))
        reference['states'][key]=state
        def add(label,kind,**fields):
            contract['requirements'].append(dict(id=key+'-'+label+'-'+kind,state=key,kind=kind,evidence=evidence,**fields))
        for i,card in enumerate(cards):
            element='review-card-'+str(i);state['elements'][element]=dict(rect=card['rect'],role=card['role'],enabled=card['enabled'])
            add(element,'element_geometry',element=element,rect=card['rect'],tolerance_points=0)
            add(element,'element_role',element=element,role=card['role'])
            add(element,'element_boolean',element=element,field='enabled',expected=card['enabled'])
        texts=['查看你的成绩单！','点击下面的小方块来浏览答案吧！']
        if suffix!='open':texts+=['你的答案：','正确答案：','hot']+(['coffee'] if suffix=='wrong-expanded' else [])
        for i,text in enumerate(texts):
            assert text in source['snapshot'],text
            state['accessible_text'].append(text);add('text-'+str(i),'accessible_text',text=text)
        add('whole-image','image_pixels',reference_image=state['capture']['path'],pixels=[1200,732])
        # Interior backgrounds away from text/icons; actual PNG sampled below.
        points=[(540,345)] if suffix!='correction-expanded' else [(540,640)]
        state['pixel_color_space']='sRGB';state['pixel_samples']={}
        with Image.open(EV/'source'/(stem+'.png')) as image:
            for point in points:
                rgb=list(image.convert('RGB').getpixel(point));expected=[215,255,184] if suffix=='correction-expanded' else [255,223,224]
                assert rgb==expected,(suffix,rgb)
                state['pixel_samples'][','.join(map(str,point))]=rgb
                add('card-background','pixel_color',point=list(point),rgb=rgb)
    assert contract['requirements'][:2027]==parent['requirements']
    return contract,reference

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out-dir',required=True);a=p.parse_args()
    output=Path(a.out_dir);output.mkdir(parents=True,exist_ok=False)
    for name,value in zip(['contract.json','reference.json'],build()):
        (output/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
