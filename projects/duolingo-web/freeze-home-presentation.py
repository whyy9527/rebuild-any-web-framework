"""Freeze actual completed-node face/highlight and league countdown pixels."""
import argparse,json
from pathlib import Path
from PIL import Image
BASE=Path(__file__).resolve().parent;ROOT=BASE.parents[1];EV=BASE/'evidence/english-home-presentation-v1'
def build():
 c=json.loads((BASE/'frontend-english-v45.json').read_text());old=c['requirements'][:];c.update(revision='english-v46',parent_revision='english-v45',changes=['Actual completed-node highlight/base and yellow countdown pixels; all whole images retained.'])
 ref=json.loads((BASE/'evidence/english-registration-controls-v1/reference.json').read_text());s=ref['states']['chest-reloaded'];source=BASE/'evidence/english-chest-v1/source/reloaded.png';im=Image.open(source).convert('RGB')
 pseudo=json.loads((EV/'source/home-node-pseudo.json').read_text());assert pseudo['::after']['height']=='57px' and pseudo['::after']['background']=='rgb(88, 204, 2)'
 for label,point,rgb in [('base',[520,165],[88,204,2]),('highlight',[520,170],[114,214,39]),('countdown',[931,200],[255,200,0])]:
  assert list(im.getpixel(tuple(point)))==rgb;s.setdefault('pixel_samples',{})[','.join(map(str,point))]=rgb;s['pixel_color_space']='sRGB'
  c['requirements'].append(dict(id='home-'+label+'-pixel-v46',state='chest-reloaded',kind='pixel_color',point=point,rgb=rgb,evidence=[str(source.relative_to(ROOT)),str((EV/'source/home-node-pseudo.json').relative_to(ROOT))]))
 assert c['requirements'][:len(old)]==old
 return c,ref
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out-dir',required=True);a=p.parse_args();out=Path(a.out_dir);out.mkdir(parents=True,exist_ok=False)
 for name,v in zip(['contract.json','reference.json'],build()):(out/name).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
