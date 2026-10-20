"""Correct source-copy sampling in a new revision; retain original failed contracts.

AX serialization quotes are not displayed glyphs. Animated score containers
expose all clipped digits, so their strings cannot specify rendered copy.
"""
import copy
import json
from pathlib import Path
BASE=Path(__file__).resolve().parent
SOURCE=BASE/'evidence/english-sixth-v1'
EV=BASE/'evidence/english-sixth-native-v1'
def read(p):return json.loads(p.read_text())
def write(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
def decode_label(s):
    if s.startswith('"') and s.endswith('"'):
        value=json.loads(s)
        assert isinstance(value,str)
        return value
    return s
contract=read(BASE/'frontend-english-sixth.json');observed=read(SOURCE/'source-observed.json');changes=[]
complete='en-zh-l6-complete'
for state in observed['states'].values():state['accessible_text']=sorted(set(map(decode_label,state['accessible_text'])))
rows=[]
for r in contract['requirements']:
    if r['state']==complete and r['kind']=='accessible_text':
        changes.append(dict(id=r['id'],before=r['text'],reason='Grouped/animated AX node is not an atomic rendered label; replaced using actual completion PNG'))
        continue
    if r['kind']=='accessible_text':
        decoded=decode_label(r['text'])
        if decoded!=r['text']:changes.append(dict(id=r['id'],before=r['text'],after=decoded,reason='Decode actual AX YAML quoted scalar; no visible quote glyph'))
        r['text']=decoded
    rows.append(r)
visual=read(SOURCE/'completion-visual.json')
labels=[visual['title'],visual['body'],'总经验',str(visual['experience']),'超级棒',str(visual['accuracy'])+'%','回顾本单元','继续']
refs=[str((SOURCE/n).relative_to(BASE.parent.parent)) for n in ['completion-visual.json','english-sixth-complete.png']]
for i,label in enumerate(labels):rows.append(dict(id=complete+'-rendered-copy-'+str(i),state=complete,kind='accessible_text',text=label,evidence=refs))
observed['states'][complete]['accessible_text']=labels
observed['kind']='actual-source-AX-with-explicit-manual-completion-PNG-copy'
observed['limitations']=['Completion labels are transcribed from the retained actual PNG, not automated AX digit selection or scoring inference; pixel and audio equivalence remain pending']
new=dict(revision='actual-sixth-continuation-copy-v2',requirements=rows,supersedes='frontend-english-sixth.json',sampling_correction='Serialization/animated-parent sampling corrected; original failed source/candidate results retained')
write(BASE/'frontend-english-sixth-v2.json',new);write(EV/'source-v2-observed.json',observed)
prior=read(BASE/'frontend-english-v10.json');prior['revision']='english-v12-sixth-visible-copy';prior['requirements']+=rows
write(BASE/'frontend-english-v12.json',prior)
write(EV/'copy-sampling-revision.json',dict(changes=changes,completion_copy_source=refs,original_contract_retained=True,scope='Sampling repair, not weakened visual/audio acceptance; all 50 pending requirements retained'))
print(len(rows),'sixth requirements;',len(changes),'sampling corrections;',len(prior['requirements']),'product requirements')
