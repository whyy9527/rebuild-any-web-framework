"""Compile actual audio-pair ordering and public played files; not a replacement lesson."""
from pathlib import Path
import json,hashlib,re
BASE=Path(__file__).resolve().parent;EV=BASE/'evidence/english-next-node-v1'
r=json.loads((EV/'listen-match8.json').read_text());assert not r['failure'] and len(r['rows'])==4
assert '- text: "3"' in r['before'].split('- heading')[0]
assert '- text: "2"' in r['rows'][0]['wrong_feedback'].split('- heading')[0]
resources=[];pairs=[]
for row in r['rows']:
 assert len(row['played_audio'])==1
 url=row['played_audio'][0];assert url.startswith('https://d1vq87e9lcf771.cloudfront.net/') and '?' not in url
 name='en-speech-'+hashlib.sha256(url.encode()).hexdigest()[:20]+'.mp3'
 resources.append(dict(url=url,kind='speech',name=name[:-4],source_file=name))
 pairs.append(dict(id='p'+str(row['left_index']),left=str(row['left_index']+1),right=row['translation'],audioResource=name))
q=dict(id='en-zh-node2-match8',kind='matching',sourceType='listenMatch',prompt='选择配对',pairs=pairs,
 rightOrder=[next(p['id'] for p in pairs if p['right']==text) for text in r['right_text']],
 correctFeedback=re.search(r'heading "([^"]+)" \[level=2\]',r['feedback']).group(1),explanation='')
fixture=dict(data={'candidate_course':dict(id='english-node2-pairing-probe',title='提供或接受饮料',speechLanguage='en',interfaceLanguage='zh',lessons=[dict(id='pairing-probe',title='听音配对验证',questions=[q])],pathNodes=[dict(kind='star',lessonIDs=['pairing-probe'],lessonCount=4)])},provenance=dict(source='Actual source audio matching, current played URLs and observed wrong-pair heart decrement',evidence=['projects/duolingo-web/evidence/english-next-node-v1/listen-match8.json'],scope='One isolated component; full node-two lesson remains pending',unknown='Wrong-pair animation timing, other review trajectories, acoustic equality and full-state layout fidelity pending'))
(BASE/'fixture-english-pairing-probe.json').write_text(json.dumps(fixture,ensure_ascii=False,indent=2)+'\n')
(BASE/'reference-assets-english-pairing-probe.json').write_text(json.dumps(resources,indent=2)+'\n')
requirements=[];state=q['id'];evidence=fixture['provenance']['evidence']
def add(kind,suffix,st=state,**fields):requirements.append(dict(id=state+'-'+suffix,state=st,kind=kind,evidence=evidence,**fields))
add('accessible_text','heading',text=q['prompt'])
for i,rect in enumerate(r['left_rects']):
 add('element_geometry',f'left-{i}',element='pair-left-p'+str(i),rect=[rect[k] for k in ['x','y','width','height']],tolerance_points=0)
for i,rect in enumerate(r['right_rects']):
 add('element_geometry',f'right-{i}',element='pair-right-'+q['rightOrder'][i],rect=[rect[k] for k in ['x','y','width','height']],tolerance_points=0)
for field in ['heart_decremented_once','unmatched_remains_available','wrong_pair_marked_incorrect']:
 add('interaction_boolean',field,st=state+'-wrong',field=field,expected=True)
add('interaction_boolean','matched-disabled',st=state+'-paired-first',field='matched_pair_disabled',expected=True)
add('accessible_text','feedback',st=state+'-feedback',text=q['correctFeedback'])
for category in ['visual','actual-audio','wrong-animation','late-review']:
 add('pending',category,description='Source/candidate '+category+' equality still unverified')
contract=dict(revision='audio-pairing-component-v1',scope='Source-observed pairing checks; not full product acceptance',requirements=requirements)
(BASE/'frontend-english-pairing-probe.json').write_text(json.dumps(contract,ensure_ascii=False,indent=2)+'\n')
previous=json.loads((BASE/'frontend-english-v7.json').read_text());previous.update(revision='actual-en-zh-frontends-v8',scope='Preserves v7 and adds observed audio pairing penalty, ordering and control geometry',requirements=previous['requirements']+requirements)
(BASE/'frontend-english-v8.json').write_text(json.dumps(previous,ensure_ascii=False,indent=2)+'\n')
print('Source pairing fixture and contract frozen; product requirements',len(previous['requirements']))
