// Capture each actual settlement page and return to home without registration.
import {spawnSync} from 'node:child_process';
import {mkdirSync,existsSync,writeFileSync} from 'node:fs';
import {resolve} from 'node:path';
const arg=n=>{const i=process.argv.indexOf(n);if(i<0||!process.argv[i+1])throw Error('Required '+n);return process.argv[i+1]};
const cli=arg('--cli'),session=arg('--session'),out=resolve(arg('--out'));
if(existsSync(out))throw Error('Fresh output required');mkdirSync(out,{recursive:true});
const ledger={maximum_actions:8,attempts:[],limits:['Only observed Continue or Later, no registration, purchase or question answering','A successful route is not a server reset']};
function run(code){const r=spawnSync(cli,['-s='+session,'run-code',code],{cwd:resolve('artifacts/output/playwright'),encoding:'utf8',timeout:60000,maxBuffer:8*1024*1024});if(r.status!==0||!r.stdout.includes('### Result\n'))throw Error('No actual source Result');return JSON.parse(r.stdout.split('### Result\n')[1].split('\n### Ran')[0])}
for(let i=0;i<=ledger.maximum_actions;i++){
 run(`async page=>{const ready=await page.waitForFunction(()=>document.querySelector('[data-test~="challenge"]')||document.querySelector('a[href="/sections"]')||[...document.querySelectorAll('button,[role="radio"]')].some(n=>n.checkVisibility()&&!n.disabled&&(['继续','稍后再说','我可以！'].includes(n.innerText.trim())||n.getAttribute('role')==='radio')),{},{timeout:5000}).then(()=>true,()=>false);return {ready}}`);
 const r=spawnSync(process.execPath,['projects/duolingo-web/capture-visible-state.mjs','--cli',cli,'--session',session,'--out',out+'/state-'+i],{encoding:'utf8',timeout:65000});if(r.status!==0)throw Error(r.stderr||r.stdout);
 const before=run(`async page=>{return {path:new URL(page.url()).pathname,snapshot:await page.locator('body').ariaSnapshot(),challenge_count:await page.locator('[data-test~="challenge"]').count(),home_ready:await page.locator('a[href="/sections"]').count()===1}}`);
 if(before.home_ready){writeFileSync(out+'/home-ready.json',JSON.stringify(before,null,2)+'\n');break}
 if(before.challenge_count)throw Error('Preserve actual unfinished exercise');
 const role=before.snapshot.includes('radio "7 天连胜 小试牛刀"')&&!before.snapshot.includes('radio "7 天连胜 小试牛刀" [checked]')?'radio':'button';
 const label=role==='radio'?'7 天连胜 小试牛刀':before.snapshot.includes('button "我可以！"')?'我可以！':before.snapshot.includes('button "稍后再说"')?'稍后再说':before.snapshot.includes('button "继续"')?'继续':null;
 if(!label||i>=ledger.maximum_actions)throw Error('Unknown settlement or budget exhausted');
 const row={before,role,label,status:'attempted'};ledger.attempts.push(row);writeFileSync(out+'/actions.json',JSON.stringify(ledger,null,2)+'\n');
 row.result=run(`async page=>{const previous=await page.evaluate(()=>document.body.innerText);const next=page.getByRole(${JSON.stringify(role)},{name:${JSON.stringify(label)},exact:true});await next.click();if(${JSON.stringify(role)}!=='radio')await page.waitForFunction(previous=>document.body.innerText!==previous,previous);return {path:new URL(page.url()).pathname,snapshot:await page.locator('body').ariaSnapshot()}}`);
 row.status='observed';writeFileSync(out+'/actions.json',JSON.stringify(ledger,null,2)+'\n');
}
console.log(JSON.stringify({actual_attempts:ledger.attempts.length}));
