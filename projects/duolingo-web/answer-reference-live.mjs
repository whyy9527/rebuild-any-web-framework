// Submit a model-chosen answer to the actually visible word bank. Persist the
// acceptance receipt before any transition; continue is a separate operation.
import {spawnSync} from 'node:child_process';
import {writeFileSync,mkdirSync,existsSync} from 'node:fs';
import {resolve,dirname} from 'node:path';
function arg(name){const i=process.argv.indexOf(name);if(i<0)throw Error('Required '+name);return process.argv[i+1];}
const words=JSON.parse(arg('--words')), output=resolve(arg('--out'));
if(!Array.isArray(words)||!words.length||!words.every(w=>typeof w==='string'&&w))throw Error('Nonempty word sequence required');
mkdirSync(dirname(output),{recursive:true});
const prefix=resolve('artifacts/output/playwright',arg('--screenshot-prefix'));
for(const path of [output,output+'.raw.txt',...['before','feedback'].map(s=>prefix+'-'+s+'.png')])
 if(existsSync(path))throw Error('Output already exists; choose fresh receipt and screenshot stems before any action');
const callback=async page=>{
 const actions=WORDS, prefix=PREFIX;
 await page.waitForFunction(()=>document.querySelectorAll('[data-test~="challenge"]').length===1);
 const challenge=page.locator('[data-test~="challenge"]'),bank=challenge.locator('[data-test="word-bank"]');
 const before=await page.locator('body').ariaSnapshot(),text=await challenge.innerText();
 const prompts=await challenge.locator('[data-test=hint-token]').evaluateAll(ns=>[...new Set(ns.map(n=>n.parentElement.innerText.trim()).filter(Boolean))]);
 const choices=await bank.getByRole('button').allTextContents();
 const images=await challenge.locator('img').evaluateAll(ns=>ns.map(n=>({alt:n.alt,src:n.currentSrc||n.src})));
 await page.screenshot({path:prefix+'-before.png'});
 const clicks=[];
 for(const word of actions){
  const matches=bank.getByRole('button',{name:word,exact:true});let selected=false;
  for(let i=0;i<await matches.count();i++)if(await matches.nth(i).isVisible()&&await matches.nth(i).isEnabled()){
   await matches.nth(i).click();clicks.push({word,occurrence:i});selected=true;break;
  }
  if(!selected)throw Error('No available occurrence: '+word);
 }
 await page.getByRole('button',{name:'检查',exact:true}).click();
 await page.getByRole('button',{name:'继续',exact:true}).waitFor();
 const feedback=await page.locator('body').ariaSnapshot(),rejected=await page.locator('[data-test~="blame-incorrect"]').count()>0;
 await page.screenshot({path:prefix+'-feedback.png'});
 return {before,text,prompts,choices,images,clicks,feedback,rejected,next_action:'Receipt saved before transition. Inspect acceptance then continue separately; no assumed next question.'};
};
const code=callback.toString().replace('WORDS',JSON.stringify(words)).replace('PREFIX',JSON.stringify(prefix));
const r=spawnSync(arg('--cli'),['-s='+arg('--session'),'run-code',code],{cwd:resolve('artifacts/output/playwright'),encoding:'utf8',timeout:90000,maxBuffer:4*1024*1024});
const raw=(r.stdout||'')+(r.stderr||'');writeFileSync(output+'.raw.txt',raw,{flag:'wx'});
if(r.status!==0||!raw.includes('### Result\n'))throw Error('Submission receipt unavailable; inspect current UI, do not repeat answer blindly');
const facts=JSON.parse(raw.split('### Result\n')[1].split('\n### Ran')[0]);
writeFileSync(output,JSON.stringify({...facts,observed_at:new Date().toISOString()},null,2)+'\n',{flag:'wx'});
console.log(JSON.stringify({prompts:facts.prompts,rejected:facts.rejected,receipt_saved_before_transition:true}));
if(facts.rejected)process.exitCode=1;
