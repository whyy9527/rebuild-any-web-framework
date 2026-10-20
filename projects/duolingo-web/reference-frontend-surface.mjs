// Serialized into the actual source browser; only rendered DOM, no session payload.
export function referenceFrontendSurface() {
 const rect=n=>{const r=n.getBoundingClientRect();return [r.x,r.y,r.width,r.height]};
 const shown=n=>n.checkVisibility({checkOpacity:true,checkVisibilityCSS:true});
 const intersects=r=>r[2]>0&&r[3]>0&&r[0]<innerWidth&&r[1]<innerHeight&&r[0]+r[2]>0&&r[1]+r[3]>0;
 const css=n=>{const s=getComputedStyle(n);return Object.fromEntries(['fontFamily','fontSize','fontWeight','lineHeight','color','backgroundColor','borderRadius','borderWidth'].map(k=>[k,s[k]]))};
 const controls=[...document.querySelectorAll('a[href],button,input,[role="button"],[role="radio"],[role="checkbox"],[tabindex]:not([tabindex="-1"])')].filter(shown).map((n,i)=>{
  const r=rect(n),hit=document.elementFromPoint(r[0]+r[2]/2,r[1]+r[3]/2);
  return {id:'surface-action-'+i,tag:n.tagName,test:n.getAttribute('data-test'),name:n.getAttribute('aria-label')||n.innerText||n.getAttribute('placeholder')||'',role:n.getAttribute('role')||({BUTTON:'button',A:'link',INPUT:n.type==='radio'?'radio':'textbox'}[n.tagName]??null),rect:r,enabled:!n.disabled&&n.getAttribute('aria-disabled')!=='true',checked:typeof n.checked==='boolean'?n.checked:n.getAttribute('aria-checked'),intersects_viewport:intersects(r),center_hit:!!hit&&(hit===n||n.contains(hit)),css:css(n)};
 });
 const text_runs=[];const walker=document.createTreeWalker(document.body,NodeFilter.SHOW_TEXT);
 while(walker.nextNode()) {
  const n=walker.currentNode,p=n.parentElement,text=n.textContent.trim();if(!text||!p||!shown(p)||['SCRIPT','STYLE','NOSCRIPT'].includes(p.tagName))continue;
  const range=document.createRange();range.selectNodeContents(n);const b=range.getBoundingClientRect(),r=[b.x,b.y,b.width,b.height];if(!intersects(r))continue;
  const clipping=[];for(let a=p;a&&a!==document.body;a=a.parentElement){const s=getComputedStyle(a);if(/hidden|clip|scroll|auto/.test(s.overflow+s.overflowX+s.overflowY))clipping.push({rect:rect(a),overflow:[s.overflowX,s.overflowY]})}
  text_runs.push({text,tag:p.tagName,test:p.getAttribute('data-test'),rect:r,css:css(p),clipping});
 }
 return {path:location.pathname,viewport:[innerWidth,innerHeight],observed_at:new Date().toISOString(),actions:controls.filter(a=>a.intersects_viewport),control_inventory:controls,text_runs,limitations:['Rendered DOM ranges retain clipping ancestors; clipped text inventory is not automatically visible truth','Hit-test and viewport reachability are separate from executed interaction coverage','Audio, motion and future behavior require separate observations']};
}
