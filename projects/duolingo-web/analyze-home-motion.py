"""Inspect actual captured motion in the frozen Duo rectangle; not animation equality."""
import argparse,json,hashlib
from pathlib import Path
from PIL import Image,ImageChops,ImageStat
from capture_color import srgb_image

def analyze(observed,rect):
 receipt=json.loads(Path(observed).read_text());samples=[]
 for i in range(6):
  key='home-motion-frame-'+str(i);capture=receipt['states'][key]['capture'];path=Path(capture['path']);x,y,w,h=capture['content_rect_points'];scale=capture['backing_scale']
  with Image.open(path) as im:
   assert im.size==tuple(round(v*scale) for v in capture['window_points'])
   normalized=srgb_image(im).crop(tuple(round(v*scale) for v in [x,y,x+w,y+h])).resize((int(w),int(h)),Image.Resampling.LANCZOS)
   rx,ry,rw,rh=rect;samples.append(normalized.crop((round(rx),round(ry),round(rx+rw),round(ry+rh))))
 pairs=[]
 for i,(a,b) in enumerate(zip(samples,samples[1:])):
  diff=ImageChops.difference(a,b);pairs.append({'pair':[i,i+1],'different':any(hi!=0 for lo,hi in diff.getextrema()),'mean_absolute_rgb_difference':ImageStat.Stat(diff).mean})
 return {'capture_receipt':str(observed),'frame_pixel_sha256':[hashlib.sha256(x.tobytes()).hexdigest() for x in samples],'adjacent_pairs':pairs,'changed_pairs':sum(p['different'] for p in pairs),'limitations':['Frozen source Duo rectangle only; this diagnostic is not whole-image equality','No phase alignment, loop-period, speed, or cross-renderer acoustic/visual equality claim']}
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--reference',required=True);p.add_argument('--candidate',required=True);p.add_argument('--out',required=True);a=p.parse_args()
 r=json.loads(Path(a.reference).read_text());rect=r['states']['home-motion-frame-0']['elements']['home-duo-animation']['rect'];result={'rectangle':rect,'reference':analyze(a.reference,rect),'candidate':analyze(a.candidate,rect)}
 Path(a.out).write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:result[k]['changed_pairs'] for k in ['reference','candidate']}))
