"""Append the actual third-lesson UI trajectory to v77; preserve unknown branches."""
import argparse,json
from PIL import Image
from pathlib import Path
from capabilities.rebuild.discovery import frontier
p=argparse.ArgumentParser();p.add_argument('--out-dir',required=True);O=Path(p.parse_args().out_dir);O.mkdir(parents=True,exist_ok=False)
B=Path('projects/duolingo-web');E=B/'evidence/english-unit12-lesson3-v1';read=lambda p:json.loads(p.read_text())
c=read(B/'frontend-english-v77.json');prior=c['requirements'][:];h=read(B/'evidence/english-streak-followup-v1/history.json');aliases={};image_audit=[];course=read(B/'fixture-reference-en-zh-unit12-lesson3-v1.json')['data']['candidate_course']['lessons'][0];qs={int(q['id'].split('q')[-1]):q for q in course['questions']}
files=[f'q{i}-{phase}' for i in range(1,16) for phase in ['before','feedback'] if (E/'source'/f'q{i}-{phase}.json').exists()]+['q2-closed','review-introduction','review-q0-before','review-q0-feedback','settlement-current','settlement-review','review-table-expanded','after-result','after-heart-reward','home-after','fourth-lesson-popup-view']
for name in files:
 path=E/'source'/(name+'.json');s=read(path);assert s['capture_state_consistent'];state='unit12-l3-'+name;ev=[str(path),str(path.with_suffix('.png'))];aliases[state]={}
 for a in s['actions']:a['operations']=['click'] if a['role'] in ['button','radio','link'] else ['hover','click','Enter']
 h['states'].append(dict(id=state,evidence=str(path),actions=s['actions']))
 def add(suffix,kind,**kw):c['requirements'].append(dict(id=state+'-'+suffix,state=state,kind=kind,evidence=ev,**kw))
 intended=dict(reference_image=ev[1],pixels=[1200,732],reference_capture=dict(s['capture_geometry'],state_consistent=True))
 actual=list(Image.open(path.with_suffix('.png')).size);expected=[round(v*s['capture_geometry']['backing_scale']) for v in s['capture_geometry']['window_points']]
 image_audit.append(dict(state=state,actual_png_pixels=actual,independently_measured_expected_pixels=expected,usable=actual==expected))
 if actual==expected:add('whole','image_pixels',**intended)
 else:add('whole','pending',description='Image comparison not executed: source PNG cropped by browser surface; actual '+str(actual)+' differs from independently measured '+str(expected)+'. Preserve original image assertion and recollect exact source state.',unavailable_reference_requirement=dict(kind='image_pixels',**intended))
 for i,t in enumerate(dict.fromkeys(x['text'] for x in s['text_runs'])):add('text-'+str(i),'accessible_text',text=t)
 q=qs.get(int(name.split('-')[0][1:])) if name.startswith('q') and name.split('-')[0][1:].isdigit() else qs[0] if name.startswith('review-q0') else None
 for i,a in enumerate(s['actions']):
  key=state+'-action-'+str(i);native={'player-next':'continue','player-skip':'skip','quit-button':'practice-quit','player-check':'check'}.get(a.get('test'))
  if a['name']=='检查':native='check'
  if q:
   for w in q.get('words',[]):
    if a['name']==w['text']:native=('selected-word-' if a['rect'][1]<480 and '-feedback' in name else 'word-bank-')+w['id']
   for o in q.get('options',[]):
    if a['name'].split('\n')[-1]==o['text']:native='option-'+o['id']
   for pair in q.get('pairs',[]):
    if a['name'].split('\n')[-1]==pair['left']:native='pair-left-'+pair['id']
    if a['name'].split('\n')[-1]==pair['right']:native='pair-right-'+pair['id']
  if name in ['settlement-current','after-result','after-heart-reward']:
   native={'继续':'settlement-continue','稍后再说':'settlement-continue','回顾本单元':'settlement-secondary'}.get(a['name'],native)
  if native:aliases[state][key]=native
  add('geometry-'+str(i),'element_geometry',element=key,rect=a['rect'],tolerance_points=0)
  if a['role']:add('role-'+str(i),'element_role',element=key,role=a['role'])
  add('enabled-'+str(i),'element_boolean',element=key,field='enabled',expected=a['enabled'])
 add('audio','pending',description='Source call/playing resources are recorded; aligned source acoustic equality is unavailable. Actual native owned-output comparison is separate.')
 if 'q5-' in name or 'q11-' in name:add('table-style','pending',description='Three-row source TABLE, purple emphasis, dotted token underline, border and row geometry must match; content alone cannot pass.')
# Only actions actually executed get edges. Composite submissions are retained as
# sequential receipts, not fabricated successful probes of other input modes.
states={s['id']:s for s in h['states']}
for i in range(3,16):
 start='unit12-l3-'+f'q{i}-feedback';end='unit12-l3-'+(f'q{i+1}-before' if i<15 else 'review-introduction');receipt=E/'source'/f'q{i}-next.raw.txt'
 if start not in states or end not in states or not receipt.exists():continue
 action=next(a for a in states[start]['actions'] if a['name']=='继续')
 h['transitions'].append(dict(**{'from':start,'to':end},action=action['id'],operation='click',outcome='observed',evidence=str(receipt)))
start='unit12-l3-home-after';end='unit12-l3-fourth-lesson-popup-view'
action=next(a for a in states[start]['actions'] if a['name']=='Lesson 4 of 6')
h['transitions'].append(dict(**{'from':start,'to':end},action=action['id'],operation='click',outcome='observed',evidence=str(E/'source/fourth-lesson-popup.raw.txt')))
c.update(revision='english-v78',parent_revision='english-v77',changes=['Executed third lesson discovers patternTapComplete table variants, text-match sound sequence, skip/review and heart reward settlement','Old requirements unchanged; unknown characters, source acoustic output and later locked branches remain pending'])
assert c['requirements'][:len(prior)]==prior
assert len({r['id'] for r in c['requirements']})==len(c['requirements'])
for name,d in [('contract.json',c),('reference-image-audit.json',image_audit),('aliases.json',aliases),('history.json',h),('frontier.json',frontier(Path.cwd(),h))]:(O/name).write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(dict(requirements=len(c['requirements']),states=len(h['states']),edges=len(h['transitions']))))
