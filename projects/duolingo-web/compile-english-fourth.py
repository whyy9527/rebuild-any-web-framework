"""Append UI-confirmed fourth challenge; keep frozen earlier fixtures unchanged."""
import importlib.util
import json
from pathlib import Path
BASE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('english_third',BASE/'compile-english-third.py')
third=importlib.util.module_from_spec(spec);spec.loader.exec_module(third)
compiler=third.compiler
EV=BASE/'evidence/english-fourth-v1'
def read(name):return json.loads((EV/name).read_text())
def build_fourth_fixture():
    fixture=third.build_third_fixture();source=read('session.json')['session'];rows={}
    for name in ['replay-02.json','replay-03.json']:
        for row in read(name)['observed']:
            if row.get('feedback'):rows[row['index']]=row
    assert set(rows)==set(range(12))
    # Source screenshot and actual DOM both show Coffee or tea?; API omits it.
    dialogue=rows[10]
    assert 'Coffee\n or\n tea\n?' in dialogue['identity']['actual']['text']
    clip=dialogue['media_before'][-1]['src']
    assert clip.startswith('https://d1vq87e9lcf771.cloudfront.net/linen/')
    questions=compiler.compile_questions(source,rows,{'10':{'prompt':'Coffee or tea?','observed_speech':clip}},prefix='en-zh-l4-q')
    for row in rows.values():
        q=questions[row['index']]
        if '挑战题' in row['before']:q['indicator']='挑战题'
        elif '错题重练' in row['before']:q['indicator']='错题重练'
    course=fixture['data']['candidate_course']
    course['lessons'].append({'id':'lesson-4','title':'Lesson 4 of 4','questions':questions,
        'entry':{'id':'en-zh-l4-entry','title':'来复习一下这个等级，完成后有惊喜哦！','startLabel':'开始挑战 +20 经验','declineLabel':'下次再说'},
        'initialInterlude':{'id':'en-zh-l4-review-intro','afterQuestionID':'','text':'一起来复习一下之前你不太熟练的部分吧！'},
        'interludes':[{'id':'en-zh-l4-hard-intro','afterQuestionID':'en-zh-l4-q4','text':'来试试这个等级里最有挑战性的练习吧！'}]})
    course['pathNodes'][0]['lessonIDs'].append('lesson-4')
    bronze=read('bronze-card.json')['images'][0]['src']
    bronzeResource=compiler.resource(bronze,'home')
    # Frozen source presentation snapshots, not an inferred per-lesson reward rule.
    course['home']['progressSnapshots']=[{'completedLessons':i,'gems':505} for i in [1,2]] + [
        {'completedLessons':3,'gems':505,'leagueTitle':'青铜等级','leagueLink':'查看排行榜',
         'leagueMessage':'这周的排行榜挑战赛即将开始！','leagueCountdown':'18 小时','leagueResource':bronzeResource}]
    course['home']['progressSnapshots'].append(dict(course['home']['progressSnapshots'][-1],completedLessons=4,leagueCountdown='17 小时'))
    fixture['provenance']['evidence'] += [str((EV/n).relative_to(BASE.parent.parent)) for n in ['session.json','replay-02.json','replay-03.json','reference-fourth-question-10-before.png','reloaded-entry.json','review-intro.json','post-third-profile.json','bronze-card.json']]
    fixture['provenance']['source']+='; fourth actual 12-question challenge, observed entry and two introductions; home presentation snapshots from actual source'
    fixture['provenance']['unknown']='Fourth completion chain, full-body/animated characters, actual output audio equivalence, second path node and remaining navigation not implemented; reward/league countdown generalization unknown. Frozen home snapshots are not server reward rules.'
    return fixture
if __name__=='__main__':
    fixture=build_fourth_fixture()
    (BASE/'fixture-reference-en-zh-v4.json').write_text(json.dumps(fixture,ensure_ascii=False,indent=2)+'\n')
    (BASE/'reference-assets-en-zh-v4.json').write_text(json.dumps(list(compiler.resources.values()),ensure_ascii=False,indent=2)+'\n')
    print('Compiled question counts',[len(l['questions']) for l in fixture['data']['candidate_course']['lessons']], 'resources',len(compiler.resources))
