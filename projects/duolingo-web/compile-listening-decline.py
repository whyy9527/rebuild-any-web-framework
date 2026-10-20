"""Freeze the executed listening-decline prefix; no inferred future adaptation."""
import importlib.util
import json
import re
from pathlib import Path

BASE = Path(__file__).resolve().parent
EV = BASE / 'evidence/english-listening-decline-v1'
def read(name): return json.loads((EV / name).read_text())
def heading(snapshot, level): return re.findall(r'- heading "([^"\n]+)" \[level='+str(level)+r'\]', snapshot)[0]
def write(name, value): (BASE/name).write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n')
spec = importlib.util.spec_from_file_location('english', BASE/'compile-english-course.py')
compiler = importlib.util.module_from_spec(spec); spec.loader.exec_module(compiler)
source = json.loads((BASE/'evidence/english-character-render-v1/sixth-session.json').read_text())['session']
before = read('english-sixth-listening-before.json')
declined = read('english-sixth-listening-declined.json')
adaptive = read('q3-answer.json')
fill = read('english-sixth-after-coffee-milk.json')
accepted = read('english-sixth-milk-fill-accepted.json')
assert not adaptive['rejected'] and adaptive['prompts'] == ['coffee with milk']
assert '连对 4 题' in accepted['snapshot'] and ': milk' in accepted['snapshot']
assert '听力题已跳过' in declined['snapshot'] and '将在 15 分钟后恢复' in declined['snapshot']
right = re.findall(r'- button "[5-8] ([^"\n]+)"', before['snapshot'])
pairs = [dict(id='p'+str(i), left=str(i+1), right=p['translation'], audioResource=compiler.resource(p['tts'], 'speech')) for i,p in enumerate(source['challenges'][2]['content']['pairs'])]
assert set(right) == {p['right'] for p in pairs}
matching = dict(id='en-zh-decline-match', kind='matching', sourceType='listenMatch', prompt='选择配对',
                pairs=pairs, rightOrder=[next(p['id'] for p in pairs if p['right']==t) for t in right], explanation='',
                listeningDecline=dict(label='现在不做听力题', title='听力题已跳过', body='将在 15 分钟后恢复'))
words, answer = compiler.compile_word_bank([dict(text=t) for t in adaptive['choices']], adaptive['choices'], [a['word'] for a in adaptive['clicks']])
translation = dict(id='en-zh-decline-adaptive', kind='word_tiles', sourceType='translate', prompt=heading(adaptive['before'],1),
                   hint='coffee with milk', words=words, answer_words=answer, explanation='', sourceLanguage='en',
                   characterResource='en-image-aea31ef9b72326cf846e', correctFeedback=heading(adaptive['feedback'],2))
# This character is bound to the actual exported Bea RIVE buffer, not API row3's LIN.
c=source['challenges'][3]['content'];tokens=c['displayTokens'];blank=[i for i,t in enumerate(tokens) if t['isBlank']]
assert len(blank)==1 and tokens[blank[0]]['text']=='milk'
typed=dict(id='en-zh-decline-fill',kind='text_entry',sourceType='completeReverseTranslation',prompt=heading(fill['snapshot'],1),
           hint=c['prompt'],answer='milk',completionPrefix=''.join(t['text'] for t in tokens[:blank[0]]),
           completionSuffix=''.join(t['text'] for t in tokens[blank[0]+1:]),explanation='',correctFeedback=heading(accepted['snapshot'],2))
refs=['projects/duolingo-web/evidence/english-listening-decline-v1/'+n for n in ['english-sixth-listening-before.json','english-sixth-listening-declined.json','q3-answer.json','english-sixth-after-coffee-milk.json','english-sixth-milk-fill-accepted.json']]
fixture=dict(data=dict(candidate_course=dict(id='listening-decline-observed-prefix',title='提供或接受饮料',speechLanguage='en',interfaceLanguage='zh',
    lessons=[dict(id='decline-prefix',title='听力暂缓现场',questions=[matching,translation,typed])],pathNodes=[dict(kind='star',lessonIDs=['decline-prefix'],lessonCount=4)])),
    provenance=dict(evidence=refs,scope='Executed sixth-lesson decline prefix, not completed lesson; observer stops on typed feedback',
    unknown=['Audio pair left-order binding is API-only; not graded or asserted in this decline probe',
             'Adaptive prompt audio identity, later replacements, timer expiry, final score and persistence',
             'Source progress begins after two correct answers; probe begins at decline state, progress geometry not comparable']))
write('fixture-listening-decline.json',fixture)
write('reference-assets-listening-decline.json',list(compiler.resources.values()))
requirements=[]
def text(state,suffix,value): requirements.append(dict(id=state+'-'+suffix,state=state,kind='accessible_text',text=value,evidence=refs))
text(matching['id'],'heading','选择配对');text(matching['id'],'action','现在不做听力题')
closed=matching['id']+'-declined'
text(closed,'title','听力题已跳过');text(closed,'body','将在 15 分钟后恢复');text(closed,'continue','继续')
for suffix,label in [('too-easy','太简单'),('too-hard','太难'),('report','报错')]: text(closed,suffix,label)
for field in ['hearts_unchanged','all_pairs_disabled']:
    requirements.append(dict(id=closed+'-'+field,state=closed,kind='interaction_boolean',field=field,expected=True,evidence=refs))
for q in [translation,typed]:
    text(q['id'],'heading',q['prompt']);text(q['id'],'hint',q['hint']);text(q['id']+'-feedback','accepted',q['correctFeedback'])
for gap in ['same-state-pixels','pair-playback-binding','adaptive-audio','timer-expiry','later-adaptive-sequence','secondary-actions']:
    requirements.append(dict(id='decline-'+gap,state=closed,kind='pending',description=gap+' remains unverified',evidence=refs))
write('frontend-listening-decline.json',dict(revision='observed-listening-decline-v1',requirements=requirements))
def ax_text(snapshot):
    # Read independent source AX facts, not the contract's expected strings.
    return sorted(set(re.findall(r'"([^"\n]+)"',snapshot)+re.findall(r'- text: ([^\n]+)',snapshot)+re.findall(r'- generic: ([^\n]+)',snapshot)))
disabled = re.findall(r'- button "(?:[1-4]|[5-8] [^"\n]+)" \[disabled\]', declined['snapshot'])
# Read the player header only: pair buttons also contain numeric text.
def source_hearts(snapshot): return re.findall(r'- (?:generic|text): "(\d+)"',snapshot.split('- heading ')[0])
states={matching['id']:dict(accessible_text=ax_text(before['snapshot'])),
        closed:dict(accessible_text=ax_text(declined['snapshot']),interactions=dict(
            hearts_unchanged=source_hearts(before['snapshot'])==source_hearts(declined['snapshot'])==['2'],all_pairs_disabled=len(disabled)==8)),
        translation['id']:dict(accessible_text=ax_text(adaptive['before'])+adaptive['prompts']),
        translation['id']+'-feedback':dict(accessible_text=ax_text(adaptive['feedback'])),
        typed['id']:dict(accessible_text=ax_text(fill['snapshot'])+[line for node in fill['visible'] for line in node['text'].splitlines() if line]),
        typed['id']+'-feedback':dict(accessible_text=ax_text(accepted['snapshot']))}
(EV/'source-observed.json').write_text(json.dumps(dict(kind='actual-source-AX-and-visible-DOM-facts',states=states),ensure_ascii=False,indent=2)+'\n')
print('Compiled 3-state observed prefix and',len(requirements),'requirements; no inferred full lesson')
