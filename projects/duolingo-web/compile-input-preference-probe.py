"""Freeze independently observed cross-question keyboard/harder preferences.

Four real questions are compressed into an action probe; it is not the seventh
lesson or a replacement for its skip/listening/speech/settlement requirements.
"""
import json
from pathlib import Path
BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[1]
EV = BASE / 'evidence/english-seventh-v1'
OLD = BASE / 'evidence/english-secondary-actions-v1'
def read(path): return json.loads(path.read_text())
def write(path, value): path.write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n')
def relative(path): return path.relative_to(ROOT).as_posix()
source = read(OLD/'secondary-session.json')['session']['challenges']
fixture = read(BASE/'fixture-reference-en-zh-secondary-v2.json')
qs = fixture['data']['candidate_course']['lessons'][0]['questions']
assets = read(BASE/'reference-assets-en-zh-v7.json')
def character(c):
    url = c['character']['image']['svg']
    return next(a['name'] for a in assets if a['url'] == url)
c6 = source[6]['content']; c7 = source[7]['content']
r6 = read(EV/'seventh-q6-answer.json'); r7 = read(EV/'seventh-q7-answer.json')
assert c6['prompt'] == '不要咖啡，谢谢。' and not r6['rejected'] and r6['input'] == 'No coffee, thank you.'
assert c7['prompt'] == '加冰吗？' and not r7['rejected'] and r7['input'] == 'With ice?'
qs.append(dict(id='en-zh-secondary-q6', kind='word_tiles', sourceType='translate', prompt='用英语写出这句话',
    sourceLanguage='zh', hint=c6['prompt'], words=[dict(id=str(i),text=c['text']) for i,c in enumerate(c6['choices'])],
    answer_words=[str(i) for i in c6['correctIndices']], keyboardAnswer=r6['input'], keyboardPrompt='用英语写出这句话',
    explanation='', characterResource=character(c6)))
tokens=c7['displayTokens']; blank=next(i for i,t in enumerate(tokens) if t['isBlank'])
qs.append(dict(id='en-zh-secondary-q7', kind='text_entry', sourceType='completeReverseTranslation', prompt='输入所缺单词',
    hint=c7['prompt'], answer=tokens[blank]['text'], completionPrefix=''.join(t['text'] for t in tokens[:blank]),
    completionSuffix=''.join(t['text'] for t in tokens[blank+1:]), keyboardAnswer=r7['input'], keyboardPrompt='用英语写出这句话',
    explanation='', characterResource=character(c7)))
fixture['data']['evidence'] += [relative(EV/name) for name in ['seventh-q6-before.json','seventh-q7-before.json','lin-binding.json']]
fixture['data']['unknown']='Four-question action probe; original listening/skip/speech/review/settlement and external heart refresh remain required but are not implemented by this fixture. Preference across separate lessons, app restart and full visual/audio equality remain unverified.'
write(BASE/'fixture-reference-en-zh-secondary-v3.json', fixture)
contract=read(BASE/'frontend-english-secondary-v2.json'); contract['revision']='actual-cross-question-input-preferences-v3'
observed=read(BASE/'evidence/english-input-layout-v1/source-observed.json')
for key,name,full in [('en-zh-secondary-harder','secondary-fill-before.json',False),('en-zh-secondary-q6','seventh-q6-before.json',True),('en-zh-secondary-q7','seventh-q7-before.json',True)]:
    path=(OLD if name.startswith('secondary-') else EV)/name
    snap=read(path)['snapshot']
    assert ('textbox "使用英语键入"' in snap) == full
    assert 'button "检查" [disabled]' in snap
    facts={'keyboard_mode':full, 'empty_input':True, 'check_enabled':False}
    state=observed['states'].setdefault(key, {'accessible_text':[],'elements':{}})
    state['interactions']=facts
    fields=['keyboard_mode'] if key=='en-zh-secondary-harder' else list(facts)
    for field in fields:
        contract['requirements'].append(dict(id=key+'-initial-'+field, state=key, kind='interaction_boolean', field=field, expected=facts[field], evidence=[relative(path)]))
for key,name in [('en-zh-secondary-q6','seventh-q6-answer.json'),('en-zh-secondary-q7','seventh-q7-answer.json')]:
    path=EV/name; receipt=read(path); assert not receipt['rejected']
    state=key+'-feedback';observed['states'][state]={'interactions':{'accepted':True},'accessible_text':['继续']}
    contract['requirements'].append(dict(id=state+'-accepted',state=state,kind='interaction_boolean',field='accepted',expected=True,evidence=[relative(path)]))
write(BASE/'frontend-english-secondary-v3.json',contract)
write(EV/'source-preferences-observed.json',observed)
print('Frozen',len(qs),'actual questions and',len(contract['requirements']),'frontend requirements')
