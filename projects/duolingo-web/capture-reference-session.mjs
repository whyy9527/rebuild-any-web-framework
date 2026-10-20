// Capture public lesson fields from the real sessions response; never persist the raw payload.
// Precondition: owned tab at the explicitly chosen unfinished route. Reload creates a fresh instance.
import {spawnSync} from 'node:child_process';
import {writeFileSync,mkdirSync,existsSync} from 'node:fs';
import {resolve,dirname} from 'node:path';
import {publicChallenge} from './public-reference-challenge.mjs';
function arg(name,fallback){const i=process.argv.indexOf(name);return i<0?fallback:process.argv[i+1];}
for(const name of ['--cli','--session','--out'])if(!arg(name))throw Error('Required: --cli PATH --session NAME --out PATH');
const output=resolve(arg('--out'));mkdirSync(dirname(output),{recursive:true});
for(const path of [output,output+'.raw.txt'])if(existsSync(path))throw Error('Capture output exists; choose a fresh path before reloading');
const route=arg('--route','/lesson');
if(!['/lesson','/practice'].includes(route))throw Error('Supported capture routes: /lesson, /practice');
const callback = async page=>{
 if(new URL(page.url()).pathname!==EXPECTED_ROUTE||await page.locator('[data-test~="challenge"]').count()!==1)throw Error('Capture requires the explicitly selected unfinished route; current page is preserved');
 const sanitize=PUBLIC_CHALLENGE;
 let timer,listener;
 const data=new Promise((resolve,reject)=>{
  timer=setTimeout(()=>reject(Error('No sessions response within capture window; reference preserved')),60000);
  listener=async r=>{if(r.request().method()!=='POST'||!new URL(r.url()).pathname.endsWith('/sessions'))return;try{const d=await r.json();if(!Array.isArray(d.challenges))return;resolve(d)}catch(error){reject(error)}};
  page.on('response',listener);
 });
 const onDialog=async d=>{try{await (d.type()==='beforeunload'?d.accept():d.dismiss())}catch(error){if(!String(error).includes('already handled'))throw error}};
 page.once('dialog',onDialog);
 try {
 await page.addInitScript(()=>{if(window.__referenceMediaInstalled)return;window.__referenceMediaInstalled=true;window.__referenceMedia=[];const play=HTMLMediaElement.prototype.play;HTMLMediaElement.prototype.play=function(...args){window.__referenceMedia.push({src:this.currentSrc||this.src,at:performance.now(),muted:this.muted,volume:this.volume});return play.apply(this,args)}});
 await page.reload({waitUntil:'domcontentloaded'});
 const raw=await data;
 const challenges=raw.challenges.map((c,index)=>({index,keys:Object.keys(c),...sanitize(c,'challenge.'+index)}));
 const publicSession={learningLanguage:raw.learningLanguage,fromLanguage:raw.fromLanguage,type:raw.type,lessonIndex:raw.lessonIndex,levelIndex:raw.levelIndex,levelSessionIndex:raw.levelSessionIndex,
  challenges:challenges.map(({omitted_keys,...row})=>row),omitted_keys:[...new Set(challenges.flatMap(c=>c.omitted_keys))]};
 await page.evaluate(s=>window.__referenceSession=s,publicSession);
 // A fresh session may start with a review introduction, not a question.
 // Preserve the actual state instead of imposing a challenge heading.
 return {source:'Actual sessions response, public lesson fields only; no session/user identifiers or tracking payloads retained',path:new URL(page.url()).pathname,session:publicSession,initial:await page.locator('body').ariaSnapshot()};
 } finally {clearTimeout(timer);page.off('response',listener);page.off('dialog',onDialog)}
};
const result=spawnSync(arg('--cli'),['-s='+arg('--session'),'run-code',callback.toString().replace('PUBLIC_CHALLENGE',publicChallenge.toString()).replace('EXPECTED_ROUTE',JSON.stringify(route))],{cwd:resolve('artifacts/output/playwright'),encoding:'utf8',timeout:90000,maxBuffer:16*1024*1024});
const raw=(result.stdout||'')+(result.stderr||'');writeFileSync(output+'.raw.txt',raw,{flag:'wx'});
if(result.status!==0||!raw.includes('### Result\n'))throw Error('Session unavailable; preserve tab and inspect raw output');
const facts=JSON.parse(raw.split('### Result\n')[1].split('\n### Ran')[0]);
writeFileSync(output,JSON.stringify({...facts,observed_at:new Date().toISOString()},null,2)+'\n',{flag:'wx'});
console.log(JSON.stringify({observed:true,challenges:facts.session.challenges.length}));
