"""Compile the actual unlocked unit12 home; frame assets do not prove animation."""
import argparse,hashlib,json,re
from pathlib import Path
B=Path('projects/duolingo-web');E=B/'evidence/english-unit-placement-v1';S=E/'source';R=B.parent/'education-swift/Sources/LingoSeed/Resources/Reference'
p=argparse.ArgumentParser();p.add_argument('--out-dir');a=p.parse_args();out=Path(a.out_dir) if a.out_dir else R
if a.out_dir:out.mkdir(parents=True,exist_ok=False)
d=json.loads((S/'unit12-home-uncovered.json').read_text());layout=json.loads((S/'unit12-current-path-layout.json').read_text());manifest={}
def local(r):return [r[0]-280,r[1]-138,*r[2:]]
def resource(m,w,h):
 svg=m.get('svg');url=m.get('src') or 'https://www.duolingo.com/learn';name='en-unit12-path-'+hashlib.sha256((svg or url).encode()).hexdigest()[:16]
 manifest[name]=dict(name=name,url=url,kind='image',source_file=name+'.svg',render_width=w,render_height=h)
 if svg:(out/(name+'.svg')).write_text(svg);manifest[name]['inline_svg']=True
 return name
nodes=[]
for n in layout['nodes']:
 if not n.get('test') or n['rect'][1]<138:continue
 m=next(m for m in d['media'] if m.get('src') and '/images/path/icons/' in m['src'] and abs(m['rect'][1]-n['rect'][1]-11.5)<1 and abs(m['rect'][0]-n['rect'][0]-14)<1)
 label=re.search(r'aria-label="([^"]+)"',n['html']).group(1)
 nodes.append(dict(id='unit12-path-'+str(len(nodes)),test=n['test'],label=label,rect=local(n['rect']),imageRect=local(m['rect']),resource=resource(m,42,34),active=label=='Lesson 1 of 6',role='button'))
art=[];chests=[]
for m in d['media']:
 r=m['rect'];url=m.get('src') or ''
 if not 280<=r[0]<800 or r[1]<138 or r[1]>2200:continue
 if len(m.get('svg') or '')>10000 or '/pathCharacters/' in url:
  art.append(dict(rect=local(r),resource=resource(m,round(r[2]),round(r[3])),**({'animationResource':json.loads((E/'source-animations.json').read_text())[0]['name']} if len(m.get('svg') or '')>10000 else {})))
 if '/images/path/' in url and '/icons/' not in url and r[3]==90:
  control=next(c for c in d['control_inventory'] if c['name']=='宝箱' and abs(c['rect'][0]-r[0])<1 and abs(c['rect'][1]-r[1])<=5)
  chests.append(dict(id='path-chest' if not chests else 'unit12-chest-'+str(len(chests)),rect=local(control['rect']),imageRect=local(r),resource=resource(m,80,90),enabled=control['enabled']))
heading=next(v for v in d['visible'] if v['tag']=='H2' and v['text']=='描述你的家居布局')
old=json.loads((R/'stage2-path-presentation.json').read_text())
path=dict(nodes=nodes,chests=chests,artwork=art,headings=[dict(text=heading['text'],rect=local(heading['rect']))],headerBack=old['headerBack'],height=max(n['rect'][1]+n['rect'][3] for n in nodes)+60,limits=['Actual source rendered unit12 after-jump scroll position; hidden earlier completed nodes not reconstructed by this presentation','Actual original Vikram Lottie source acquired after original reload; native trigger/phase and branch outcomes remain to verify'])
for file,data in [('unit12-path-presentation.json',path),('unit12-path-resources.json',list(manifest.values()))]:(out/file).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(dict(nodes=len(nodes),artwork=len(art),resources=len(manifest))))
