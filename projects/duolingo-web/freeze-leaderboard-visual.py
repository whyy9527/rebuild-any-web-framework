"""Freeze actual selected/cleared status presentation; retain all v54 requirements."""
import argparse,json
from pathlib import Path
from PIL import Image
from capture_color import srgb_image
B=Path(__file__).resolve().parent;R=B.parents[1];E=B/'evidence/english-leaderboard-visual-v1';S=E/'source'
def build():
 c=json.loads((B/'frontend-english-v54.json').read_text());old=c['requirements'][:];ref={'states':{}}
 for stem,selected in [('selected-hover',True),('cleared',False)]:
  source=json.loads((S/(stem+'.json')).read_text());assert source['viewport']=={'width':1200,'height':732}
  key='leaderboard-visual-'+('selected' if selected else 'cleared');image=str((S/(stem+'.png')).relative_to(R));ev=[str((S/(stem+'.json')).relative_to(R)),image]
  def add(suffix,kind,**kw):c['requirements'].append(dict(id=key+'-'+suffix,state=key,kind=kind,evidence=ev,**kw))
  state={'accessible_text':['青铜等级','设置状态','清除','去学个单元'],'elements':{},'interactions':{'status_selected':selected,'footer_status_visible':selected},'capture':{'path':image,'content_rect_points':[0,0,1200,732],'window_points':[1200,732],'backing_scale':1},'pixel_color_space':'sRGB','pixel_samples':{}};ref['states'][key]=state
  add('whole','image_pixels',reference_image=image,pixels=[1200,732])
  for i,t in enumerate(state['accessible_text']):assert t in source['snapshot'];add('text-'+str(i),'accessible_text',text=t)
  buttons=[a for a in source['actions'] if a['tag']=='BUTTON' and a['rect'][0]>820 and 275<a['rect'][1]<390];assert len(buttons)==12
  for i,a in enumerate(buttons):
   name='leaderboard-status-'+str(i);state['elements'][name]={k:a[k] for k in ['rect','role','enabled']}
   add(name+'-geometry','element_geometry',element=name,rect=a['rect'],tolerance_points=0);add(name+'-role','element_role',element=name,role=a['role']);add(name+'-enabled','element_boolean',element=name,field='enabled',expected=a['enabled'])
  if selected:
   images=[m for m in source['media'] if '2439bac' in (m.get('src') or '')];assert len(images)==3
   for name,match in [('leaderboard-selected-status',lambda m:m['rect'][0]>1000),('leaderboard-footer-status',lambda m:m['rect'][0]<500)]:
    m=next(m for m in images if match(m));state['elements'][name]={'rect':m['rect']};add(name+'-geometry','element_geometry',element=name,rect=m['rect'],tolerance_points=0)
  for name,value in state['interactions'].items():add(name,'interaction_boolean',field=name,expected=value)
  # Frozen points compare exact source colors, never infer whole-page equality.
  im=srgb_image(Image.open(R/image))
  for point in [(831,300),(854,326),(835,290),(1043,160),(413,646),(414,650),(1024,177)]:
   rgb=list(im.getpixel(point));state['pixel_samples'][','.join(map(str,point))]=rgb;add('pixel-'+','.join(map(str,point)),'pixel_color',point=list(point),rgb=rgb)
  add('actual-audio','pending',description='Original/native actual transition audio equality unverified')
 c.update(revision='english-v55',parent_revision='english-v54',changes=['Actual pointer-state status border/background, panel/footer badge geometry and exact screenshot pixels; fonts probed equal, no speculative global font change'])
 assert c['requirements'][:len(old)]==old and len({r['id'] for r in c['requirements']})==len(c['requirements'])
 scenarios={'journeys':[{'id':'status-visual','steps':[{'native_action':'nav-leaderboards'},{'native_action':'leaderboard-status-0'},{'native_action':'leaderboard-status-0','operation':'hover','state':'leaderboard-visual-selected'},{'native_action':'leaderboard-clear','operation':'hover'},{'native_action':'leaderboard-clear','state':'leaderboard-visual-cleared'}]}],'limits':'AX press after actual pointer hover; not physical click equivalence or all12status outcomes'}
 return c,ref,scenarios
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out-dir',required=True);out=Path(p.parse_args().out_dir);out.mkdir(parents=True,exist_ok=False)
 for n,v in zip(['contract.json','reference.json','scenarios.json'],build()):(out/n).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
