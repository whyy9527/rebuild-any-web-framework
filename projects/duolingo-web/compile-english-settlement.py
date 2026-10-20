"""Extend the actual fourth fixture with observed settlement and completed-path presentation."""
import importlib.util
import json
from pathlib import Path
BASE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('english_fourth',BASE/'compile-english-fourth.py')
fourth=importlib.util.module_from_spec(spec);spec.loader.exec_module(fourth)
fixture=fourth.build_fourth_fixture();course=fixture['data']['candidate_course']
course['lessons'][3]['settlement']=[
 {'id':'en-zh-l4-complete','kind':'result','title':'挑战完成！','continueLabel':'继续','secondaryLabel':'回顾本单元','experience':20},
 {'id':'en-zh-l4-score','kind':'score','title':'离提升你的英语分数又近了一步！','continueLabel':'继续'},
 {'id':'en-zh-l4-streak','kind':'streak','title':'连胜战绩','body':'天天小练，连胜不断；一天不练，连胜不见！','continueLabel':'我可以！','secondaryLabel':'回顾本单元','observedStreak':2},
 {'id':'en-zh-l4-xp-boost','kind':'reward','title':'到手一个经验宝！','body':'恭喜你完成了这个等级！接下来 15 分钟里，做单元练习可得双倍经验！','continueLabel':'继续'},
 {'id':'en-zh-l4-legendary','kind':'legendary','title':'来向我们展示你的传奇实力吧','body':'完成这个超硬核挑战，晋升到传奇等级！','continueLabel':'不，谢谢','secondaryLabel':'开始 +80 经验'},
 {'id':'en-zh-l4-profile','kind':'profile','title':'来创建你的个人档案吧！','body':'创建档案就能保存学习进度，随时都可以继续免费学习后续内容。','continueLabel':'稍后再说','secondaryLabel':'创建档案'}]
source=json.loads((BASE/'evidence/english-settlement-v1/popovers.json').read_text())
assert 'Lesson 1 of 4' in source['next'] and '练习 +5 经验' in source['completed']
course['home']['completedNodeResource']=fourth.compiler.resource(source['completed_icons'][0],'home')
course['pathNodes'][1]['lessonCount']=4
geometry=json.loads((BASE/'evidence/english-settlement-v1/path-geometry.json').read_text())
layout=json.loads((BASE/'evidence/english-settlement-v1/layout.json').read_text())
centers=[(r['rect'][1]+r['rect'][3]/2)-138 for r in geometry]
centers.insert(2,layout['chest']['y']+layout['chest']['height']/2-138)
course['home']['completedNodeCenters']=centers
course['home']['completedPathHeight']=layout['nextSection']['y']-138

fixture['provenance']['evidence'] += ['projects/duolingo-web/evidence/english-fourth-v1/'+n for n in ['complete.json','score.json','streak.json','xp-boost.json','legendary.json','home.json']] + ['projects/duolingo-web/evidence/english-settlement-v1/popovers.json']
fixture['provenance']['source']+='; actual six-stage fourth settlement, completed-node icon and next-node popover'
fixture['provenance']['unknown']='Settlement original graphics/animations, wrong-answer accuracy, review/legendary/profile branches, source calendar and reward timers, second-node content, broader navigation and actual acoustic equivalence remain incomplete. observedStreak is a frozen source snapshot, not a calendar model.'
(BASE/'fixture-reference-en-zh-v5.json').write_text(json.dumps(fixture,ensure_ascii=False,indent=2)+'\n')
(BASE/'reference-assets-en-zh-v5.json').write_text(json.dumps(list(fourth.compiler.resources.values()),ensure_ascii=False,indent=2)+'\n')
print('Compiled six observed settlement stages and completed-node source icon')
