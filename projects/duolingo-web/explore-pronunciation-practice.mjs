// Continue the currently observed pronunciation practice, preserve new types and failures.
import {spawnSync} from 'node:child_process';
import {writeFileSync,mkdirSync} from 'node:fs';
import {resolve} from 'node:path';
const arg=n=>process.argv[process.argv.indexOf(n)+1],out=resolve(arg('--out'));mkdirSync(out,{recursive:true});
const answerFile=process.argv.includes('--answers')?JSON.parse((await import('node:fs')).readFileSync(arg('--answers'),'utf8')):null;
const callback=async page=>{
 const answers=ANSWERS??{};
 const receipt={kind:'actual-pronunciation-practice-continuation',observed_at:new Date().toISOString(),start_question:START,steps:[],failure:null,terminal:false,answer_memory:answers};
 await page.evaluate(()=>{window.__practicePlays=[];const original=HTMLMediaElement.prototype.play;HTMLMediaElement.prototype.play=function(...args){window.__practicePlays.push({src:this.currentSrc||this.src,at:performance.now()});return original.apply(this,args)}});
 try{
  for(let i=START;i<START+24;i++){
   // A completed answer can remain in the visible DOM during a route transition.
   // Wait for actionable choices or an actual non-choice challenge/result, not a fixed delay.
   await page.waitForFunction(()=>{
    const visible=n=>n.checkVisibility(),enabled=n=>!n.disabled&&n.getAttribute('aria-disabled')!=='true';
    const radios=[...document.querySelectorAll('[role="radio"]')].filter(visible);
    if(radios.length)return radios.length===2&&radios.every(enabled);
    return [...document.querySelectorAll('[data-test~="challenge"],[data-test="session-complete-slide"]')].some(visible)
     ||[...document.querySelectorAll('button')].some(n=>visible(n)&&n.innerText.trim()==='回顾本单元');
   },null,{timeout:15000});
   if(await page.locator('[data-test="session-complete-slide"]').isVisible()
      ||await page.getByRole('button',{name:'回顾本单元',exact:true}).isVisible()){
    receipt.terminal=true;receipt.terminal_snapshot=await page.locator('body').ariaSnapshot();
    await page.screenshot({path:OUT+'/settlement.png'});break;
   }
   const snapshot=await page.locator('body').ariaSnapshot(),step={index:i,before:snapshot};receipt.steps.push(step);
   const radios=page.getByRole('radio');
   if(await radios.count()!==2){step.unhandled='Observed state is not a two-choice question; preserve for next exploration';break;}
   step.labels=await radios.evaluateAll(ns=>ns.map(n=>({label:n.getAttribute('aria-label')||n.innerText,rect:(()=>{const r=n.getBoundingClientRect();return[r.x,r.y,r.width,r.height]})()})));
   await page.screenshot({path:OUT+'/q'+i+'-before.png'});
   await page.evaluate(()=>{window.__practicePlays=[]});
   const challenge=page.locator('[data-test~="challenge"]');step.source_type=await challenge.getAttribute('data-test');
   const speakers=challenge.getByRole('button');if(![1,2].includes(await speakers.count()))throw Error('Unobserved speaker arrangement');
   step.speakers=[];for(let j=0;j<await speakers.count();j++){await page.evaluate(()=>{window.__practicePlays=[]});await speakers.nth(j).click();await page.waitForTimeout(1200);step.speakers.push(await page.evaluate(()=>window.__practicePlays.slice()));}
   step.media=step.speakers.flat();
   const key=JSON.stringify([step.source_type,step.labels.map(x=>x.label.replaceAll('\n',' ')),[...new Set(step.media.map(x=>x.src))].sort()]);const chosen=answers[key]??0;step.chosen=chosen;step.answer_origin=answers[key]===undefined?'first_probe':'prior_feedback';
   await radios.nth(chosen).click();step.selected=await page.locator('body').ariaSnapshot();
   await page.getByRole('button',{name:'检查',exact:true}).click();await page.getByRole('button',{name:'继续',exact:true}).waitFor();
   step.feedback=await page.locator('body').ariaSnapshot();answers[key]=step.feedback.includes('还不太准确')?1-chosen:chosen;await page.screenshot({path:OUT+'/q'+i+'-feedback.png'});
   await page.getByRole('button',{name:'继续',exact:true}).click();await page.waitForTimeout(700);
   step.after_continue=await page.locator('body').ariaSnapshot();
   // The next iteration performs readiness and preserves newly encountered states.
  }
 }catch(error){receipt.failure=String(error)}
 receipt.stop_reason=receipt.failure?'error':receipt.terminal?'terminal':receipt.steps.some(s=>s.unhandled)?'unhandled_state':'budget';
 return receipt;
};
const r=spawnSync(arg('--cli'),['-s='+arg('--session'),'run-code',callback.toString().replaceAll('OUT',JSON.stringify(out)).replaceAll('START',String(Number(arg('--start-index')||1))).replace('ANSWERS',JSON.stringify(answerFile))],{cwd:resolve('artifacts/output/playwright'),encoding:'utf8',timeout:180000,maxBuffer:8*1024*1024});const raw=(r.stdout??'')+(r.stderr??'');writeFileSync(out+'/raw.txt',raw,{flag:'wx'});
if(!raw.includes('### Result\n'))throw Error('Source unavailable; preserve live session');const d=JSON.parse(raw.split('### Result\n')[1].split('\n### Ran')[0]);writeFileSync(out+'/walk.json',JSON.stringify(d,null,2)+'\n',{flag:'wx'});console.log(JSON.stringify({steps:d.steps.length,failure:d.failure,terminal:d.terminal,stop_reason:d.stop_reason}));if(d.failure)process.exitCode=1;
