// Observe original clock behavior in a separate context; keep session data in memory.
import {spawnSync} from 'node:child_process';
import {mkdirSync,writeFileSync} from 'node:fs';
import {resolve} from 'node:path';
const arg=name=>{const i=process.argv.indexOf(name);if(i<0||!process.argv[i+1])throw Error('Required '+name);return process.argv[i+1];};
const out=resolve(arg('--out'));mkdirSync(out,{recursive:false});
const callback=async page=>{
 const config=CONFIG,base=Date.now(),receipts=[],times=[],network=[];
 const env=await page.evaluate(()=>({origin:location.origin,ua:navigator.userAgent,locale:navigator.language,tz:Intl.DateTimeFormat().resolvedOptions().timeZone,session:Object.entries(sessionStorage)}));
 if(env.origin!=='https://www.duolingo.com')throw Error('Explicit source session must be the Duolingo page');
 const c=await page.context().browser().newContext({storageState:await page.context().storageState({indexedDB:true}),viewport:{width:1200,height:732},userAgent:env.ua,locale:env.locale,timezoneId:env.tz});
 let timer,p;
 try{return await Promise.race([(async()=>{
  await c.addInitScript(({origin,entries,epoch})=>{
   if(location.origin!==origin)return;
   for(const [k,v] of entries)sessionStorage.setItem(k,v);
   // Change only wall-clock reads. Native RAF, performance and timers remain live.
   const NativeDate=Date;let offset=epoch-NativeDate.now();const now=()=>NativeDate.now()+offset;
   function ReferenceDate(...args){if(!new.target)return new NativeDate(now()).toString();return Reflect.construct(NativeDate,args.length?args:[now()],new.target===ReferenceDate?NativeDate:new.target);}
   Object.setPrototypeOf(ReferenceDate,NativeDate);ReferenceDate.prototype=NativeDate.prototype;ReferenceDate.now=now;
   globalThis.Date=ReferenceDate;globalThis.__codexRebuildClock={set:epoch=>{offset=epoch-NativeDate.now();}};
  },{origin:env.origin,entries:env.session,epoch:base});
  p=await c.newPage();p.on('response',async r=>{
   const u=new URL(r.url());if(['fetch','xhr'].includes(r.request().resourceType()))network.push({host:u.hostname,status:r.status()});
   if(u.hostname==='duolingo-leaderboards-prod.duolingo.com'){
    try{const body=await r.json();const walk=(x,path)=>{if(x&&typeof x==='object')for(const [k,v] of Object.entries(x)){const label=path+'.'+k;if(/end|start|time|duration|period|date/i.test(k)&&['number','string'].includes(typeof v))times.push({field:label,value:v});else if(typeof v==='object')walk(v,label);}};walk(body,'response');}catch{}
   }
  });
  await p.goto('https://www.duolingo.com/learn',{waitUntil:'domcontentloaded',timeout:20000});
  await p.locator('svg[viewBox="0 0 1080 1080"]').waitFor({timeout:20000});
  await p.evaluate(()=>{
   const node=[...document.querySelectorAll('body *')].find(n=>n.childElementCount===0 && /^\d+ (小时|分钟|秒)$/.test(n.textContent.trim()) && n.checkVisibility());
   if(!node)throw Error('No visible source countdown');
   const history=[];const record=()=>{const value=node.textContent.trim();if(history.at(-1)?.value!==value)history.push({value,now:Date.now(),performance:performance.now()});};record();
   new MutationObserver(record).observe(node.parentElement,{subtree:true,childList:true,characterData:true});
   globalThis.__codexRebuildClock.read=()=>({value:node.textContent.trim(),rect:(r=>[r.x,r.y,r.width,r.height])(node.getBoundingClientRect()),history:history.slice()});
  });
  for(const delta of config.deltas){
   await p.evaluate(epoch=>globalThis.__codexRebuildClock.set(epoch),base+delta);
   await new Promise(r=>setTimeout(r,1500));
   const before=await p.evaluate(()=>globalThis.__codexRebuildClock.read());
   const path=config.out+'/source-'+delta+'.png';await p.screenshot({path,timeout:5000});const after=await p.evaluate(()=>globalThis.__codexRebuildClock.read());
   receipts.push({delta,countdown:after,stable_clock_capture:before.value===after.value,now:await p.evaluate(()=>Date.now()),text:await p.locator('body').innerText(),svg:await p.locator('svg[viewBox="0 0 1080 1080"]').evaluate(n=>n.outerHTML),rect:await p.locator('svg[viewBox="0 0 1080 1080"]').boundingBox(),path});
  }
  return {isolated_context:true,wall_clock_only:true,progressing_offset_clock:true,base,receipts,times,network};
 })(),new Promise((_,reject)=>{timer=setTimeout(()=>reject(new Error('Owned clock capture deadline 55s')),55000);})]);
 }catch(e){let observed;try{if(p){await p.screenshot({path:config.out+'/failure.png',timeout:2000});observed={url:p.url(),text:await p.locator('body').innerText({timeout:2000})};}}catch{}return {isolated_context:true,base,receipts,times,network,observed,failure:String(e)};
 }finally{clearTimeout(timer);await c.close();}
};
const code=callback.toString().replace('CONFIG',JSON.stringify({out,deltas:process.argv.includes('--contest-start')?[Number(arg('--contest-start'))-Date.now()-7200000,Number(arg('--contest-start'))-Date.now()-1800000,Number(arg('--contest-start'))-Date.now()-30000]:[0,1800000,3600000]}));
const r=spawnSync(arg('--cli'),['-s='+arg('--session'),'run-code',code],{cwd:resolve('artifacts/output/playwright'),encoding:'utf8',maxBuffer:8*1024*1024,timeout:70000});
writeFileSync(out+'/raw.txt',(r.stdout||'')+(r.stderr||''),{flag:'wx'});
if(r.status!==0||!r.stdout.includes('### Result\n'))throw Error('Clock observation unavailable; inspect current process before repeating');
const facts=JSON.parse(r.stdout.split('### Result\n')[1].split('\n### Ran')[0]);writeFileSync(out+'/observed.json',JSON.stringify(facts,null,2)+'\n',{flag:'wx'});
console.log(JSON.stringify({captured:facts.receipts?.length??0,failure:facts.failure??null}));if(facts.failure)process.exitCode=1;
