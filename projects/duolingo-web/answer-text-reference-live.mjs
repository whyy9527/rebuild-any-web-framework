// Submit a chosen value to a previously inspected visible text field; preserve
// acceptance before advancing. Label matching prevents silent input substitution.
import {spawnSync} from 'node:child_process';
import {writeFileSync,mkdirSync,existsSync} from 'node:fs';
import {resolve,dirname} from 'node:path';
function arg(name){const i=process.argv.indexOf(name);if(i<0||!process.argv[i+1])throw Error('Required '+name);return process.argv[i+1];}
const output=resolve(arg('--out'));mkdirSync(dirname(output),{recursive:true});
const prefix=resolve(arg('--screenshot-prefix'));
for(const path of [output,output+'.raw.txt',output+'.intent.json',...['before','filled','feedback'].map(s=>prefix+'-'+s+'.png')])
 if(existsSync(path))throw Error('Output already exists; choose fresh receipt and screenshot stems before any action');
writeFileSync(output+'.intent.json',JSON.stringify({label:arg('--label'),input:arg('--text'),created_at:new Date().toISOString()})+'\n',{flag:'wx'});
const callback=async page=>{
 const label=LABEL,value=VALUE,prefix=PREFIX;
 const input=page.getByRole('textbox',{name:label,exact:true});
 if(await input.count()!==1||!await input.isVisible()||!await input.isEnabled())throw Error('Expected input unavailable; no answer submitted');
 const before=await page.locator('body').ariaSnapshot();
 const challenge=page.locator('[data-test~="challenge"]');
 const visible_text=await challenge.innerText();
 const prompts=await challenge.locator('[data-test=hint-token]').evaluateAll(ns=>[...new Set(ns.map(n=>n.parentElement.innerText.trim()).filter(Boolean))]);
 await page.screenshot({path:prefix+'-before.png'});
 await input.fill(value);
 await page.screenshot({path:prefix+'-filled.png'});
 await page.getByRole('button',{name:'检查',exact:true}).click();
 await page.getByRole('button',{name:'继续',exact:true}).waitFor();
 const feedback=await page.locator('body').ariaSnapshot(),rejected=await page.locator('[data-test~="blame-incorrect"]').count()>0;
 await page.screenshot({path:prefix+'-feedback.png'});
 return {before,visible_text,prompts,input_label:label,input:value,feedback,rejected,next_action:'Inspect receipt before a separate Continue action'};
};
const code=callback.toString().replace('LABEL',JSON.stringify(arg('--label'))).replace('VALUE',JSON.stringify(arg('--text'))).replace('PREFIX',JSON.stringify(prefix));
const r=spawnSync(arg('--cli'),['-s='+arg('--session'),'run-code',code],{cwd:resolve('artifacts/output/playwright'),encoding:'utf8',timeout:90000,maxBuffer:4*1024*1024});
const raw=(r.stdout||'')+(r.stderr||'');writeFileSync(output+'.raw.txt',raw,{flag:'wx'});
if(r.status!==0||!raw.includes('### Result\n'))throw Error('Receipt unavailable; inspect current page without blindly resubmitting');
const facts=JSON.parse(raw.split('### Result\n')[1].split('\n### Ran')[0]);
writeFileSync(output,JSON.stringify({...facts,observed_at:new Date().toISOString()},null,2)+'\n',{flag:'wx'});
console.log(JSON.stringify({rejected:facts.rejected,receipt_saved_before_transition:true}));
if(facts.rejected)process.exitCode=1;
