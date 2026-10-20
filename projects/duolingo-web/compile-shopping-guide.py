"""Compile actual shopping guide text, five clicked audio buttons and layout."""
import argparse,importlib.util,json
from pathlib import Path
B=Path(__file__).resolve().parent;E=B/'evidence/english-shopping-guide-v1';S=E/'source';R=B.parent/'education-swift/Sources/LingoSeed/Resources/Reference'
p=argparse.ArgumentParser();p.add_argument('--out-dir');a=p.parse_args();out=Path(a.out_dir) if a.out_dir else None
if out:out.mkdir(parents=True,exist_ok=False)
spec=importlib.util.spec_from_file_location('english',B/'compile-english-course.py');c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)
def raw(name):
 text=(S/name).read_text();assert '### Result\n' in text
 return json.loads(text.split('### Result\n')[1].split('\n### Ran')[0])
layout=raw('grocery-guide-layout-top.raw.txt');audio=raw('grocery-guide-all-five-audio.raw.txt');source=json.loads((S/'grocery-guide-v2-top.json').read_text())
assert len(layout['rows'])==len(audio['rows'])==5 and layout['scrollY']==0
origin=[280,104]
def local(r):return [r[0]-origin[0],r[1]-origin[1],*r[2:]]
phrases=[]
for row,clip in zip(layout['rows'],audio['rows']):
 assert row['index']==clip['index'] and row['text']==clip['text'] and len(clip['played'])==1
 english,translation=row['text'].split('\n')
 phrases.append(dict(id='shopping-phrase-'+str(row['index']),english=english,translation=translation,audioResource=c.resource(clip['played'][0]['src'],'speech'),card=local(row['card']),speaker=local(row['speaker']),englishRect=local(row['english']),translationRect=local(row['translation']),tokens=[dict(label=t['label'],rect=local(t['rect'])) for t in row['tokens']]))
character=next(m for m in source['media'] if '/pathCharacters/guidebook/' in (m.get('src') or ''))
characterResource=c.resource(character['src'],'home');c.resources[characterResource].update(render_width=106,render_height=156)
back=next(m for m in source['media'] if m['tag']=='IMG' and m['rect']==[280,64,16,16]);backResource=c.resource(back['src'],'home');c.resources[backResource].update(render_width=16,render_height=16)
dotted=next(m for m in source['background_media'] if '06f94a15de0c0937cce25dc5dc083e6e.svg' in m['backgroundImage'])
dottedResource=c.resource(dotted['backgroundImage'].split('"')[1],'home');c.resources[dottedResource].update(render_width=6,render_height=2)
title=next(t for t in source['text_runs'] if t['text']=='第 1 部分指南');subtitle=next(t for t in source['text_runs'] if t['text']=='来看看这一部分的语法点和重点语句吧！');key=next(t for t in source['text_runs'] if t['text']=='重点语句')
idle=raw('grocery-guide-idle-speaker.raw.txt')
name='en-shopping-guide-speaker-idle'
(out/(name+'.svg') if out else R/(name+'.svg')).write_text(idle['svg'])
c.resources[name]=dict(name=name,url='https://www.duolingo.com/guidebook/en/11',kind='home',source_file=name+'.svg',render_width=29,render_height=22,inline_svg=True,source=idle['source'])
content=dict(title=title['text'],subtitle=subtitle['text'],keyTitle=key['text'],titleRect=local(title['rect']),subtitleRect=local(subtitle['rect']),keyRect=local(key['rect']),characterResource=characterResource,characterRect=local(character['rect']),backResource=backResource,dottedResource=dottedResource,phrases=phrases,height=raw('grocery-guide-ancestor-layout.raw.txt')['ancestors'][4]['rect'][3]-80,limits=['Source text is rendered per-letter aria-hidden; full sentences reconstructed only from actually rendered row innerText','Hat hover, click and Enter produced no visible popup; normal lexical hint outcome unknown','Original speaker JSON and five clicked clips retained; acoustic and animation equality unverified'])
for path,data in [(R/'shopping-guide.json',content),(B/'reference-assets-en-zh-shopping-guide-v1.json',list(c.resources.values()))]:
 (out/path.name if out else path).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(dict(phrases=len(phrases),tokens=sum(len(p['tokens']) for p in phrases),resources=len(c.resources))))
