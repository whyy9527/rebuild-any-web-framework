"""Fetch exact public source assets, render SVGs in an isolated browser context."""
import argparse
import concurrent.futures
import hashlib
import gzip
import json
from pathlib import Path
import subprocess
from urllib.request import urlopen

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--cli', required=True); p.add_argument('--session', required=True)
p.add_argument('--manifest', default='projects/duolingo-web/reference-assets-en-zh-v1.json')
p.add_argument('--out', default='projects/duolingo-web/evidence/english-v1/resources.json')
a = p.parse_args()
base = Path('projects/duolingo-web')
out = Path('projects/education-swift/Sources/LingoSeed/Resources/Reference')
rows = json.loads(Path(a.manifest).read_text())
def fetch(row):
    path = out/row['source_file']
    if not path.exists():
        with urlopen(row['url'], timeout=30) as response:
            data = response.read()
            encoding = response.headers.get('Content-Encoding', '').lower()
            if encoding == 'gzip' or data.startswith(b'\x1f\x8b'):
                row['wire_sha256'] = hashlib.sha256(data).hexdigest()
                row['content_encoding'] = 'gzip'
                data = gzip.decompress(data)
        if row['kind'] not in ('speech', 'feedback'): assert b'<svg' in data[:2000]
        path.write_bytes(data)
    row['sha256'] = hashlib.sha256(path.read_bytes()).hexdigest()
    return row
with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
    rows = list(pool.map(fetch, rows))
images = [{'name': r['name'], 'svg': (out/r['source_file']).read_text(),
           'inline_svg':r.get('inline_svg',False),
           'background_position':r.get('background_position'), 'width': r.get('render_width',180), 'height': r.get('render_height',180), 'target': str((out/(r['name']+'.png')).resolve())} for r in rows if r['kind'] not in ('speech', 'feedback') and not (out/(r['name']+'.png')).exists()]
# Own tab is used only to reach its browser; asset rendering does not share
# reference cookies, navigation or state.
code = '''async page => {
 const context=await page.context().browser().newContext({viewport:{width:180,height:180},deviceScaleFactor:3});
 try {const render=await context.newPage();
 for(const image of IMAGES){await render.setViewportSize({width:Math.ceil(image.width),height:Math.ceil(image.height)}); const source='data:image/svg+xml;base64,'+Buffer.from(image.svg).toString('base64');
 if(image.inline_svg){await render.setContent('<html><body style="margin:0;background:transparent">'+image.svg+'</body></html>');await render.locator('svg').first().evaluate((n,size)=>{n.style.width=size.width+'px';n.style.height=size.height+'px'},image);}
 else if(image.background_position){await render.setContent('<html><body style="margin:0;background:transparent"><div style="width:'+image.width+'px;height:'+image.height+'px;background-image:url('+source+');background-position:'+image.background_position+'"></div></body></html>');await render.evaluate(async src=>{const i=new Image();i.src=src;await i.decode();},source);}
 else {await render.setContent('<html><body style="margin:0;background:transparent"><img style="width:'+image.width+'px;height:'+image.height+'px;object-fit:contain" src="'+source+'"></body></html>');await render.locator('img').evaluate(n=>n.decode());} await render.screenshot({path:image.target,omitBackground:true});}
 return {rendered:IMAGES.length,scale:3};
 }finally{await context.close()}
}'''.replace('IMAGES', json.dumps(images))
r = subprocess.run([a.cli,'-s='+a.session,'run-code',code],cwd='artifacts/output/playwright',text=True,capture_output=True,timeout=90)
raw_receipt=Path(a.out).with_suffix('.raw.txt');raw_receipt.parent.mkdir(parents=True,exist_ok=True);raw_receipt.write_text(r.stdout+r.stderr)
if r.returncode or '### Result\n' not in r.stdout: raise RuntimeError('Asset rendering failed; inspect browser before retry')
for row in rows:
    if row['kind'] not in ('speech', 'feedback'):
        row['rendered_file'] = row['name']+'.png'
        row['rendered_sha256'] = hashlib.sha256((out/row['rendered_file']).read_bytes()).hexdigest()
receipt = Path(a.out)
receipt.parent.mkdir(parents=True, exist_ok=True)
receipt.write_text(json.dumps({'resources':rows,'render':'Original SVG, transparent at 3x; dimensions from optional render_width/render_height, otherwise legacy 180x180; optional background_position reproduces observed CSS sprite viewport; isolated context; native geometry still to verify'},indent=2)+'\n')
print(json.dumps({'downloaded':len(rows),'rendered':len(images),'hashes_recorded':True}))
