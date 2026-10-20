// Observe actual play invocations and completion boundaries for visible source buttons.
import {spawnSync} from 'node:child_process';
import {readFileSync,writeFileSync,mkdirSync} from 'node:fs';
import {resolve} from 'node:path';
const arg=n=>process.argv[process.argv.indexOf(n)+1];
const names=JSON.parse(readFileSync(arg('--phonemes'),'utf8')).phonemes.map(x=>x.source_label);
const out=resolve(arg('--out'));mkdirSync(out,{recursive:true});
const callback=async page=>{
 const rows=[];const result={kind:'source-phoneme-audio-completion-boundaries',observed_at:new Date().toISOString(),rows,failure:null};
 await page.evaluate(()=>{window.__phonemeProbe=[];const original=HTMLMediaElement.prototype.play;HTMLMediaElement.prototype.play=function(...args){const record={element:this,src:this.currentSrc||this.src,at:performance.now(),ended:false};window.__phonemeProbe.push(record);this.addEventListener('ended',()=>{record.ended=true},{once:true});return original.apply(this,args)}});
 try{
  await page.waitForTimeout(2000);
  for(const name of NAMES){
   await page.waitForFunction(()=>window.__phonemeProbe.every(x=>x.element.ended||x.element.paused),null,{timeout:10000});
   await page.waitForTimeout(500);
   await page.evaluate(()=>{window.__phonemeProbe=[]});
   const target=page.getByRole('button',{name,exact:true});if(await target.count()!==1)throw Error('Visible observed button missing '+name);
   await target.click();
   await page.waitForFunction(()=>window.__phonemeProbe.length>0,null,{timeout:5000});
   await page.waitForFunction(()=>window.__phonemeProbe.every(x=>x.ended),null,{timeout:10000});
   await page.waitForTimeout(500);
   await page.waitForFunction(()=>window.__phonemeProbe.every(x=>x.ended),null,{timeout:10000});
   rows.push({name,events:await page.evaluate(()=>window.__phonemeProbe.map(x=>({src:x.src,at:x.at,ended:x.ended,duration:x.element.duration,muted:x.element.muted,volume:x.element.volume})))});
  }
 }catch(error){result.failure=String(error)}
 return result;
};
const r=spawnSync(arg('--cli'),['-s='+arg('--session'),'run-code',callback.toString().replace('NAMES',JSON.stringify(names))],{cwd:resolve('artifacts/output/playwright'),encoding:'utf8',timeout:180000,maxBuffer:8*1024*1024});
const raw=(r.stdout??'')+(r.stderr??'');writeFileSync(out+'/raw.txt',raw,{flag:'wx'});
if(!raw.includes('### Result\n'))throw Error('Source observation unavailable; preserve same session');
const result=JSON.parse(raw.split('### Result\n')[1].split('\n### Ran')[0]);writeFileSync(out+'/audio.json',JSON.stringify(result,null,2)+'\n',{flag:'wx'});
console.log(JSON.stringify({rows:result.rows.length,failure:result.failure}));if(result.failure)process.exitCode=1;
