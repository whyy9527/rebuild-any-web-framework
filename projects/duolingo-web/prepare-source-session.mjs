// Prepare a new anonymous English source through observed onboarding controls.
// Browser profile is explicit and private; this is not a server-state reset.
import {spawnSync} from 'node:child_process';
import {mkdirSync,existsSync,writeFileSync} from 'node:fs';
import {resolve} from 'node:path';
const arg=n=>{const i=process.argv.indexOf(n);if(i<0||!process.argv[i+1])throw Error('Required '+n);return process.argv[i+1]};
const cli=arg('--cli'),session=arg('--session'),out=resolve(arg('--out'));
if(existsSync(out))throw Error('Fresh output required');mkdirSync(out,{recursive:true});
const ledger={maximum_actions:32,attempts:[],limitations:['Anonymous fixture preferences, not the human user preferences','No notification permission granted','No server reset or equivalence to the prior completed course']};
function save(){writeFileSync(out+'/actions.json',JSON.stringify(ledger,null,2)+'\n')}
function run(code){const r=spawnSync(cli,['-s='+session,'run-code',code],{cwd:resolve('artifacts/output/playwright'),encoding:'utf8',timeout:60000,maxBuffer:8*1024*1024});if(r.status!==0||!r.stdout.includes('### Result\n'))throw Error('No actual source result: '+(r.stderr||r.stdout).slice(0,400));return JSON.parse(r.stdout.split('### Result\n')[1].split('\n### Ran')[0])}
save();
for(let i=0;i<32;i++){
 const before=run(`async page=>{return {path:new URL(page.url()).pathname,snapshot:await page.locator('body').ariaSnapshot()}}`);
 if(before.path==='/lesson'||before.path==='/learn'){writeFileSync(out+'/prepared.json',JSON.stringify(before,null,2)+'\n');break}
 let target;
 if(before.snapshot.includes('link "Get started"'))target={role:'link',name:'Get started'};
 else if(before.snapshot.includes('button "Get started"'))target={role:'button',name:'Get started',index:0};
 else if(before.snapshot.includes('link "开始使用"'))target={role:'link',name:'开始使用'};
 else {
  for(const choice of ['其他','我是第一次学英语','每天 5 分钟 休闲模式','从最基础的内容开始 从英语课程里最简单的单元开始学习']){
   if(before.snapshot.includes('radio "'+choice+'"')&&!before.snapshot.includes('radio "'+choice+'" [checked]')){target={role:'radio',name:choice};break}
  }
  if(!target&&before.snapshot.includes('button "禁止"'))target={role:'button',name:'禁止'};
  if(!target&&before.snapshot.includes('button "继续"'))target={role:'button',name:'继续'};
 }
 if(!target){writeFileSync(out+'/unknown.json',JSON.stringify(before,null,2)+'\n');throw Error('Unobserved onboarding controls; preserve source')}
 if(ledger.attempts.length>=ledger.maximum_actions)throw Error('Preparation action budget exhausted');
 const row={before,target,status:'attempted',at:new Date().toISOString()};ledger.attempts.push(row);save();
 try{row.after=run(`async page=>{const all=page.getByRole(${JSON.stringify(target.role)},{name:${JSON.stringify(target.name)},exact:true});const c=${target.index===undefined?'all':'all.nth('+target.index+')'};await c.waitFor({state:'visible'});await c.click();return {path:new URL(page.url()).pathname,snapshot:await page.locator('body').ariaSnapshot()}}`);row.status='observed'}catch(e){row.failure=String(e);save();throw e}save();
 // Wait for the next enabled Continue or radio group, not a fixed animation delay.
 if(target.name==='继续')run(`async page=>{await page.waitForFunction(()=>location.pathname==='/lesson'||location.pathname==='/learn'||[...document.querySelectorAll('button,[role=radio]')].some(n=>n.checkVisibility()&&!n.disabled&&(n.getAttribute('role')==='radio'||n.innerText.trim()==='继续')));return {ready:true}}`);
 if(target.name==='Get started'||target.name==='开始使用')run(`async page=>{await page.waitForURL(u=>['/welcome','/register','/lesson','/learn'].includes(u.pathname));await page.getByRole('radiogroup').waitFor();return {ready:true}}`);
}
console.log(JSON.stringify({actual_attempts:ledger.attempts.length}));
