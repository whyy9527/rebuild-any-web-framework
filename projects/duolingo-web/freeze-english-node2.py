"""Preserve v6 and add source-observed node-two input and speaking states."""
import json
from pathlib import Path
BASE=Path(__file__).resolve().parent;EV=BASE/'evidence/english-next-node-v1'
previous=json.loads((BASE/'frontend-english-v6.json').read_text());req=[]
def add(state,kind,suffix,filename,**fields):
 req.append(dict(id=state+'-'+suffix,state=state,kind=kind,evidence=['projects/duolingo-web/evidence/english-next-node-v1/'+filename],**fields))
for index,filename in [(3,'listen-complete-response.json'),(5,'reverse-response.json')]:
 state=f'en-zh-node2-q{index}'
 response=json.loads((EV/filename).read_text())
 add(state,'accessible_text','heading',filename,text='输入所缺单词')
 suffix='or coffee?' if index==3 else '.'
 add(state,'accessible_text','fixed-suffix',filename,text=suffix)
 if index==5:add(state,'accessible_text','prompt',filename,text='我想要茶。')
 if index==3:
  for field in ['empty_check_disabled','nonempty_check_enabled','cleared_check_disabled']:
   add(state+'-filled','interaction_boolean',field,filename,field=field,expected=True)
 add(state+'-submitted','interaction_boolean','locked',filename,field='submitted_input_locked',expected=True)
 feedback='太棒了！' if index==3 else '你太棒了！'
 add(state+'-feedback','accessible_text','source-feedback',filename,text=feedback)
 for category in ['visual','audio','full-grader']:
  add(state,'pending',category,filename,description='Source/candidate '+category+' equivalence not proved by this input probe')
for value in ['朗读下面的句子','点击并开始录音','现在不做口语题']:
 add('en-zh-node2-q6','accessible_text','text-'+str(len(req)),'speak-entry.json',text=value)
for value in ['麦克风已关闭','将在 15 分钟后恢复']:
 add('en-zh-node2-q6-declined','accessible_text','text-'+str(len(req)),'speak-declined.json',text=value)
add('en-zh-node2-q6','pending','recognition','speak-entry.json',description='Source actual microphone recognition and candidate implementation unverified')
product=dict(revision='actual-en-zh-frontends-v7',scope='Preserve v6; append actually observed node-two input and speaking requirements without replacing the full lesson',requirements=previous['requirements']+req)
(BASE/'frontend-english-v7.json').write_text(json.dumps(product,ensure_ascii=False,indent=2)+'\n')
probe=dict(revision='node2-input-probe-v1',scope='Two isolated input states only; not product acceptance or full node-two curriculum',requirements=[r for r in req if r['state'].startswith(('en-zh-node2-q3','en-zh-node2-q5'))])
(BASE/'frontend-english-input-probe.json').write_text(json.dumps(probe,ensure_ascii=False,indent=2)+'\n')
print('Full requirements',len(product['requirements']),'input component requirements',len(probe['requirements']))
