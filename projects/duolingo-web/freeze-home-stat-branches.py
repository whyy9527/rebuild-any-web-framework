"""Freeze actual catalog, practice and refill outcomes without replacing old states."""
import argparse,json,re
from pathlib import Path
from capabilities.rebuild.discovery import frontier
B=Path('projects/duolingo-web');E=B/'evidence/english-home-stat-branches-v1'
p=argparse.ArgumentParser();p.add_argument('--out-dir',required=True);out=Path(p.parse_args().out_dir);out.mkdir(parents=True,exist_ok=False)
def read(p):return json.loads(p.read_text())
c=read(B/'frontend-english-v75.json');prior=c['requirements'][:];h=read(B/'evidence/english-home-stats-v1/history.json');aliases={};states={}
map_names={'10':'stat-course','1':'stat-streak','505':'stat-gems','155':'stat-gems','4':'stat-hearts','5':'stat-hearts','补心':'stat-hearts-refill','做练习获取红心':'stat-hearts-practice','无限红心':'stat-hearts-super','学习':'nav-learn','发音':'nav-pronunciation','排行榜':'nav-leaderboards','特别任务':'nav-quests','个人档案':'nav-profile','更多':'nav-more'}
for state,name in [('stat-branches-courses','courses-transparent-control'),('stat-branches-course-menu','course-keyboard-canonical-state'),('stat-branches-courses-en','courses-en-options-state'),('stat-branches-courses-return','courses-zh-options-state'),('stat-branches-super-login','course-canonical-state'),('stat-branches-practice','heart-practice-state'),('stat-branches-refill','heart-refill-state'),('stat-branches-full','heart-full-state'),('stat-branches-super','heart-super-state')]:
 path=E/'source'/(name+'.json');s=read(path);assert s['capture_state_consistent'] is True
 geometry=dict(s['capture_geometry'],state_consistent=True);assert geometry['backing_scale']==2
 for action in s['actions']:
  if action['role']=='combobox':
   labels=re.findall(r'- option "([^"]+)"',s['snapshot']);assert len(labels)==33 and len(set(labels))==33
   action['operations']=['select:'+label for label in labels]+['Enter','Space']
 ev=[str(path),str(path.with_suffix('.png'))];aliases[state]={};texts=list(dict.fromkeys(t['text'] for t in s['text_runs']));states[state]=dict(id=state,evidence=str(path),actions=s['actions']);h['states'].append(states[state])
 def add(suffix,kind,**kw):c['requirements'].append(dict(id=state+'-'+suffix,state=state,kind=kind,evidence=ev,**kw))
 add('whole','image_pixels',reference_image=ev[1],pixels=[1200,732],reference_capture=geometry)
 for j,t in enumerate(texts):add('text-'+str(j),'accessible_text',text=t)
 for j,a in enumerate(s['actions']):
  key=f'{state}-action-{j}';first=a['name'].split('\n')[0];native=map_names.get(first)
  if state=='stat-branches-course-menu':native={'英语':'stat-course-english'}.get(first,native)
  tests={'stat-branches-super':{'age-input':'path-age-input','continue-button':'path-age-next','close-button':'registration-back','sign-up-button':'registration-switch-login'},'stat-branches-super-login':{'email-input':'login-address','password-input':'login-password','close-button':'login-close','sign-up-button':'login-signup','register-button':'login-submit','forgot-password':'login-forgot','login-with-google':'login-google','login-with-facebook':'login-facebook','login-with-apple':'login-apple'}}
  native=tests.get(state,{}).get(a.get('test'),native)
  if native:aliases[state][key]=native
  add('geometry-'+str(j),'element_geometry',element=key,rect=a['rect'],tolerance_points=0)
  if a['role'] is not None:add('role-'+str(j),'element_role',element=key,role=a['role'])
  add('enabled-'+str(j),'element_boolean',element=key,field='enabled',expected=a['enabled'])
 add('audio','pending',description='No sound equality or silence established for these new source transitions')
 if state in ['stat-branches-courses','stat-branches-courses-en','stat-branches-courses-return']:add('enrollment','pending',description='Actual courses catalog and language options discovered; native consumer and enrollment outcomes incomplete')
 if state=='stat-branches-practice':add('practice-instance','pending',description='Actual first audible pairs differ from existing observed practice instance; no new instance compiled or sound output matched')
# Existing four-heart hover and source actual downstream actions remain distinct.
for to,label,receipt in [('stat-branches-practice','做练习获取红心','heart-practice.raw.txt'),('stat-branches-refill','补心\n350','heart-refill-action.raw.txt')]:
 source=next(s for s in h['states'] if s['id']=='stats-hearts');a=next(a for a in source['actions'] if a['name']==label)
 h['transitions'].append({'from':'stats-hearts','to':to,'action':a['id'],'outcome':'observed','evidence':str(E/'source'/receipt)})
h.setdefault('environment_observations',[]).append({'operation':'actual add-course click','evidence':str(E/'source/course-add.raw.txt'),'observed':'/courses catalog','limits':'Old sampler omitted role menuitem; no action coverage retrofilled into old state'})
a=next(a for a in states['stat-branches-course-menu']['actions'] if a['name']=='添加新课程');h['transitions'].append({'from':'stat-branches-course-menu','to':'stat-branches-courses','action':a['id'],'outcome':'observed','evidence':str(E/'source/course-add-canonical-retry.raw.txt')})
a=next(a for a in states['stat-branches-courses']['actions'] if a['role']=='combobox');h['transitions'].append({'from':'stat-branches-courses','to':'stat-branches-courses-en','action':a['id'],'operation':'select:English','outcome':'observed','evidence':str(E/'source/courses-language-select-action.raw.txt')})
a=next(a for a in states['stat-branches-courses-en']['actions'] if a['role']=='combobox');h['transitions'].append({'from':'stat-branches-courses-en','to':'stat-branches-courses-return','action':a['id'],'operation':'select:中文','outcome':'observed','evidence':str(E/'source/courses-language-zh-action.raw.txt')})
a=next(a for a in states['stat-branches-super']['actions'] if a.get('test')=='close-button');h['transitions'].append({'from':'stat-branches-super','to':'stat-branches-super-login','action':a['id'],'outcome':'observed','evidence':str(E/'source/course-canonical-action.raw.txt')})
a=next(a for a in states['stat-branches-full']['actions'] if a['name'].split('\n')[0]=='无限红心');h['transitions'].append({'from':'stat-branches-full','to':'stat-branches-super','action':a['id'],'outcome':'observed','evidence':str(E/'source/heart-super-action.raw.txt')})
# Reload receipt proves durable balance/heart change; hover is a separate action.
h.setdefault('environment_observations',[]).append({'from':'stat-branches-refill','to':'stat-branches-full','operation':'reload then hover','evidence':str(E/'source/heart-refill-reload-action.raw.txt'),'observed':'505→155 gems after reload, hearts5; full refill/practice disabled','limits':'No server implementation or exact settlement delay inferred'})
for field,text in [('hearts','5'),('gems','155')]:
 c['requirements'].append(dict(id='stat-branches-restarted-'+field,state='stat-branches-restarted',kind='accessible_text',text=text,evidence=[str(E/'source/heart-full-state.json'),str(E/'source/heart-refill-reload-action.raw.txt')]))
c['requirements'].append(dict(id='stat-branches-refill-transient',state='stat-branches-refill-immediate',kind='pending',description='Source400ms action receipt shows hearts5/gems505, later capture155; native driver observes at700ms. Exact transient timing not matched or inferred',evidence=[str(E/'source/heart-refill-action.raw.txt'),str(E/'source/heart-refill-state.json')]))
c['requirements'].append(dict(id='stat-branches-restarted-image',state='stat-branches-restarted',kind='pending',description='No source reload root screenshot without hover; do not compare unlike visual states',evidence=[str(E/'source/heart-refill-reload-action.raw.txt')]))
assert c['requirements'][:len(prior)]==prior
assert len({r['id'] for r in c['requirements']})==len(c['requirements'])
c.update(revision='english-v76',parent_revision='english-v75',changes=['Actual add-course catalog, independent audible-pair practice and durable 350-gem refill','Sampler now includes menuitem and opacity0 native select; actual language selection reaches /courses/en','Full-heart disabled controls and guest Super→age registration','Source400ms receipt still505; later actual capture155. No matched native400ms transient capture'])
h['limitations']+=['Source actual refill changes guest state; old505/4 fixtures preserved separately from155/5','Practice first audible matching instance not equated with prior compiled practice','Opacity0 native select remains actual center hit target; paint visibility is not action availability','33 actual option labels and Enter/Space tracked separately per catalog state; one selection does not resolve whole picker','English language selection did navigate; speculative English heading wait timed out because interface stayed Chinese, original receipt retained','Super age close reaches login; focus/hover probes beneath that overlay were unavailable, not course failures','No new RSI model call or matched-budget gain claim']
f=frontier(Path.cwd(),h)
feedback=dict(discoveries=['Add-course is full courses route, not guest-languages modal','Heart practice is independent audible-pair instance','Refill updates heart immediately but displayed gems settle by reload','Full hearts disable refill and practice; guest Super opens age registration'],next_exploration=['Implement actual catalog/enrollment and streak/calendar consumers','Compile new practice instance and actual sound; continue prior unfinished course/story/radio','Probe insufficient balance and refill later outcomes rather than infer generic rule from one purchase','Measure frontend consumers/input modes and product quality in next preregistered RSI evaluation'],causal_status='Product feedback guided real actions, no new model experiment')
for n,d in [('contract.json',c),('aliases.json',aliases),('history.json',h),('frontier.json',f),('exploration-feedback.json',feedback)]: (out/n).write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(dict(prior=len(prior),requirements=len(c['requirements']),states=len(h['states']),edges=len(h['transitions']),pending=len(f['pending']))))
