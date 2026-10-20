"""Review the four actual captures; strict judgments remain frontend-v77.json."""
import json
from pathlib import Path

E=Path('projects/duolingo-web/evidence/english-streak-followup-v1')
rows=json.loads((E/'frontend-v77.json').read_text())['rows']
source={'streak-hover':'streak-root','streak-calendar':'details-scoped-root','streak-bottom':'deployment06/step1-after','streak-next':'deployment06/step2-after'}
states=[]
for state,path in source.items():
    result=next(x for x in rows if x['id']==state+'-whole')
    states.append(dict(id=state,source='source/'+path+'.png',native='native-delivery/'+state+'.png',status=result['status'],difference=result['mean_absolute_rgb_difference']))
html='''<!doctype html><html lang="zh"><meta charset="utf-8"><title>连胜实际前端对照</title>
<style>body{margin:24px;font:16px system-ui;color:#333}button{padding:10px;margin:4px}main{display:grid;grid-template-columns:1fr 1fr;gap:16px}.capture{position:relative;aspect-ratio:1200/732;overflow:hidden;background:#ddd}.capture img{width:100%;position:absolute;top:0}.native img{top:-4.3715847%}p{line-height:1.7}#metric{color:#a21d28}</style>
<h1>原版与 Swift：连胜交互实际捕获</h1><p>四张整图仍失败。左侧原版，右侧同一最终二进制的实际窗口内容；只按实测内容区裁去 macOS 标题栏，不屏蔽背景或对齐差异。单页对照不代表整 App 已完成，声音和动画时序仍未验证。</p><nav id="tabs"></nav><p id="metric"></p><main><section><h2>原版</h2><div class="capture"><img id="source"></div></section><section><h2>Swift</h2><div class="capture native"><img id="native"></div></section></main><p>原版日历背景因虚拟化变为杂货单元，Swift 仍保持家居单元；差异完整保留在严格整图结果中。<a href="frontend-v77.json">逐项验收</a> · <a href="validation.json">实际旅程检查</a> · <a href="README.md">证据与复跑</a></p>
<script>const states=STATES;function show(s){document.querySelector('#source').src=s.source;document.querySelector('#native').src=s.native;document.querySelector('#metric').textContent=s.id+'：'+s.status+'；RGB平均绝对差 '+s.difference.map(x=>x.toFixed(4)).join(' / ')}for(const s of states){const b=document.createElement('button');b.textContent=s.id;b.onclick=()=>show(s);document.querySelector('#tabs').append(b)}show(states[0]);</script></html>'''.replace('STATES',json.dumps(states,ensure_ascii=False))
(E/'comparison.html').write_text(html)
