// Real source top-stat probes. No inferred menu outcome or hidden application state.
import {spawnSync} from 'node:child_process';
import {mkdirSync,writeFileSync,existsSync} from 'node:fs';
import {resolve} from 'node:path';
const arg=n=>{const i=process.argv.indexOf(n);if(i<0)throw Error('Required '+n);return process.argv[i+1]};
const cli=arg('--cli'),session=arg('--session'),out=resolve(arg('--out'));mkdirSync(out,{recursive:true});
function run(name,callback){const path=out+'/'+name+'.raw.txt';if(existsSync(path))throw Error('Receipt exists');const r=spawnSync(cli,['-s='+session,'run-code',callback],{cwd:resolve('artifacts/output/playwright'),encoding:'utf8',timeout:60000,maxBuffer:8*1024*1024});writeFileSync(path,(r.stdout||'')+(r.stderr||''),{flag:'wx'});if(r.status!==0||r.stdout.includes('### Error')||!r.stdout.includes('### Result\n'))throw Error('Probe unavailable: '+name);return JSON.parse(r.stdout.split('### Result\n')[1].split('\n### Ran')[0]);}
function capture(name){const r=spawnSync(process.execPath,['projects/duolingo-web/capture-visible-state.mjs','--out',out+'/'+name,'--cli',cli,'--session',session],{encoding:'utf8',timeout:60000});if(r.status!==0)throw Error('Capture unavailable: '+name);}
const receipts=[];
if(process.argv.includes('--decline')){receipts.push(run('decline',`async page=>{await page.getByRole('button',{name:'下次再说',exact:true}).click();await page.getByRole('button',{name:'下次再说',exact:true}).waitFor({state:'hidden'});return {path:new URL(page.url()).pathname,snapshot:await page.locator('body').ariaSnapshot()};}`));capture('home-root');}
for(const [key,label] of [['course','10'],['streak','1'],['gems','505'],['hearts','4']]){
 receipts.push(run(key+'-hover',`async page=>{await page.mouse.move(600,710);await page.getByRole('button',{name:${JSON.stringify(label)},exact:true}).hover();await page.waitForTimeout(500);return {operation:'hover',label:${JSON.stringify(label)},snapshot:await page.locator('body').ariaSnapshot()};}`));capture(key+'-hovered');
}
writeFileSync(out+'/probes.json',JSON.stringify({kind:'actual-source-top-stats-hover',receipts,limitations:['500ms observed hover window, not complete delayed behavior or audio coverage','No click or dismissal behavior inferred from hover','Parent driven discovery, not matched-budget causal RSI']},null,2)+'\n',{flag:'wx'});console.log(JSON.stringify({hovers:4,observed:true}));
