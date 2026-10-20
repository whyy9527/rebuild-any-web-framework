"""Freeze observed home destinations/returns and retain unmapped action gaps."""
import argparse
import json
from pathlib import Path
B=Path(__file__).resolve().parent; ROOT=B.parents[1]; E=B/'evidence/english-home-journey-v1'

def build():
 c=json.loads((B/'frontend-english-v48.json').read_text());old=c['requirements'][:]
 ref=json.loads((B/'evidence/english-home-clock-v1/reference.json').read_text())
 inventory={'states':{},'journeys':[]};scenarios={'journeys':[]}
 mappings={
 'profile':{'close-button':'registration-back','age-input':'path-age-input','continue-button':'path-age-next','sign-up-button':'registration-switch-login'},
 'login':{'close-button':'login-close','sign-up-button':'login-signup','email-input':'login-address','password-input':'login-password','forgot-password':'login-forgot','register-button':'login-submit','login-with-google':'login-google','login-with-facebook':'login-facebook','login-with-apple':'login-apple'},
 'shop':{'create-profile-juicy':'shop-create-profile'},
 'more':{'det-nav':'more-duolingo-english-test','create-account-button':'more-create-a-profile','settings-button':'more-settings','help-button':'more-help','sign-in-button':'more-sign-in'}}
 copy={'profile':['你的年龄是……'],'login':['邮箱或用户名','密码','忘记密码？','或者','使用 Apple 登录'],'shop':['你赚取了 525 颗宝石！ 创建个人档案，在小店中就能使用邻角啦！','红心','道具','连胜激冻'],'more':['多邻国英语测试','创建档案','设置','帮助','登录']}
 targets={'profile':('profile-tab','nav-profile','registration-back'),'login':('sign-in-juicy','sign-in','login-close'),'shop':('shop-nav','nav-shop','nav-learn'),'more':('more-nav','nav-more','nav-learn')}
 for name in ['profile','login','shop','more']:
  before=json.loads((E/'source'/(name+'-before.json')).read_text());after=json.loads((E/'source'/(name+'-after.json')).read_text());back=json.loads((E/'source'/(name+'-return.json')).read_text())
  assert all(r['viewport']=={'width':1200,'height':732} for r in [before,after,back]), 'Observed viewport mismatch'
  root='home-eight-opened';
  if root not in inventory['states']: inventory['states'][root]=before['actions']
  inventory['states']['journey-'+name]=after['actions'];
  source_test,native_action,native_return=targets[name]
  action=next(a['id'] for a in inventory['states'][root] if (a['name']=='更多' if name=='more' else a['test']==source_test))
  states=['journey-'+name,'journey-'+name+'-return'];inventory['journeys'].append({'id':name,'from':root,'action':action,'states':states})
  scenarios['journeys'].append({'id':name,'native_action':native_action,'native_return':native_return,'operation':'hover' if name=='more' else 'click'})
  for state,receipt,stem in [(states[0],after,name+'-after'),(states[1],back,name+'-return')]:
   image=str((E/'source'/(stem+'.png')).relative_to(ROOT));evidence=[str((E/'source'/(stem+'.json')).relative_to(ROOT)),image]
   ref['states'][state]={'accessible_text':[],'elements':{},'capture':{'path':image,'content_rect_points':[0,0,1200,732],'window_points':[1200,732],'backing_scale':1}}
   def add(kind,suffix,**kwargs):c['requirements'].append({'id':state+'-'+suffix,'state':state,'kind':kind,'evidence':evidence,**kwargs})
   add('image_pixels','whole',reference_image=image,pixels=[1200,732])
   texts=copy[name] if state==states[0] else ['提供或接受饮料','第 1 阶段，第 1 部分']
   source_text='\n'.join(x['text'] for x in receipt['text_runs'])+'\n'+receipt['snapshot']
   for i,text in enumerate(texts):
    assert text in source_text,(name,text)
    ref['states'][state]['accessible_text'].append(text);add('accessible_text','copy-'+str(i),text=text)
   if state==states[0]:
    for source_id,native_id in mappings[name].items():
     candidates=[x for x in receipt['visible'] if x['test']==source_id]
     if name=='shop':candidates=[x for x in candidates if 256<x['rect'][0]<800]
     assert len(candidates)==1,(name,source_id,len(candidates));x=candidates[0]
     role='textbox' if x['tag']=='INPUT' else 'link' if x['tag']=='A' else 'button'
     ref['states'][state]['elements'][native_id]={'rect':x['rect'],'role':role,'enabled':x['enabled']}
     add('element_geometry',native_id+'-rect',element=native_id,rect=x['rect'],tolerance_points=0)
     add('element_role',native_id+'-role',element=native_id,role=role)
     add('element_boolean',native_id+'-enabled',element=native_id,field='enabled',expected=x['enabled'])
    add('pending','audio-output',description='Actual original/native application output for this transition not compared; media start hooks do not prove acoustic equality or silence')
 c.update(revision='english-v49',parent_revision='english-v48',changes=['Actual home destination/return journeys, complete visible action inventory and unresolved audio output; preserve all v48 requirements'])
 assert c['requirements'][:len(old)]==old
 return c,ref,inventory,scenarios

if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out-dir',required=True);out=Path(p.parse_args().out_dir);out.mkdir(parents=True,exist_ok=False)
 for name,value in zip(['contract','reference','inventory','scenarios'],build()):(out/(name+'.json')).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
