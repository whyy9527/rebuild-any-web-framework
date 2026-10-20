// Capture actual visible canvas buffers after actual radio selections; no private app state.
import {spawnSync} from 'node:child_process';
import {mkdirSync,writeFileSync,existsSync} from 'node:fs';
import {resolve} from 'node:path';
import {createHash} from 'node:crypto';
const args=process.argv;const get=n=>args[args.indexOf(n)+1];
for(const n of ['--cli','--session','--out'])if(!args.includes(n))throw Error('Required '+n);
const out=resolve(get('--out'));if(existsSync(out))throw Error('Fresh output required');mkdirSync(out,{recursive:true});
const callback=async page=>{
 const radios=page.getByRole('radio');if(await radios.count()!==15)throw Error('Expected actual15skin radios');
 if(await page.locator('canvas').count()!==1)throw Error('Expected one visible avatar canvas');
 const before=await page.locator('body').ariaSnapshot();const rows=[];
 for(let index=0;index<15;index++){
  await radios.nth(index).click();await page.waitForTimeout(250);
  const facts=await radios.nth(index).evaluate(n=>({checked:n.getAttribute('aria-checked'),rect:n.getBoundingClientRect().toJSON(),css:getComputedStyle(n).cssText,children:[...n.querySelectorAll('*')].map(c=>({tag:c.tagName,bg:getComputedStyle(c).backgroundColor,rect:c.getBoundingClientRect().toJSON()}))}));
  const frames=[];
  for(let i=0;i<3;i++){
   frames.push(await page.locator('canvas').evaluate(n=>new Promise(resolve=>requestAnimationFrame(()=>resolve({at:performance.now(),data:n.toDataURL('image/png')})))));
   await page.waitForTimeout(80);
  }
  rows.push({index,...facts,frames});
 }
 return {observed_at:new Date().toISOString(),path:new URL(page.url()).pathname,before,rows,after:await page.locator('body').ariaSnapshot(),limits:['Actual visible canvas buffers, not a complete original renderer','Three short samples do not prove static rendering or animation equivalence','Selections unsaved; original persisted skin unchanged']};
};
const r=spawnSync(get('--cli'),['-s='+get('--session'),'run-code',callback.toString()],{cwd:resolve('artifacts/output/playwright'),encoding:'utf8',timeout:60000,maxBuffer:24*1024*1024});
writeFileSync(out+'/raw.txt',(r.stdout||'')+(r.stderr||''));
if(r.status!==0||!r.stdout.includes('### Result\n'))throw Error('Source capture failed, inspect existing page');
const data=JSON.parse(r.stdout.split('### Result\n')[1].split('\n### Ran')[0]);
for(const row of data.rows)row.frames=row.frames.map((frame,i)=>{
 if(!frame.data.startsWith('data:image/png;base64,'))throw Error('Unexportable canvas');
 const bytes=Buffer.from(frame.data.split(',')[1],'base64'),file='skin-'+row.index+'-frame-'+i+'.png';writeFileSync(out+'/'+file,bytes);
 return {at:frame.at,file,sha256:createHash('sha256').update(bytes).digest('hex')};
});
writeFileSync(out+'/observation.json',JSON.stringify(data,null,2)+'\n');console.log(JSON.stringify({skins:data.rows.length,frames:data.rows.reduce((n,r)=>n+r.frames.length,0)}));
