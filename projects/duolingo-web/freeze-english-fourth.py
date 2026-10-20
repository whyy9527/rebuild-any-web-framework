"""Freeze discovered fourth-lesson needs and exploration outcomes; no candidate pass invented."""
import json
import re
from pathlib import Path

BASE=Path(__file__).resolve().parent
ROOT=BASE.parent.parent
EV=BASE/'evidence/english-fourth-v1'
def read(name): return json.loads((EV/name).read_text())
def evidence(name): return (EV/name).relative_to(ROOT).as_posix()
def write(path,data): path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
rows={}
for name in ['replay-02.json','replay-03.json']:
    for row in read(name)['observed']:
        if row.get('feedback'): rows[row['index']]=(row,name)
assert set(rows)==set(range(12))
assert all('正确答案：' not in row['feedback'] for row,_ in rows.values())
requirements=[]
def text(state,value,name,suffix):
    requirements.append(dict(id=state+'-'+suffix,state=state,kind='accessible_text',text=value,evidence=[evidence(name)]))
def pending(state,description,name,suffix):
    requirements.append(dict(id=state+'-'+suffix,state=state,kind='pending',description=description,evidence=[evidence(name)]))
for i,(row,name) in sorted(rows.items()):
    state=f'en-zh-l4-q{i}'
    text(state,row['heading'],name,'heading')
    values=row['identity']['actual']['choices']
    for j,value in enumerate(dict.fromkeys(values)):
        text(state,value,name,f'choice-{j}')
    if '错题重练' in row['before']: text(state,'错题重练',name,'indicator')
    if '挑战题' in row['before']: text(state,'挑战题',name,'indicator')
    for suffix,description in [('visual','Same-state source/candidate layout, font, original graphics and animation equality'),('audio','Actual triggered application speech and effect output equality'),('interaction','Same-state selection, undo, grading and feedback behavior equality')]:
        pending(state,description,name,suffix)
for state,name,values in [
    ('en-zh-l4-entry','reloaded-entry.json',['来复习一下这个等级，完成后有惊喜哦！','下次再说','开始挑战 +20 经验']),
    ('en-zh-l4-review-intro','review-intro.json',['一起来复习一下之前你不太熟练的部分吧！','继续']),
    ('en-zh-l4-hard-intro','replay-02.json',['来试试这个等级里最有挑战性的练习吧！','继续']),
    ('en-zh-l4-complete','complete.json',['挑战完成！','总经验','超级棒','回顾本单元','继续']),
    ('en-zh-l4-score','score.json',['离提升你的英语分数又近了一步！','继续']),
    ('en-zh-l4-streak','streak.json',['天天小练，连胜不断；一天不练，连胜不见！','我可以！']),
    ('en-zh-l4-xp-boost','xp-boost.json',['到手一个经验宝！','恭喜你完成了这个等级！接下来 15 分钟里，做单元练习可得双倍经验！','继续']),
    ('en-zh-l4-legendary','legendary.json',['来向我们展示你的传奇实力吧','完成这个超硬核挑战，晋升到传奇等级！','开始 +80 经验','不，谢谢']),
    ('home-after-lesson-3','post-third-profile.json',['青铜等级','查看排行榜','这周的排行榜挑战赛即将开始！','505']),
    ('home-after-lesson-4','home.json',['青铜等级','查看排行榜','505','Lesson 1 of 4']),
]:
    for j,value in enumerate(values): text(state,value,name,f'text-{j}')
    pending(state,'Same-state visual and transition comparison still pending',name,'visual-transition')
text('en-zh-l4-complete','20','reference-fourth-complete.png','xp')
text('en-zh-l4-complete','100%','reference-fourth-complete.png','accuracy')
contract=dict(revision='actual-en-zh-fourth-frontends-v1',scope='Actual fourth lesson and newly discovered completion/home states; candidate not yet implemented',requirements=requirements)
write(BASE/'frontend-english-fourth-v1.json',contract)
prior=json.loads((BASE/'frontend-english-v4.json').read_text())
write(BASE/'frontend-english-v5.json',dict(revision='actual-en-zh-frontends-v5',scope='Preserves all v4 requirements and appends actual fourth-lesson discoveries',requirements=prior['requirements']+requirements))
states=[];transitions=[]
def state(id,name,actions):
    states.append(dict(id=id,evidence=evidence(name),actions=[dict(id=a,label=l) for a,l in actions]))
def move(src,action,dst,name,outcome='observed'):
    transitions.append(dict(**{'from':src,'action':action,'to':dst,'outcome':outcome,'evidence':evidence(name)}))
state('entry','reloaded-entry.json',[('start','开始挑战 +20 经验'),('later','下次再说')])
state('review-intro','review-intro.json',[('continue','继续')]);move('entry','start','review-intro','reloaded-entry.json')
state('hard-intro','replay-02.json',[('continue','继续')])
for i,(row,name) in sorted(rows.items()):
    actions=[('submit','Submit observed choice/word answer')]
    # Only controls actually visible in the stored pre-action snapshot enter the frontier.
    for action,label in [('skip','跳过'),('keyboard','使用键盘'),('disable-listening','现在不做听力题')]:
        if f'button "{label}"' in row['before']: actions.append((action,label))
    if row['type']=='listenTap': actions.append(('play','Explicit normal-speed source playback'))
    state(f'q{i}',name,actions);state(f'feedback{i}',name,[('continue','继续')])
    if i==5: move('q5','submit',None,'replay-02.json','unavailable')
    move(f'q{i}','submit',f'feedback{i}',name)
    if row['type']=='listenTap': move(f'q{i}','play',f'q{i}',name)
    if i<11: move(f'feedback{i}','continue','hard-intro' if i==4 else f'q{i+1}',name)
move('review-intro','continue','q0','review-intro.json')
move('hard-intro','continue','q5','replay-02.json')
for id,name,actions in [
    ('complete','complete.json',[('continue','继续'),('review','回顾本单元')]),
    ('score','score.json',[('continue','继续')]),
    ('streak','streak.json',[('continue','我可以！'),('review','回顾本单元')]),
    ('xp-boost','xp-boost.json',[('continue','继续'),('review','回顾本单元')]),
    ('legendary','legendary.json',[('decline','不，谢谢'),('start','开始 +80 经验')]),
    ('profile','home.json',[('later','稍后再说'),('create','创建档案')]),
    ('home','home.json',[('next-node','Lesson 1 of 4'),('leaderboard','查看排行榜'),('pronunciation','发音')]),
]: state(id,name,actions)
move('feedback11','continue','complete','complete.json')
for src,dst,name,action in [('complete','score','complete.json','continue'),('score','streak','score.json','continue'),('streak','xp-boost','streak.json','continue'),('xp-boost','legendary','xp-boost.json','continue'),('legendary','profile','legendary.json','decline'),('profile','home','home.json','later')]: move(src,action,dst,name)
write(EV/'history.json',dict(kind='actual-reference-exploration-history',scope='One actual regenerated fourth en/zh session and real completion chain; no whole-app coverage claim',states=states,transitions=transitions))
print(json.dumps(dict(accepted_questions=len(rows),new_frontend_requirements=len(requirements),combined_requirements=len(prior['requirements'])+len(requirements),states=len(states),transitions=len(transitions))))
