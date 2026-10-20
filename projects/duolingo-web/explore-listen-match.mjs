// Inspect current source audio pairing, match played public URLs, retain every failure.
import {spawnSync} from 'node:child_process';
import {writeFileSync,mkdirSync} from 'node:fs';
import {resolve,dirname} from 'node:path';
function arg(name){const i=process.argv.indexOf(name);return i<0?null:process.argv[i+1];}
for(const n of ['--cli','--session','--out','--screenshot-prefix'])if(!arg(n))throw Error('Required '+n);
const callback=async page=>{
 const r={kind:'actual-source-listen-match',observed_at:new Date().toISOString(),rows:[],failure:null};
 const save=async()=>page.evaluate(r=>window.__listenMatchReceipt=r,r);
 try {
  await page.waitForFunction(()=>[...document.querySelectorAll('[data-test~="challenge"]')].filter(n=>n.checkVisibility()).length===1);
  const c=page.locator('[data-test~="challenge"]:visible');
  r.type=await c.getAttribute('data-test');
  if(r.type!=='challenge challenge-listenMatch')throw Error('Current state is not audio matching; reference preserved');
  r.before=await page.locator('body').ariaSnapshot();
  const buttons=c.getByRole('button');
  const left=buttons.filter({hasNot:page.locator('[data-test="challenge-tap-token-text"]')});
  const right=buttons.filter({has:page.locator('[data-test="challenge-tap-token-text"]')});
  r.right_text=await right.locator('[data-test="challenge-tap-token-text"]').allTextContents();
  if(await left.count()!==r.right_text.length||!r.right_text.length)throw Error('Audio/text columns differ');
  r.left_rects=[];r.right_rects=[];
  for(let i=0;i<await left.count();i++)r.left_rects.push(await left.nth(i).boundingBox());
  for(let i=0;i<await right.count();i++)r.right_rects.push(await right.nth(i).boundingBox());
  const catalog=await page.evaluate(()=>window.__referenceSession.challenges.flatMap(q=>q.content.pairs??[]).filter(p=>p.tts).map(p=>({tts:p.tts,translation:p.translation})));
  await page.screenshot({path:SCREENSHOT_PREFIX+'-before.png'});await save();
  for(let i=0;i<await left.count();i++){
   const row={left_index:i,actions:[]};r.rows.push(row);await save();
   const start=await page.evaluate(()=>window.__referenceMedia.length);
   await left.nth(i).click();row.actions.push('play left');
   await page.waitForFunction(start=>window.__referenceMedia.slice(start).some(x=>x.src.startsWith('https://d1vq87e9lcf771.cloudfront.net/')),start);
   row.played_audio=await page.evaluate(start=>[...new Set(window.__referenceMedia.slice(start).map(x=>x.src).filter(x=>x.startsWith('https://d1vq87e9lcf771.cloudfront.net/')))],start);
   const translations=[...new Set(catalog.filter(p=>row.played_audio.includes(p.tts)).map(p=>p.translation))];
   if(translations.length!==1)throw Error('Current played audio not uniquely mapped in public source vocabulary');
   row.translation=translations[0];await save();
   const index=r.right_text.indexOf(row.translation);
   if(index<0||r.right_text.lastIndexOf(row.translation)!==index)throw Error('Source text pair missing/ambiguous');
   if(WRONG_FIRST&&i===0){
    const wrong=r.right_text.findIndex(t=>t!==row.translation);await right.nth(wrong).click();row.actions.push({wrong_text:r.right_text[wrong]});
    row.wrong_feedback=await page.locator('body').ariaSnapshot();
    await page.screenshot({path:SCREENSHOT_PREFIX+'-wrong.png'});await save();
    await left.nth(i).click();row.actions.push('replay left');
   }
   await right.nth(index).click();row.actions.push({matched_text:row.translation});
   row.after=await c.ariaSnapshot();await save();
  }
  await page.getByRole('button',{name:'继续',exact:true}).waitFor();
  r.feedback=await page.locator('body').ariaSnapshot();
  await page.screenshot({path:SCREENSHOT_PREFIX+'-feedback.png'});
 }catch(error){r.failure=String(error)}
 await save();return r;
};
const out=resolve(arg('--out'));mkdirSync(dirname(out),{recursive:true});
const code=callback.toString().replaceAll('SCREENSHOT_PREFIX',JSON.stringify(arg('--screenshot-prefix'))).replace('WRONG_FIRST',String(process.argv.includes('--wrong-first')));
const p=spawnSync(arg('--cli'),['-s='+arg('--session'),'run-code',code],{cwd:resolve('artifacts/output/playwright'),encoding:'utf8',timeout:120000,maxBuffer:8*1024*1024});
const raw=(p.stdout??'')+(p.stderr??'');writeFileSync(out+'.raw.txt',raw,{flag:'wx'});
if(!raw.includes('### Result\n'))throw Error('Tool unavailable; raw receipt retained; inspect same source tab');
const result=JSON.parse(raw.split('### Result\n')[1].split('\n### Ran')[0]);
writeFileSync(out,JSON.stringify(result,null,2)+'\n',{flag:'wx'});
console.log(JSON.stringify({observed:result.rows.length,failure:result.failure}));if(result.failure)process.exitCode=1;
