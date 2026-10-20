"""Render the current frozen source/native comparison without modifying captures."""
import argparse
from html import escape
import json
import os
from pathlib import Path

p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',required=True);a=p.parse_args()
root=Path(__file__).resolve().parents[2];base=root/'projects/duolingo-web'
out=Path(a.out).resolve();out.parent.mkdir(parents=True,exist_ok=True)
evidence=base/'evidence/english-third-native-v1'
result=json.loads((evidence/'final-result.json').read_text())
counts={status:sum(row['status']==status for row in result['rows']) for status in ['pass','fail','not_run']}
metadata=json.loads((evidence/'final-window.json').read_text())
height=metadata['window_points'][1];offset=metadata['content_rect_points'][1]/height*100
pairs=[('首课完成后的主页',base/'evidence/english-home-v2/reference-english-home-v2.png',evidence/'final-after-first-home-window.png'),
       ('第三课首题：水',base/'evidence/english-third-v1/reference-english-third-question-0-before.png',evidence/'final-en-zh-l3-q0-before.png'),
       ('第三课：两个“不要”',base/'evidence/english-third-v1/reference-english-third-02-question-9-before.png',evidence/'final-en-zh-l3-q9-before.png'),
       ('第三课现场挑战：糖和牛奶',base/'evidence/english-third-v1/reference-english-third-adaptive-12-before.png',evidence/'final-en-zh-l3-q12-before.png')]
sections=[]
for label,source,native in pairs:
    for file in (source,native):assert file.is_file(),file
    source_url=escape(os.path.relpath(source,out.parent),quote=True);native_url=escape(os.path.relpath(native,out.parent),quote=True)
    sections.append(f'<section><h2>{escape(label)}</h2><div class="pair"><figure><figcaption>原版 · 1200 × 732</figcaption><div class="frame"><img src="{source_url}"></div></figure><figure><figcaption>Swift · 同内容视口</figcaption><div class="frame"><img class="native" src="{native_url}"></div></figure></div></section>')
html=f'''<!doctype html><html lang="zh"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>英语第三课 · 原版 / Swift 对照</title>
<style>body{{font:16px system-ui;margin:0;background:#f5f6f7;color:#263238}}main{{max-width:1600px;margin:auto;padding:28px}}h1{{font-size:26px}}p{{line-height:1.7}}section{{margin:30px 0}}h2{{font-size:20px}}.pair{{display:grid;grid-template-columns:1fr 1fr;gap:16px}}figure{{margin:0}}figcaption{{padding:8px 0;font-weight:600}}.frame{{position:relative;aspect-ratio:1200/732;overflow:hidden;background:white;border:1px solid #ddd;border-radius:8px}}img{{display:block;width:100%}}.native{{transform:translateY(-{offset}%);position:absolute;top:0}}@media(max-width:850px){{.pair{{grid-template-columns:1fr}}}}</style>
<main><h1>英语第三课：原版 / Swift 实测对照</h1><p>当前默认三课，共45题。前端契约：{counts['pass']} 通过、{counts['fail']} 失败、{counts['not_run']} 未覆盖，整体未完成。第三课30对截图全部存在差异；角色、动画、布局、声音及完整结算仍待验证和修正。</p><p>保留原图；Swift仅按窗口元数据裁去标题栏，网页图片按相同内容比例展示。此页用于审阅，不将并排查看算作验收通过。</p>{''.join(sections)}</main></html>'''
with out.open('x') as stream:stream.write(html)
print('Rendered four source/native states from actual archived captures')
