"""Append actual action availability and completed-path needs without weakening v5."""
import json
from pathlib import Path
BASE=Path(__file__).resolve().parent
root=BASE.parent.parent
previous=json.loads((BASE/'frontend-english-v5.json').read_text())
requirements=[]
def add(id,state,kind,**fields):requirements.append(dict(id=id,state=state,kind=kind,**fields))
for suffix,name in [('complete','complete.json'),('score','score.json'),('streak','streak.json'),('xp-boost','xp-boost.json'),('legendary','legendary.json'),('profile','home.json')]:
    state='en-zh-l4-'+suffix;ev=['projects/duolingo-web/evidence/english-fourth-v1/'+name]
    add(state+'-transition',state,'interaction_boolean',field='next_state_reached',expected=True,evidence=ev)
    if suffix!='score':add(state+'-secondary-action',state,'interaction_boolean',field='secondary_action_available',expected=suffix!='xp-boost',evidence=['projects/duolingo-web/evidence/english-fourth-v1/reference-fourth-xp-boost.png'] if suffix=='xp-boost' else ev)
    add(state+'-sound',state,'pending',description='Actual source/candidate same-state effect/speech output equality',evidence=ev)
for state,values in [('en-zh-completed-popover',['提供或接受饮料','完成传奇挑战，展示你的传奇实力','练习 +5 经验','晋升传奇 +40 经验']),('en-zh-next-popover',['提供或接受饮料','第 1/4 单元','开始 +10 经验'])]:
    ev=['projects/duolingo-web/evidence/english-settlement-v1/popovers.json']
    for i,value in enumerate(values):add(state+f'-text-{i}',state,'accessible_text',text=value,evidence=ev)
    add(state+'-visual',state,'pending',description='Same-state original popover geometry and pixels',evidence=ev)
for state,field in [('en-zh-completed-popover','practice_action_available'),('en-zh-completed-popover','legendary_action_available'),('en-zh-next-popover','start_enabled')]:
    add(state+'-'+field,state,'interaction_boolean',field=field,expected=True,evidence=['projects/duolingo-web/evidence/english-settlement-v1/popovers.json'])
geometry=json.loads((BASE/'evidence/english-settlement-v1/path-geometry.json').read_text())
for i,row in enumerate(geometry[:2]):
    add(f'home-after-lesson-4-node-{i}-geometry','home-after-lesson-4','element_geometry',element='start-lesson' if i==0 else 'start-lesson-1',rect=row['rect'],tolerance_points=0,evidence=['projects/duolingo-web/evidence/english-settlement-v1/path-geometry.json'])
for i,text in enumerate(['来创建你的个人档案吧！','创建档案就能保存学习进度，随时都可以继续免费学习后续内容。','创建档案','稍后再说']):
    add(f'en-zh-l4-profile-text-{i}','en-zh-l4-profile','accessible_text',text=text,evidence=['projects/duolingo-web/evidence/english-fourth-v1/home.json'])
result=dict(revision='actual-en-zh-frontends-v6',scope='Preserves v5 and adds source-observed action affordances, fourth settlement and completed path controls',requirements=previous['requirements']+requirements)
(BASE/'frontend-english-v6.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print('Frozen',len(requirements),'new needs;',len(result['requirements']),'total')
