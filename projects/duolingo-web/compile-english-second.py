"""Append the actual second-lesson UI trajectory; preserve frozen English v1."""
import importlib.util
import json
from pathlib import Path
import re

BASE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('english_course',BASE/'compile-english-course.py')
compiler=importlib.util.module_from_spec(spec);spec.loader.exec_module(compiler)
def build_second_fixture():
    fixture=compiler.build_first_fixture()
    EV=BASE/'evidence/english-second-v1'
    def read(name):return json.loads((EV/name).read_text())
    source=read('session.json')['session'];rows={}
    for name in ['replay-01.json','replay-02.json']:
        for row in read(name)['observed']:
            if row.get('feedback'):rows[row['index']]=row
    assert set(rows)==set(range(12))
    # The API tail is not the tail actually visited. Keep it as original evidence;
    # never manufacture its acceptance feedback or substitute it for observed UI.
    normal=dict(source,challenges=source['challenges'][:12])
    questions=compiler.compile_questions(normal,rows,{},prefix='en-zh-l2-q')
    ui=json.loads((EV/'ui-transcription.json').read_text())
    fill=questions[4];fill['example']=ui['fill']['example']
    # Same source sentence/speaker clip appears in question 7. This is an explicit
    # candidate mapping; the example button's actual play URL remains unobserved.
    fill['exampleAudioResource']=compiler.resource(source['challenges'][7]['content']['tts'],'speech')
    for i,name in enumerate(['english-second-adaptive.json','english-second-adaptive-2.json','english-second-adaptive-3.json'],12):
        row=read(name);assert not row.get('rejected') and '继续' in row['feedback']
        assert '正确答案：' not in row['feedback']
        texts=[t for t in re.findall(r'- button "([^"\n]+)"',row['before']) if t not in ['跳过','使用键盘','检查']]
        actions=row['actions'];assert actions[-2:]==['检查','继续']
        words=[{'id':f'word-{j}','text':t} for j,t in enumerate(texts)]
        answer=actions[:-2];assert set(answer)<=set(texts)
        q={'id':f'en-zh-l2-q{i}','kind':'word_tiles','sourceType':'translate',
           'prompt':'用英语写出这句话','indicator':'挑战题','hint':ui['adaptive'][str(i)]['hint'],
           'sourceLanguage':'zh','newWord':False,'explanation':'','words':words,
           'answer_words':[next(w['id'] for w in words if w['text']==t) for t in answer]}
        questions.append(q)
    assert len(questions)==15
    course=fixture['data']['candidate_course']
    interludes=[]
    for i, row in enumerate(read('replay-02.json')['interludes']):
        text=re.findall(r'- text: (.+)',row['snapshot'])[-1].strip(chr(34))
        interludes.append({'id':f'en-zh-l2-interlude-{i}', 'afterQuestionID':f'en-zh-l2-q{row["before_index"]-1}', 'text':text})
    course['lessons'].append({'id':'lesson-2','title':'Lesson 2 of 4','questions':questions,'interludes':interludes})
    course['pathNodes'][0]['lessonIDs'].append('lesson-2')
    fixture['provenance']['source']+='; second actual lesson: 12 UI-confirmed initial questions and 3 accepted adaptive translations, not initial API tail'
    fixture['provenance']['evidence'] += ['projects/duolingo-web/evidence/english-second-v1/'+n for n in [
        'session.json','replay-01.json','replay-02.json','ui-transcription.json',
        'english-second-adaptive.json','english-second-adaptive-2.json','english-second-adaptive-3.json']]
    fixture['provenance']['unknown']='Other second-lesson trajectories, adaptive trigger/selection rules, later lessons, example-button sound URL, hard-question character assets, full completion chain, first-error tutorial, encouragement, animation and acoustic equivalence remain unverified'
    return fixture

if __name__ == "__main__":
    fixture=build_second_fixture()
    (BASE/'fixture-reference-en-zh-v2.json').write_text(json.dumps(fixture,ensure_ascii=False,indent=2)+'\n')
    (BASE/'reference-assets-en-zh-v2.json').write_text(json.dumps(list(compiler.resources.values()),ensure_ascii=False,indent=2)+'\n')
    print(f'Compiled {[len(l["questions"]) for l in fixture["data"]["candidate_course"]["lessons"]]} actual question trajectories, {len(compiler.resources)} source resources; v1 preserved')
