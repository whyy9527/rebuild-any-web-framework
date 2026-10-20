// Traverse category entries actually observed in the source DOM. No hidden app state.
import {spawnSync} from 'node:child_process';
import {mkdirSync,writeFileSync,existsSync,readFileSync} from 'node:fs';
import {resolve} from 'node:path';
const get=n=>process.argv[process.argv.indexOf(n)+1];
for(const n of ['--cli','--session','--out'])if(!process.argv.includes(n))throw Error('Required '+n);
const out=resolve(get('--out'));if(existsSync(out))throw Error('Fresh output required');mkdirSync(out,{recursive:true});
const cli=get('--cli'),session=get('--session');
function run(callback){
 const r=spawnSync(cli,['-s='+session,'run-code',callback],{cwd:resolve('artifacts/output/playwright'),encoding:'utf8',timeout:60000,maxBuffer:8*1024*1024});
 const file=out+'/action-'+String(records.length).padStart(2,'0')+'.raw.txt';writeFileSync(file,(r.stdout||'')+(r.stderr||''));
 if(r.status!==0||!r.stdout.includes('### Result\n'))throw Error('Action unavailable; inspect existing source tab');
 return JSON.parse(r.stdout.split('### Result\n')[1].split('\n### Ran')[0]);
}
const records=[];
function capture(stem){
 const r=spawnSync(process.execPath,['projects/duolingo-web/capture-visible-state.mjs','--cli',cli,'--session',session,'--out',out+'/'+stem],{encoding:'utf8',timeout:65000,maxBuffer:1024*1024});
 if(r.status!==0)throw Error(r.stderr||r.stdout);
 return JSON.parse(readFileSync(out+'/'+stem+'.json','utf8'));
}
for(let category=0;category<9;category++){
 const action=run(`async page=>{
  if(new URL(page.url()).pathname!=='/settings/avatar')throw Error('Not avatar editor');
  const tabs=page.locator('._1qsHg > div');
  const inventory=await tabs.evaluateAll(ns=>ns.map((n,i)=>({i,cursor:getComputedStyle(n).cursor,src:n.querySelector('img')?.src})));
  if(inventory.filter(n=>n.cursor==='pointer'&&n.src?.includes('/avatar-builder/')).length!==9)throw Error('Category structure changed');
  await tabs.nth(${category}).click();
  // Require the actual selected icon, rather than assuming fixed delay means ready.
  await page.waitForFunction(i=>document.querySelectorAll('._1qsHg > div')[i]?.querySelector('img')?.src.endsWith('_selected.svg'),${category});
  return {category:${category},inventory,operation:'click_observed_category',after:await page.locator('body').ariaSnapshot()};
 }`);
 records.push(action);writeFileSync(out+'/transitions.json',JSON.stringify(records,null,2)+'\n');
 const source=capture('category-'+category);
 const radios=source.actions.filter(a=>a.role==='radio');
 // Explore an actual different option, then leave/revisit to test draft retention.
 if(!process.argv.includes('--inventory-only')&&radios.length>1){
  const index=radios.findIndex(a=>a.checked===false);
  const selected=run(`async page=>{const rs=page.getByRole('radio');const before=await rs.evaluateAll(ns=>ns.map(n=>n.getAttribute('aria-checked')));const target=await rs.evaluateAll(ns=>ns.findIndex(n=>{const r=n.getBoundingClientRect(),hit=document.elementFromPoint(r.x+r.width/2,r.y+r.height/2);return n.getAttribute('aria-checked')!=='true'&&!!hit&&(hit===n||n.contains(hit));}));if(target<0)throw Error('No observed hittable unselected option');await rs.nth(target).click();return {category:${category},operation:'click_unselected_radio',target,before,after:await rs.evaluateAll(ns=>ns.map(n=>n.getAttribute('aria-checked')))};}`);
  records.push(selected);writeFileSync(out+'/transitions.json',JSON.stringify(records,null,2)+'\n');
  capture('selected-'+category);
 }
 console.log(JSON.stringify({category,radios:radios.length,text:source.text_runs.filter(t=>t.rect[0]>650).map(t=>t.text)}));
}
if(!process.argv.includes('--inventory-only'))for(let category=0;category<9;category++){
 const result=run(`async page=>{await page.locator('._1qsHg > div').nth(${category}).click();return {category:${category},operation:'revisit_category',after:await page.getByRole('radio').evaluateAll(ns=>ns.map(n=>n.getAttribute('aria-checked')))};}`);
 records.push(result);writeFileSync(out+'/transitions.json',JSON.stringify(records,null,2)+'\n');
 capture('revisited-'+category);
}
console.log(process.argv.includes('--inventory-only') ? 'Inventory-only traversal: no option selections or saves.' : 'Selections remain unsaved; persistence and composition are not proved by draft retention.');
