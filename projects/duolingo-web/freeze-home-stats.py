"""Keep real top-stat input modes, measured capture consistency and source menus."""
import argparse,json
from pathlib import Path
from capabilities.rebuild.discovery import frontier
B=Path('projects/duolingo-web');E=B/'evidence/english-home-stats-v1'
p=argparse.ArgumentParser();p.add_argument('--out-dir',required=True);out=Path(p.parse_args().out_dir);out.mkdir(parents=True,exist_ok=False)
def read(p):return json.loads(p.read_text())
c=read(B/'frontend-english-v74.json');prior=c['requirements'][:];h=read(B/'evidence/english-pronunciation-current-v1/history.json');aliases={};states={}
for state,name in [('stats-home-root','home-calibrated-after-close'),('stats-course','course-calibrated'),('stats-streak','streak-calibrated'),('stats-gems','gems-calibrated'),('stats-hearts','hearts-calibrated'),('stats-gems-shop','gems-shop'),('stats-streak-details','streak-details-state'),('stats-course-keyboard','course-entered')]:
 path=E/'source'/(name+'.json');s=read(path);assert s['capture_state_consistent'] is True
 geometry=dict(s['capture_geometry'],state_consistent=s['capture_state_consistent']);assert geometry['backing_scale']==2 and geometry['window_points']==[1200,732]
 ev=[str(path),str(path.with_suffix('.png'))];aliases[state]={};texts=list(dict.fromkeys(t['text'] for t in s['text_runs']));actions=s['actions']
 if state=='stats-home-root':
  for a in actions:
   if a['role']=='button' and a['name'] in ['10','1','505','4']:a['operations']=['hover','click','Enter']
 states[state]=dict(id=state,evidence=str(path),actions=actions);h['states'].append(states[state])
 def add(suffix,kind,**kw):c['requirements'].append(dict(id=state+'-'+suffix,state=state,kind=kind,evidence=ev,**kw))
 add('whole','image_pixels',reference_image=ev[1],pixels=[1200,732],reference_capture=geometry)
 for j,t in enumerate(texts):add('text-'+str(j),'accessible_text',text=t)
 for j,a in enumerate(actions):
  key=f'{state}-action-{j}';first=a['name'].split('\n')[0];native={'10':'stat-course','1':'stat-streak','505':'stat-gems','4':'stat-hearts','英语':'stat-course-english','访问宝石小店':'stat-gems-shop','学习':'nav-learn','发音':'nav-pronunciation','排行榜':'nav-leaderboards','特别任务':'nav-quests','个人档案':'nav-profile','更多':'nav-more'}.get(first)
  if native:aliases[state][key]=native
  add('geometry-'+str(j),'element_geometry',element=key,rect=a['rect'],tolerance_points=0)
  if a['role'] is not None:add('role-'+str(j),'element_role',element=key,role=a['role'])
  add('enabled-'+str(j),'element_boolean',element=key,field='enabled',expected=a['enabled'])
 for menu,label in [('course','我的课程'),('gems','宝石'),('streak','连胜精英俱乐部'),('hearts','红心')]:add(menu+'-presence','interaction_boolean',field='stat_'+menu+'_menu_present',expected=label in texts)
 add('audio','pending',description='No source acoustic equality or full effect mapping inferred from hover/menu observation')
 if state in ['stats-course','stats-course-keyboard']:add('course-enrollment','pending',description='Add-course row visually rendered; enrollment action has no native consumer yet and must be explored/implemented')
 if state=='stats-hearts':add('heart-business','pending',description='Source refill/Super/practice branches observed as controls; not implemented or inferred from presentation')
 if state=='stats-streak-details':add('calendar-business','pending',description='Actual September/October/November panel and close observed; date navigation, streak goals and native panel remain incomplete')
for label,to,key in [('10','stats-course','course'),('1','stats-streak','streak'),('505','stats-gems','gems'),('4','stats-hearts','hearts')]:
 a=next(a for a in states['stats-home-root']['actions'] if a['name']==label)
 h['transitions'].append({'from':'stats-home-root','to':to,'action':a['id'],'operation':'hover','outcome':'observed','evidence':str(E/'source'/(key+'-hover-calibrated.raw.txt'))})
for fr,to,label,receipt in [('stats-gems','stats-gems-shop','访问宝石小店','gems-visit-shop.raw.txt'),('stats-course','stats-home-root','英语','course-select-english.raw.txt'),('stats-streak','stats-streak-details','查看更多','streak-details.raw.txt')]:
 a=next(a for a in states[fr]['actions'] if a['name']==label);h['transitions'].append({'from':fr,'to':to,'action':a['id'],'outcome':'observed','evidence':str(E/'source'/receipt)})
a=next(a for a in states['stats-streak-details']['actions'] if a.get('test')=='close-button');h['transitions'].append({'from':'stats-streak-details','to':'stats-home-root','action':a['id'],'outcome':'observed','evidence':str(E/'source/streak-close2.raw.txt')})
a=next(a for a in states['stats-home-root']['actions'] if a['name']=='10');h['transitions'].append({'from':'stats-home-root','to':'stats-course-keyboard','action':a['id'],'operation':'Enter','outcome':'observed','evidence':str(E/'source/course-enter.raw.txt')})
a=next(a for a in states['stats-home-root']['actions'] if a['name']=='4');h['transitions'].append({'from':'stats-home-root','to':'stats-home-root','action':a['id'],'operation':'click','outcome':'observed','evidence':str(E/'source/hearts-click-exit.raw.txt')})
h['limitations']+=['Only new top-stat root actions declare separate probe modes; legacy activation records do not prove all input modes covered','Source Page.screenshot hover loss and CDP physical/CSS scale mismatch preserved; only coherent measured captures admitted','Source English selection/calendar close returns same visible home; no hidden server equivalence inferred','Real hover/Enter bug repair is a product feedback loop, not matched-budget RSI causal gain']
assert c['requirements'][:len(prior)]==prior
assert len({r['id'] for r in c['requirements']})==len(c['requirements'])
assert len({s['id'] for s in h['states']})==len(h['states'])
c.update(revision='english-v75',parent_revision='english-v74',changes=['Actual original top stat menus, shop navigation and streak calendar','Coherent CDP capture measured independently of reported DOM DPR','Separate hover/click/Enter frontier; source Enter reveals real native keyboard omission'])
f=frontier(Path.cwd(),h)
feedback={'prior':'english-pronunciation-current-v1/history.json','discoveries':['Native top stats were static despite source button semantics','Source hover popovers differ from click and Enter; native Return did not activate focused control','Page screenshot caused hover disappearance; CDP coherence and physical/CSS metrics needed','Streak details reveals multi-month calendar/goal panel; add-course and heart actions still missing'],'next_exploration':['Implement source streak and hearts panels plus actual downstream actions, including recovery and practice; do not substitute a timer-only patch','Explore add-course row and calendar navigation; validate keyboard/mouse modes separately','Continue actual third lesson, lower home story/radio and original sound branches','Use frontend failures and unknown consumers in future preregistered strategy comparison, not raw word-count novelty'],'causal_status':'No new model call or matched-budget RSI/product-quality benefit claim'}
for name,data in [('contract.json',c),('aliases.json',aliases),('history.json',h),('frontier.json',f),('exploration-feedback.json',feedback)]: (out/name).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(dict(prior=len(prior),requirements=len(c['requirements']),states=len(h['states']),edges=len(h['transitions']),pending=len(f['pending']))))
