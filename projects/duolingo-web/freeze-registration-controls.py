"""Freeze actual clear/reveal interactions and newly discovered login frontend."""
import argparse,json
from pathlib import Path
BASE=Path(__file__).resolve().parent;ROOT=BASE.parents[1];EV=BASE/'evidence/english-registration-controls-v1'
def build():
 c=json.loads((BASE/'frontend-english-v44.json').read_text());old=c['requirements'][:];c.update(revision='english-v45',parent_revision='english-v44',changes=['Actual age clear and password show/hide; discovered distinct login with Apple/forgot-password; typography source probe.'])
 ref=json.loads((BASE/'evidence/english-registration-v1/reference.json').read_text())
 probe=json.loads((EV/'interaction-probes.json').read_text());assert probe['cleared']['value']=='' and probe['cleared']['nextDisabled'];assert probe['visible']==dict(type='text',value='abc') and probe['rehidden']==dict(type='password',value='abc')
 for stem in ['clear-before','cleared','password-hidden','password-visible','login-empty']:
  d=json.loads((EV/'source'/f'{stem}.json').read_text());key='registration-'+stem;path=str((EV/'source'/f'{stem}.json').relative_to(ROOT));png=str((EV/'source'/f'{stem}.png').relative_to(ROOT));s=dict(snapshot=d['snapshot'],elements={},capture=dict(path=png,content_rect_points=[0,0,1200,732],backing_scale=1,window_points=[1200,732]));ref['states'][key]=s
  def add(label,kind,**fields):c['requirements'].append(dict(id=key+'-'+label+'-'+kind,state=key,kind=kind,evidence=[path],**fields))
  specs=[]
  if stem=='clear-before':specs=[(next(r for r in d['visible'] if r['tag']=='BUTTON' and r['rect']==[755.5,264.5,24,24]),'registration-age-clear','button')]
  elif stem.startswith('password'):
   specs=[(next(r for r in d['visible'] if r.get('test')=='password-input'),'registration-password','textbox'),(next(r for r in d['visible'] if r['tag']=='BUTTON' and r['rect']==[755.5,348.5,24,24]),'registration-password-reveal','button')]
  elif stem=='login-empty':
   specs=[(r,'registration-login-'+r['test'],'textbox' if r['tag']=='INPUT' else 'button') for r in d['visible'] if r['tag']=='INPUT' or r.get('test') in ['login-with-google','login-with-facebook','login-with-apple']]
   for text in ['登录','忘记密码？','或者']:add('copy-'+text,'accessible_text',text=text)
  for node,identifier,role in specs:
   s['elements'][identifier]=dict(rect=node['rect'],role=role,enabled=node['enabled']);add(identifier,'element_geometry',element=identifier,rect=node['rect'],tolerance_points=0);add(identifier,'element_role',element=identifier,role=role);add(identifier,'element_boolean',element=identifier,field='enabled',expected=node['enabled'])
  if stem=='cleared':s['interactions']=dict(clear_button_empties_age=True,clear_button_disables_next=True)
  if stem=='password-visible':s['interactions']=dict(reveal_preserves_value=True,reveal_shows_text=True,rehide_restores_secure=True)
  for field in s.get('interactions',{}):add(field,'interaction_boolean',field=field,expected=True)
  add('whole','image_pixels',reference_image=png,pixels=[1200,732])
 assert c['requirements'][:len(old)]==old
 return c,ref
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out-dir',required=True);a=p.parse_args();out=Path(a.out_dir);out.mkdir(parents=True,exist_ok=False)
 for name,v in zip(['contract.json','reference.json'],build()):(out/name).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
