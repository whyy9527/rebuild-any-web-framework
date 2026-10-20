"""Append the actual third lesson, preserving duplicate word occurrences and API divergence."""
import importlib.util
import json
from pathlib import Path
import re

BASE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('english_second',BASE/'compile-english-second.py')
second=importlib.util.module_from_spec(spec);spec.loader.exec_module(second)
compiler=second.compiler

def build_third_fixture():
    fixture=second.build_second_fixture()
    ev=BASE/'evidence/english-third-v1'
    def read(name):return json.loads((ev/name).read_text())
    source=read('session.json')['session'];rows={}
    for name in ['replay-01.json','replay-02.json']:
        for row in read(name)['observed']:
            if row.get('feedback'):rows[row['index']]=row
    assert set(rows)==set(range(12))
    questions=compiler.compile_questions(dict(source,challenges=source['challenges'][:12]),rows,{},prefix='en-zh-l3-q')
    for i in range(12,15):
        if i==12:
            row=read('adaptive-live.json');recovery=read('adaptive-12-recovery.json')
            assert recovery['feedback_observed']=='真厉害！' and not recovery['returned_json_available']
            # Acceptance comes from the saved source PNG, not an invented AX
            # snapshot after the callback's transition failure.
            assert (ev/recovery['source']).is_file()
            prompt=read('hint-token-reading.json')['hints'][0]['parent']
            texts=re.findall(r'- button "([^"\n]+)"',row['snapshot'])
            texts=[t for t in texts if t not in ['检查','跳过','使用键盘']]
            answer=recovery['chosen_words']
        else:
            row=read(f'adaptive-{i}.json')
            assert not row['rejected'] and '继续' in row['feedback'] and '正确答案：' not in row['feedback']
            assert len(row['prompts'])==1
            prompt=row['prompts'][0];texts=row['choices'];answer=[a['word'] for a in row['clicks']]
        words,answer_ids=compiler.compile_word_bank([{'text':t} for t in texts],texts,answer)
        questions.append({'id':f'en-zh-l3-q{i}','kind':'word_tiles','sourceType':'translate',
            'prompt':'用英语写出这句话','indicator':'挑战题','hint':prompt,'sourceLanguage':'zh',
            'newWord':False,'explanation':'','words':words,'answer_words':answer_ids})
    assert len(questions)==15
    interludes=[]
    for name in ['replay-01.json','replay-02.json']:
        for row in read(name)['interludes']:
            text=re.findall(r'- text: (.+)',row['snapshot'])[-1].strip(chr(34))
            interludes.append({'id':f'en-zh-l3-interlude-{len(interludes)}','afterQuestionID':f'en-zh-l3-q{row["before_index"]-1}','text':text})
    course=fixture['data']['candidate_course']
    course['lessons'].append({'id':'lesson-3','title':'Lesson 3 of 4','questions':questions,'interludes':interludes})
    course['pathNodes'][0]['lessonIDs'].append('lesson-3')
    fixture['provenance']['source']+='; third actual lesson: 12 accepted normal questions and 3 accepted visible adaptive translations; duplicate 不要 occurrences retained'
    fixture['provenance']['evidence'] += [ev.relative_to(BASE.parent.parent).as_posix()+'/'+n for n in [
        'session.json','replay-01.json','replay-02.json','adaptive-live.json','adaptive-12-recovery.json',
        'reference-english-third-adaptive-12-feedback.png','hint-token-reading.json','adaptive-13.json','adaptive-14.json']]
    fixture['provenance']['unknown']='Fourth and later lessons, alternate trajectories and adaptive selection rules, example-button audio identity, hard-question character assets, complete settlement chain, error tutorial, animation and acoustic equivalence remain unverified'
    return fixture

if __name__=='__main__':
    fixture=build_third_fixture()
    (BASE/'fixture-reference-en-zh-v3.json').write_text(json.dumps(fixture,ensure_ascii=False,indent=2)+'\n')
    (BASE/'reference-assets-en-zh-v3.json').write_text(json.dumps(list(compiler.resources.values()),ensure_ascii=False,indent=2)+'\n')
    print('Compiled actual question counts', [len(l['questions']) for l in fixture['data']['candidate_course']['lessons']], 'resources',len(compiler.resources))
