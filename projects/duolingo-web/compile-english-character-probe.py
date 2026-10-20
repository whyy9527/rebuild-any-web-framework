"""Freeze the actual sixth-lesson Bea state for native renderer verification.

This isolated component is not the sixth lesson compiled into the curriculum.
"""
import importlib.util
import json
import re
from pathlib import Path
BASE = Path(__file__).resolve().parent
EV = BASE/'evidence/english-character-render-v1'
def read(name): return json.loads((EV/name).read_text())
def write(name, data): (BASE/name).write_text(json.dumps(data, ensure_ascii=False, indent=2)+'\n')
spec = importlib.util.spec_from_file_location('english_compiler', BASE/'compile-english-course.py')
compiler = importlib.util.module_from_spec(spec); spec.loader.exec_module(compiler)
source = read('sixth-session.json')['session']
before = read('bea-idle.json'); feedback = read('bea-correct.json')
c = source['challenges'][0]['content']
assert c['prompt'] == '牛奶' and c['character']['name'] == 'BEA'
assert before['prompt'].splitlines()[1] == c['prompt']
assert feedback['renderer']['correct'] is True and '不错哦！' in feedback['before']
bank = re.findall(r'- button "([^"\n]+)"', before['before'])
bank = [text for text in bank if text not in ['跳过','使用键盘','检查']]
answer = [c['choices'][i]['text'] for i in c['correctIndices']]
row = dict(before=before['before'], heading='用英语写出这句话', feedback=feedback['before'],
           word_bank=bank, actions=[dict(word=t) for t in answer])
q = compiler.compile_questions(dict(source, challenges=[source['challenges'][0]]), {0:row}, {}, prefix='en-zh-render-q')[0]
q['correctFeedback'] = '不错哦！'
fixture = dict(data=dict(candidate_course=dict(id='english-bea-renderer-probe', title='提供或接受饮料',
    speechLanguage='en', interfaceLanguage='zh', lessons=[dict(id='renderer-probe', title='角色渲染验证', questions=[q])],
    pathNodes=[dict(kind='star', lessonIDs=['renderer-probe'], lessonCount=4)])),
    provenance=dict(source='Actual sixth-lesson q0 before/accepted feedback, exact source Rive buffer and public asset match',
    evidence=['projects/duolingo-web/evidence/english-character-render-v1/'+n for n in ['sixth-session.json','bea-idle.json','bea-correct.json','asset-verification.json']],
    scope='Isolated actual renderer state; not full sixth lesson', unknown='Full pose/timing/geometry/font/audio equality and all other characters remain unverified'))
write('fixture-english-character-probe.json', fixture)
write('reference-assets-english-character-probe.json', list(compiler.resources.values()))
refs=fixture['provenance']['evidence']; state=q['id']
requirements=[dict(id=state+'-heading',state=state,kind='accessible_text',text=q['prompt'],evidence=refs),
    dict(id=state+'-hint',state=state,kind='accessible_text',text=q['hint'],evidence=refs),
    dict(id=state+'-geometry',state=state,kind='element_geometry',element='question-character',
         rect=[before['metadata']['rect'][key] for key in ['x','y','width','height']],tolerance_points=0,evidence=refs),
    dict(id=state+'-feedback',state=state+'-feedback',kind='accessible_text',text='不错哦！',evidence=refs)]
for dimension in ['visual','source-animation-timing','actual-audio','wrong-feedback','mouth-sync']:
    requirements.append(dict(id=state+'-'+dimension,state=state,kind='pending',description=dimension+' equality remains unverified',evidence=refs))
write('frontend-english-character-v1.json',dict(revision='actual-Bea-renderer-v1',scope='Actual source character geometry and state, with fidelity gaps explicit',requirements=requirements))
print('Compiled actual Bea source state and',len(requirements),'renderer requirements')
