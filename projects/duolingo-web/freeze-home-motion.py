"""Freeze actual homepage Lottie frame images and measured visible SVG bounds."""
import argparse,json,hashlib
from pathlib import Path
BASE=Path(__file__).resolve().parent;ROOT=BASE.parents[1];EV=BASE/'evidence/english-home-motion-v1'
def build():
 c=json.loads((BASE/'frontend-english-v46.json').read_text());old=c['requirements'][:]
 ref=json.loads((BASE/'evidence/english-home-presentation-v1/reference.json').read_text());source=json.loads((EV/'source-motion.json').read_text())
 assert source['viewport']=={'width':1200,'height':732} and len(source['frames'])==6
 for i,f in enumerate(source['frames']):
  name='home-motion-frame-'+str(i);path=str((EV/(name+'.png')).relative_to(ROOT));svg=EV/(name+'.svg')
  assert hashlib.sha256(svg.read_bytes()).hexdigest()==f['svg_sha256'];assert (EV/(name+'.png')).is_file()
  rect=[f['rect'][k] for k in ['x','y','width','height']]
  ref['states'][name]={'elements':{'home-duo-animation':{'tag':'svg','rect':rect}},'capture':{'path':path,'content_rect_points':[0,0,1200,732],'window_points':[1200,732],'backing_scale':1}}
  c['requirements'].append(dict(id=name+'-whole',state=name,kind='image_pixels',reference_image=path,pixels=[1200,732],evidence=[path]))
 assert len({f['svg_sha256'] for f in source['frames']})>1
 c['requirements'].append(dict(id='home-motion-geometry',state='home-motion-frame-0',kind='element_geometry',element='home-duo-animation',rect=[source['frames'][0]['rect'][k] for k in ['x','y','width','height']],tolerance_points=0,evidence=[str((EV/'source-motion.json').relative_to(ROOT))]))
 c.update(revision='english-v47',parent_revision='english-v46',changes=['Actual live homepage Duo motion frame captures and element bounds; no relaxation of v46.'])
 assert c['requirements'][:len(old)]==old
 return c,ref
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out-dir',required=True);a=p.parse_args();out=Path(a.out_dir);out.mkdir(parents=True,exist_ok=False)
 for name,v in zip(['contract.json','reference.json'],build()):(out/name).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
