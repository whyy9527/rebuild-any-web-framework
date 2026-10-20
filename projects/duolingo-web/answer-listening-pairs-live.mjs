// Resolve actual left audio against the captured public pair table, then verify
// source acceptance. Never assume API pair order equals displayed button order.
import {spawnSync} from 'node:child_process';
import {readFileSync,writeFileSync,mkdirSync,existsSync} from 'node:fs';
import {resolve,dirname} from 'node:path';
function arg(name){const i=process.argv.indexOf(name);if(i<0||!process.argv[i+1])throw Error('Required '+name);return process.argv[i+1];}
const output=resolve(arg('--out'));mkdirSync(dirname(output),{recursive:true});
if(existsSync(output)||existsSync(output+'.raw.txt'))throw Error('Existing receipt; inspect before any action');
const session=JSON.parse(readFileSync(arg('--reference'),'utf8')).session;
const c=session.challenges[Number(arg('--index'))].content;
if(c.type!=='listenMatch')throw Error('Expected captured listenMatch');
writeFileSync(output+'.intent.json',JSON.stringify({index:Number(arg('--index')),type:c.type})+'\n',{flag:'wx'});
const callback=async page=>{
 const pairs=PAIRS,prefix=PREFIX;
 const before=await page.locator('body').ariaSnapshot();
 if(!before.includes('heading "选择配对"'))throw Error('Unexpected current challenge; no action');
 const buttons=await page.getByRole('button').allTextContents();
 for(const p of pairs)if(buttons.filter(t=>t.replace(/^\d+\s*/, '').trim()===p.translation).length!==1)throw Error('Actual right options differ from reference');
 await page.screenshot({path:prefix+'-before.png'});
 const rows=[];
 for(let i=0;i<pairs.length;i++){
  const start=await page.evaluate(()=>window.__referenceMedia.length);
  await page.getByRole('button',{name:String(i+1),exact:true}).click();
  await page.waitForFunction(start=>window.__referenceMedia.slice(start).some(m=>m.src.startsWith('https://d1vq87e9lcf771.cloudfront.net/')),start);
  const played=await page.evaluate(start=>window.__referenceMedia.slice(start),start);
  const urls=[...new Set(played.map(m=>m.src).filter(u=>u.startsWith('https://d1vq87e9lcf771.cloudfront.net/')))];
  const matches=pairs.filter(p=>urls.includes(p.tts));if(matches.length!==1)throw Error('Played audio has no unique public pair binding');
  const target=page.getByRole('button').filter({hasText:matches[0].translation});
  if(await target.count()!==1)throw Error('Right target not unique');
  await target.click();rows.push({left_index:i,played_audio:urls,translation:matches[0].translation});
 }
 await page.getByRole('button',{name:'继续',exact:true}).waitFor();
 const feedback=await page.locator('body').ariaSnapshot(),rejected=await page.locator('[data-test~="blame-incorrect"]').count()>0;
 await page.screenshot({path:prefix+'-feedback.png'});
 return {before,rows,feedback,rejected,limitation:'Playback invocation binding, not acoustic-output equality'};
};
const code=callback.toString().replace('PAIRS',JSON.stringify(c.pairs)).replace('PREFIX',JSON.stringify(resolve(arg('--screenshot-prefix'))));
const r=spawnSync(arg('--cli'),['-s='+arg('--session'),'run-code',code],{cwd:resolve('artifacts/output/playwright'),encoding:'utf8',timeout:90000,maxBuffer:4*1024*1024});
const raw=(r.stdout||'')+(r.stderr||'');writeFileSync(output+'.raw.txt',raw,{flag:'wx'});
if(r.status!==0||!raw.includes('### Result\n'))throw Error('Pair receipt unavailable; inspect current page, do not replay blindly');
const facts=JSON.parse(raw.split('### Result\n')[1].split('\n### Ran')[0]);writeFileSync(output,JSON.stringify({...facts,observed_at:new Date().toISOString()},null,2)+'\n',{flag:'wx'});
console.log(JSON.stringify({pairs:facts.rows.length,rejected:facts.rejected}));if(facts.rejected)process.exitCode=1;
