// Execute the recorded policy against actual DOM groups, with scroll/selection receipts.
import {spawnSync} from 'node:child_process';
import {readFileSync,writeFileSync} from 'node:fs';
import {resolve} from 'node:path';
const get=n=>process.argv[process.argv.indexOf(n)+1];
for(const n of ['--cli','--session','--out'])if(!process.argv.includes(n))throw Error('Required '+n);
const out=resolve(get('--out')),policy=JSON.parse(readFileSync(out+'/policy-before-deployment.json','utf8'));
const transitions=[];
for(const [i,entry] of policy.deployment.entries()){
 const fn=async page=>{
  await page.locator('._1qsHg > div').nth(ENTRY.category).click();
  const groups=page.getByRole('radiogroup');
  const inventory=await groups.evaluateAll(ns=>ns.map(n=>({label:n.getAttribute('aria-label')||n.previousElementSibling?.textContent?.trim(),options:n.querySelectorAll('[role="radio"]').length})));
  const index=inventory.findIndex(g=>g.label===ENTRY.group);if(index<0)throw Error('Actual group absent: '+ENTRY.group);
  const group=groups.nth(index),radios=group.getByRole('radio');
  const before=await radios.evaluateAll(ns=>ns.map(n=>n.getAttribute('aria-checked')));
  const target=before.findIndex(x=>x!=='true');if(target<0)throw Error('No unselected option');
  await radios.nth(target).scrollIntoViewIfNeeded();
  const scrolled=await radios.nth(target).evaluate(n=>{const r=n.getBoundingClientRect(),hit=document.elementFromPoint(r.x+r.width/2,r.y+r.height/2);return {rect:[r.x,r.y,r.width,r.height],center_hit:!!hit&&(hit===n||n.contains(hit))};});
  await radios.nth(target).click();const selected=await radios.evaluateAll(ns=>ns.map(n=>n.getAttribute('aria-checked')));
  await page.locator('._1qsHg > div').nth(8).click();await page.locator('._1qsHg > div').nth(ENTRY.category).click();
  const revisited=await groups.nth(index).getByRole('radio').evaluateAll(ns=>ns.map(n=>n.getAttribute('aria-checked')));
  await groups.nth(index).getByRole('radio').nth(target).scrollIntoViewIfNeeded();
  return {observed_at:new Date().toISOString(),entry:ENTRY,inventory,group_index:index,target,before,scrolled,selected,revisited};
 };
 const r=spawnSync(get('--cli'),['-s='+get('--session'),'run-code',fn.toString().replaceAll('ENTRY',JSON.stringify(entry))],{cwd:resolve('artifacts/output/playwright'),encoding:'utf8',timeout:60000,maxBuffer:4*1024*1024});
 writeFileSync(out+'/action-'+i+'.raw.txt',(r.stdout||'')+(r.stderr||''),{flag:'wx'});
 if(r.status!==0||!r.stdout.includes('### Result\n'))throw Error('Inspect source before resuming');
 transitions.push(JSON.parse(r.stdout.split('### Result\n')[1].split('\n### Ran')[0]));
 writeFileSync(out+'/transitions.json',JSON.stringify(transitions,null,2)+'\n');
 const c=spawnSync(process.execPath,['projects/duolingo-web/capture-visible-state.mjs','--cli',get('--cli'),'--session',get('--session'),'--out',out+'/group-'+i],{encoding:'utf8',timeout:65000});if(c.status!==0)throw Error(c.stderr||c.stdout);
 console.log(JSON.stringify({entry,retained:JSON.stringify(transitions.at(-1).selected)===JSON.stringify(transitions.at(-1).revisited)}));
}
