"""Freeze observed fourth-lesson frontend states before candidate implementation."""
import argparse,json
from pathlib import Path
from capabilities.rebuild.discovery import frontier
from PIL import Image
B=Path('projects/duolingo-web');E=B/'evidence/english-unit12-lesson4-v1'
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out-dir',required=True);O=Path(p.parse_args().out_dir);O.mkdir(parents=True,exist_ok=False)
read=lambda p:json.loads(p.read_text())
c=read(B/'frontend-english-v78.json');prior=c['requirements'][:];h=read(B/'evidence/english-unit12-lesson3-v1/history.json');audit=[]
for path in sorted((E/'source').glob('*.json')):
 s=read(path)
 if 'text_runs' not in s:continue
 state='unit12-l4-'+path.stem;ev=[str(path),str(path.with_suffix('.png'))]
 def add(suffix,kind,**kw):c['requirements'].append(dict(id=state+'-'+suffix,state=state,kind=kind,evidence=ev,**kw))
 geometry=s['capture_geometry'];actual=list(Image.open(path.with_suffix('.png')).size);expected=[round(x*geometry['backing_scale']) for x in geometry['window_points']]
 viewport_verified=s.get('capture_viewport_consistent') is True
 css=s.get('capture_layout_metrics',{}).get('cssVisualViewport',{})
 clip=s.get('capture_clip')
 clip_verified=clip is not None and clip['x']==css.get('pageX') and clip['y']==css.get('pageY') or css.get('pageX')==0 and css.get('pageY')==0
 usable=actual==expected and s['capture_state_consistent'] and viewport_verified and clip_verified
 audit.append(dict(state=state,actual=actual,expected=expected,viewport_verified=viewport_verified,clip_verified=clip_verified,usable=usable))
 requirement=dict(reference_image=ev[1],pixels=geometry['window_points'],reference_capture=dict(geometry,state_consistent=usable))
 if usable:add('whole','image_pixels',**requirement)
 else:add('whole','pending',description='Source viewport identity missing, changed, or clip ignores measured document scroll; preserve unavailable original image requirement.',unavailable_reference_requirement=dict(kind='image_pixels',**requirement))
 for i,t in enumerate(dict.fromkeys(x['text'] for x in s['text_runs'])):add('text-'+str(i),'accessible_text',text=t)
 for i,a in enumerate(s['actions']):
  element=state+'-action-'+str(i)
  add('geometry-'+str(i),'element_geometry',element=element,rect=a['rect'],tolerance_points=0)
  if a['role']:add('role-'+str(i),'element_role',element=element,role=a['role'])
  add('enabled-'+str(i),'element_boolean',element=element,field='enabled',expected=a['enabled'])
 # Raw text CSS, original art, hit/clipping inventory remain attached. Whole
 # pixels are strict; text/geometry never substitute for artwork or audio.
 for i,t in enumerate(x for x in s['visible'] if x['tag']=='TEXTAREA'):
  element=state+'-textarea-'+str(i)
  add('textarea-geometry-'+str(i),'element_geometry',element=element,rect=t['rect'],tolerance_points=0)
  add('textarea-enabled-'+str(i),'element_boolean',element=element,field='enabled',expected=t['enabled'])
  add('textarea-role-'+str(i),'element_role',element=element,role='textbox')
 if path.stem.startswith('q14-keyboard'):add('textbox-inventory','pending',description='Textarea geometry exists in visible evidence and is compared separately; original canonical action inventory omitted textarea and did not capture value. Executed fill receipt retained; reobserve with corrected collector before closing its exploration frontier.')
 add('audio','pending',description='Original call/playing source and volume logged; actual aligned source acoustic output not yet captured.')
 actions=[]
 for a in s['actions']:
  action=dict(a,operations=['click'] if a['role'] in ['button','radio','link'] else ['fill','click','Enter'] if a['role']=='textbox' else ['hover','click','Enter']);actions.append(action)
 h['states'].append(dict(id=state,evidence=str(path),actions=actions))
# Real continued receipts only; interlude and microphone decline are explicit states.
states={s['id']:s for s in h['states']}
for i in range(17):
 start=f'unit12-l4-q{i}-feedback';end=f'unit12-l4-q{i+1}-before'
 receipt=E/'source'/f'q{i}-next.raw.txt'
 if i==9:end='unit12-l4-q10-before'
 if i==14:end='unit12-l4-hard-introduction'
 if start not in states or end not in states or not receipt.exists():continue
 action=next((a for a in states[start]['actions'] if a['name']=='继续'),None)
 if action:h['transitions'].append(dict(**{'from':start,'to':end},action=action['id'],operation='click',outcome='observed',evidence=str(receipt)))
# Executed input-mode and settlement transitions are separate from tile answers.
for start,end,label,operation,receipt in [
 ('q14-before','q14-keyboard','使用键盘','click','q14-keyboard-open'),
 ('q14-keyboard-filled','q14-feedback','检查','click','q14-answer'),
 ('q15-before','q15-wordbank','使用词库','click','q15-wordbank-open'),
 ('hard-introduction','q15-before','继续','click','hard-next'),
 ('settlement-current','settlement-review','回顾本单元','click','settlement-review-open'),
 ('after-result','after-achievement','继续','click','achievement-next'),
 ('after-achievement','home-after','稍后再说','click','profile-next'),
 ('home-after','radio-after-fourth-view','电台','click','radio-after-fourth')]:
 start,end='unit12-l4-'+start,'unit12-l4-'+end
 action=next(a for a in states[start]['actions'] if a['name']==label)
 h['transitions'].append(dict(**{'from':start,'to':end},action=action['id'],operation=operation,outcome='observed',evidence=str(E/'source'/(receipt+'.raw.txt'))))
c.update(revision='english-v79',parent_revision='english-v78',changes=['Fourth lesson actual select/translate/assist/pattern/listening and keyboard preference trajectory','Achievement upgrade between result and profile; home155gems5heartsLesson5of6','Measured source viewport and capture mutation gates; earlier legacy viewport observations stay pending'])
assert c['requirements'][:len(prior)]==prior
assert len({r['id'] for r in c['requirements']})==len(c['requirements'])
for name,data in [('contract.json',c),('history.json',h),('reference-image-audit.json',audit),('frontier.json',frontier(Path.cwd(),h))]:(O/name).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(dict(requirements=len(c['requirements']),states=len(h['states']),edges=len(h['transitions']),usable_images=sum(x['usable'] for x in audit),unavailable_images=sum(not x['usable'] for x in audit))))
