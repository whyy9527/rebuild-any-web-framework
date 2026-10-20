"""Freeze actually executed age/registration screens, preserving earlier requirements."""
import argparse,json
from pathlib import Path
BASE=Path(__file__).resolve().parent;ROOT=BASE.parents[1];EV=BASE/'evidence/english-registration-v1'
def build():
    contract=json.loads((BASE/'frontend-english-v43.json').read_text());old=contract['requirements'][:];contract.update(revision='english-v44',parent_revision='english-v43',changes=['Actual filled/cleared age, registration methods, empty email form and empty-submit errors; no successful registration or OAuth observed.'])
    reference=json.loads((BASE/'evidence/english-path-profile-v1/reference-v43.json').read_text())
    for stem in ['filled','methods','email','email-invalid']:
        source=json.loads((EV/'source'/f'{stem}.json').read_text());key='registration-'+stem;path=str((EV/'source'/f'{stem}.json').relative_to(ROOT));png=str((EV/'source'/f'{stem}.png').relative_to(ROOT))
        state=dict(snapshot=source['snapshot'],accessible_text=[],elements={},capture=dict(path=png,content_rect_points=[0,0,1200,732],backing_scale=1,window_points=[1200,732]));reference['states'][key]=state
        def add(label,kind,**fields):contract['requirements'].append(dict(id=key+'-'+label+'-'+kind,state=key,kind=kind,evidence=[path],**fields))
        title='你的年龄是……' if stem=='filled' else '选个注册方式才能继续哦！' if stem=='methods' else '创建档案';state['accessible_text'].append(title);add('title','accessible_text',text=title)
        if stem=='filled':specs=[('age-input','path-age-input','textbox'),('continue-button','path-age-next','button')]
        elif stem=='methods':specs=[('login-with-google','registration-google','button'),('login-with-facebook','registration-facebook','button'),(None,'registration-email','button')]
        else:specs=[('full-name-input','registration-name','textbox'),('email-input','registration-address','textbox'),('password-input','registration-password','textbox'),('register-button','registration-submit','button')]
        for test,identifier,role in specs:
            node=next(r for r in source['visible'] if (r.get('test')==test if test else r['tag']=='BUTTON' and r.get('text')=='使用电子邮件继续'))
            state['elements'][identifier]=dict(rect=node['rect'],role=role,enabled=node['enabled'])
            add(identifier,'element_geometry',element=identifier,rect=node['rect'],tolerance_points=0);add(identifier,'element_role',element=identifier,role=role);add(identifier,'element_boolean',element=identifier,field='enabled',expected=node['enabled'])
        if stem=='filled':
            probe=json.loads((EV/'input-probe.json').read_text());assert probe['value']=='28' and probe['nextEnabled'] and probe['clearedDisabled'];state['interactions']=dict(age_value_correct=True,cleared_disabled=True)
            for field in ['age_value_correct','cleared_disabled']:add(field,'interaction_boolean',field=field,expected=True)
        if stem=='email-invalid':
            for text in ['邮箱地址无效','密码太短了']:assert text in source['snapshot'];state['accessible_text'].append(text);add('error-'+text,'accessible_text',text=text)
        add('whole','image_pixels',reference_image=png,pixels=[1200,732])
    assert contract['requirements'][:len(old)]==old
    return contract,reference
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out-dir',required=True);a=p.parse_args();out=Path(a.out_dir);out.mkdir(parents=True,exist_ok=False)
    for name,value in zip(['contract.json','reference.json'],build()):(out/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
