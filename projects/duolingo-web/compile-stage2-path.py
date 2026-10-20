"""Compile the rendered source path, not a guessed number of lessons or pages."""
import argparse
import hashlib
import json
import re
from pathlib import Path

BASE = Path('projects/duolingo-web')
E = BASE / 'evidence/english-stage2-home-v1'
p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--out-dir')
a = p.parse_args()
B = Path(a.out_dir) if a.out_dir else Path('projects/education-swift/Sources/LingoSeed/Resources/Reference')
if a.out_dir: B.mkdir(parents=True, exist_ok=False)
layout = json.loads((E / 'stage2-home-source-02-path-layout-before.json').read_text())
source = json.loads((E / 'source/stage2-home-source-02-home-before.json').read_text())
manifest = {}

def local(rect): return [rect[0] - 280, rect[1] - 138, *rect[2:]]
def resource(url, width, height, svg=None):
    name = 'en-stage2-path-' + hashlib.sha256((svg or url).encode()).hexdigest()[:16]
    manifest[name] = dict(name=name, url=url, kind='image', source_file=name+'.svg',
                          render_width=width, render_height=height)
    if svg:
        (B / (name+'.svg')).write_text(svg)
        manifest[name]['source'] = 'Actual original rendered SVG frame; animation fidelity remains unverified'
        manifest[name]['inline_svg'] = True
    return name

nodes = []
for n in layout['nodes']:
    if n['tag'] not in ['BUTTON', 'A'] or not n.get('test'): continue
    url = re.search(r'<img[^>]+src="([^"]+)"', n['html']).group(1)
    media = next(m for m in source['media'] if m.get('src') == url
                 and n['rect'][1] <= m['rect'][1] < n['rect'][1] + n['rect'][3])
    label = re.search(r'aria-label="([^"]+)"', n['html']).group(1)
    nodes.append(dict(id='stage2-path-'+str(len(nodes)), test=n['test'], label=label,
        rect=local(n['rect']), imageRect=local(media['rect']), resource=resource(url,42,34),
        active=label=='Lesson 1 of 5', role='link' if n['tag']=='A' else 'button'))
artwork = []
chests = []
for m in source['media']:
    if m.get('src') and '/images/path/' in m['src'] and '/icons/' not in m['src'] and m['rect'][3]==90:
        control=next(c for c in source['control_inventory'] if c['name']=='宝箱'
                     and abs(c['rect'][0]-m['rect'][0])<1 and abs(c['rect'][1]-m['rect'][1])<=5)
        chests.append(dict(id='path-chest' if not chests else 'stage2-path-chest-'+str(len(chests)),
                          rect=local(control['rect']),imageRect=local(m['rect']),
                          resource=resource(m['src'],80,90),enabled=control['enabled']))
    if m['tag'].lower()=='svg' and len(m.get('svg') or '')>10000:
        animation=json.loads((BASE/'evidence/english-stage2-path-v1/source-animation-resource.json').read_text())
        artwork.append(dict(rect=local(m['rect']),resource=resource('https://www.duolingo.com/learn',243,236,m['svg']),
                            animationResource=Path(animation['source_file']).stem))
headings=[dict(text=n['text'],rect=local(n['rect'])) for n in layout['nodes'] if n['tag']=='H2' and n['rect'][0]<800 and n['rect'][1]>138]
back_url=re.search(r'<img[^>]+src="([^"]+)"',layout['header']).group(1)
data=dict(headerBack=resource(back_url,16,16),nodes=nodes,chests=chests,artwork=artwork,headings=headings,height=max(n['rect'][1]+n['rect'][3] for n in nodes)+60,
          limits=['Current rendered source inventory is not the whole app; virtualized later units remain in frontier',
                  'Original character frame and loaded animation file retained; native phase/trigger fidelity still unverified',
                  'Only first lesson and first story popup have observed outcomes in this fixture'])
(B/'stage2-path-presentation.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
target=B/'stage2-path-resource-manifest.json' if a.out_dir else BASE/'reference-assets-en-zh-stage2-path-v1.json'
target.write_text(json.dumps(list(manifest.values()),ensure_ascii=False,indent=2)+'\n')
print(json.dumps(dict(nodes=len(nodes),artwork=len(artwork),resources=len(manifest))))
