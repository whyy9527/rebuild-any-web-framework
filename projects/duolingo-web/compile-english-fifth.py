"""Compile the observed fifth trajectory, preserving the deferred, ungraded speech state.

The API's speech rows 9/13 are not the actual UI. No general adaptation/reward rule
is inferred: this fixture is the captured decline-speech, cold-error, pairing-error path.
"""
import importlib.util
import json
import re
from pathlib import Path

BASE = Path(__file__).resolve().parent
EV = BASE / 'evidence/english-next-node-v1'
spec = importlib.util.spec_from_file_location('english_compiler', BASE/'compile-english-course.py')
compiler = importlib.util.module_from_spec(spec)
spec.loader.exec_module(compiler)
def read(name): return json.loads((EV/name).read_text())
def write(name, value): (BASE/name).write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n')
def heading(snapshot, level):
    return re.search(r'heading "([^"\n]+)" \[level='+str(level)+r'\]', snapshot).group(1)

fixture = json.loads((BASE/'fixture-reference-en-zh-v5.json').read_text())
for resource in json.loads((BASE/'reference-assets-en-zh-v5.json').read_text()):
    compiler.resources[resource['name']] = resource
source = read('session.json')['session']
trajectory = read('trajectory.json')
questions = []
for state in trajectory['observed_states']:
    if state['kind'] == 'speaking_deferred': continue
    i = state['api_index']
    evidence = read(state['evidence'])
    sid = 'en-zh-l5-'+state['id']
    if i is not None and state['kind'] == 'translate':
        row = evidence['observed'][state['row_index']]
        assert row['index'] == i and row['feedback']
        q = compiler.compile_questions(dict(source, challenges=[source['challenges'][i]]), {i: row}, {}, prefix='en-zh-l5-q')[0]
    elif i is None:
        row = evidence['rows'][state['row_index']] if 'rows' in evidence else evidence
        bank = row['bank']; answer = row.get('actions', ['茶'])
        assert '正确答案：' not in row['feedback']
        words, ids = compiler.compile_word_bank([dict(text=t) for t in bank], bank, answer)
        q = dict(id=sid, kind='word_tiles', sourceType='translate',
                 prompt=heading(row['before'], 1), hint=state['prompt'], sourceLanguage='en',
                 words=words, answer_words=ids, explanation='')
    elif state['kind'] in ['listenComplete', 'completeReverseTranslation']:
        c = source['challenges'][i]['content']; tokens = c['displayTokens']
        blank = [j for j, t in enumerate(tokens) if t['isBlank']]
        assert len(blank) == 1
        answer = tokens[blank[0]]['text']
        accepted = read(state['review_evidence']) if i == 7 else evidence
        assert accepted.get('input', state.get('accepted_input', '')) .lower() == answer.lower()
        row = accepted
        q = dict(id=sid, kind='text_entry', sourceType=c['type'], prompt=heading(evidence['before'], 1),
                 answer=answer, hint=c.get('prompt'),
                 completionPrefix=''.join(t['text'] for t in tokens[:blank[0]]),
                 completionSuffix=''.join(t['text'] for t in tokens[blank[0]+1:]),
                 explanation='意思是： '+c['solutionTranslation'] if c.get('solutionTranslation') else '')
        for key, field in [('tts', 'audioResource'), ('slowTts', 'slowAudioResource')]:
            if c.get(key): q[field] = compiler.resource(c[key], 'speech')
    elif state['kind'] == 'listenMatch':
        if i == 2:
            bindings = evidence['bindings']
            row = read('replay-01.json')['observed'][2]
            right = re.findall(r'- button "[5-8] ([^"\n]+)"', row['before'])
            # Acceptance only from retained source PNG; no fabricated playback receipt.
            assert (EV/state['acceptance_evidence']).is_file()
        else:
            assert evidence['failure'] is None
            bindings = [dict(left_index=r['left_index'], translation=r['translation'], tts=r['played_audio'][0]) for r in evidence['rows']]
            right = evidence['right_text']; row = evidence
        pairs = [dict(id='p'+str(b['left_index']), left=str(b['left_index']+1), right=b['translation'],
                      audioResource=compiler.resource(b['tts'], 'speech')) for b in bindings]
        q = dict(id=sid, kind='matching', sourceType='listenMatch', prompt='选择配对', pairs=pairs,
                 rightOrder=[next(p['id'] for p in pairs if p['right'] == t) for t in right], explanation='')
        if i == 2:
            # Visually inspected actual saved source PNG; AX feedback was lost
            # in the retained transition failure, not recreated as an observation.
            q['correctFeedback'] = '真厉害！'
    else: raise ValueError(state)
    if row.get('feedback'): q['correctFeedback'] = heading(row['feedback'], 2)
    # Only captured/API-bound audio; adaptive media identity remains unknown.
    questions.append(q)

assert len(questions) == trajectory['graded_question_count'] == 15
speech = source['challenges'][6]['content']
lesson = dict(id='lesson-5', title='第 1/4 单元', questions=questions,
    deferredSpeech=[dict(id='en-zh-l5-speech6', beforeQuestionID='en-zh-l5-adaptive7',
        title='朗读下面的句子', phrase=speech['prompt'], audioResource=compiler.resource(speech['tts'], 'speech'),
        declineLabel='现在不做口语题', closedTitle='麦克风已关闭', closedBody='将在 15 分钟后恢复')],
    reviewInterlude=dict(id='en-zh-l5-review-intro', afterQuestionID='en-zh-l5-q14',
                        text='一起来复习一下之前你不太熟练的部分吧！'),
    settlement=[
        dict(id='en-zh-l5-complete', kind='result', title='听力练习完成！', continueLabel='继续', secondaryLabel='回顾本单元', experience=13, observedAccuracy=94, observedMistakes=2),
        dict(id='en-zh-l5-daily-quests', kind='daily_quests', title='所有每日特别任务都完成啦！', body='获取 30 经验', continueLabel='继续', secondaryLabel='回顾本单元'),
        dict(id='en-zh-l5-gems', kind='gems', title='你赚取了 5 颗宝石！', body='完成每日目标真不容易哦！', continueLabel='继续', secondaryLabel='回顾本单元'),
        dict(id='en-zh-l5-profile', kind='profile', title='来创建你的个人档案吧！', body='创建档案就能保存学习进度，随时都可以继续免费学习后续内容。', continueLabel='稍后再说', secondaryLabel='创建档案')])
# Title is taken from the actual completion AX, never inferred from the API type.
completion = read('complete.json')
snapshot = completion['snapshot']
assert '你莫不是特工？ 本单元中，你完成了 4 项听力挑战' in snapshot
lesson['settlement'][0].update(title='你莫不是特工？', body='本单元中，你完成了 4 项听力挑战', accuracyLabel='棒棒哒！')
course = fixture['data']['candidate_course']; course['lessons'].append(lesson)
course['pathNodes'][1]['lessonIDs'] = ['lesson-5']; course['pathNodes'][1]['lessonCount'] = 4
course['home']['progressSnapshots'].append(dict(course['home']['progressSnapshots'][-1], completedLessons=5, gems=510, questTarget=30, questProgress=30, leagueCountdown='16 小时'))
fixture['provenance']['source'] += '; fifth actual 15 graded questions plus one ungraded deferred speech stage; typed review and four settlement pages'
fixture['provenance']['evidence'] += [str((EV/n).relative_to(BASE.parent.parent)) for n in sorted(set(['trajectory.json', 'session.json']+[s['evidence'] for s in trajectory['observed_states']]+['complete.json', 'reference-lesson5-complete-settled.png', 'after-complete-settled.json', 'five-gems.json', 'home-after-five.json']))]
fixture['provenance']['unknown'] = 'Recording/recognition branch, adaptation/reward/accuracy/timer formulas, remaining second-node lessons, secondary actions, original graphics/animation and acoustic equality remain incomplete. Fifth path is the captured deferred-speech trajectory, not all possible source paths.'
write('fixture-reference-en-zh-v6.json', fixture)
write('reference-assets-en-zh-v6.json', list(compiler.resources.values()))
print('Compiled graded counts', [len(l['questions']) for l in course['lessons']], 'plus one ungraded speech stage;', len(compiler.resources), 'resources')
