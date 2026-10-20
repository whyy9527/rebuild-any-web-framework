"""Freeze the real next Practice start/profile interruption before implementing it."""
import argparse,json
from pathlib import Path
BASE=Path(__file__).resolve().parent
ROOT=BASE.parents[1]
EV=BASE/'evidence/english-chest-v1'
def build():
    contract=json.loads((BASE/'frontend-english-v40.json').read_text());old=contract['requirements'][:]
    contract.update(revision='english-v41',parent_revision='english-v40',changes=['Actual next Practice start opens a profile prompt; Later returns to learn with chest/gems retained. Candidate not yet implemented.'])
    reference=json.loads((EV/'reference-v40.json').read_text())
    for stem in ['practice-start-profile','practice-profile-dismissed']:
        source=json.loads((EV/'source'/f'{stem}.json').read_text());key='chest-'+stem;path=str((EV/'source'/f'{stem}.json').relative_to(ROOT));png=str((EV/'source'/f'{stem}.png').relative_to(ROOT))
        state=dict(snapshot=source['snapshot'],accessible_text=[],elements={},capture=dict(path=png,content_rect_points=[0,0,1200,732],backing_scale=1,window_points=[1200,732]));reference['states'][key]=state
        def add(label,kind,**fields):contract['requirements'].append(dict(id=key+'-'+label+'-'+kind,state=key,kind=kind,evidence=[path],**fields))
        if stem=='practice-start-profile':
            for i,text in enumerate(['来创建你的个人档案吧！','创建档案就能保存学习进度，随时都可以继续免费学习后续内容。']):state['accessible_text'].append(text);add('copy-'+str(i),'accessible_text',text=text)
            for name,label in [('path-profile-create','创建档案'),('path-profile-later','稍后创建帐户')]:
                button=[r for r in source['visible'] if r['tag']=='BUTTON' and r.get('text')==label][-1]
                state['elements'][name]=dict(rect=button['rect'],role='button',enabled=button['enabled'])
                add(name,'element_geometry',element=name,rect=button['rect'],tolerance_points=0);add(name,'element_role',element=name,role='button');add(name,'element_boolean',element=name,field='enabled',expected=True)
        else:
            assert '稍后创建帐户' not in source['snapshot'];state['interactions']=dict(profile_closed=True);add('closed','interaction_boolean',field='profile_closed',expected=True);state['accessible_text'].append('525');add('gems','accessible_text',text='525')
        add('whole','image_pixels',reference_image=png,pixels=[1200,732])
    assert contract['requirements'][:len(old)]==old
    return contract,reference
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out-dir',required=True);a=p.parse_args();out=Path(a.out_dir);out.mkdir(parents=True,exist_ok=False)
    for name,value in zip(['contract.json','reference.json'],build()):(out/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
