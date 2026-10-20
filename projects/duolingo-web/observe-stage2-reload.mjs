// Verify client reload against the actual source; this is not a server reset.
import {spawnSync} from 'node:child_process';
import {existsSync,mkdirSync,writeFileSync} from 'node:fs';
import {resolve} from 'node:path';
const arg=n=>{const i=process.argv.indexOf(n);if(i<0||!process.argv[i+1])throw Error('Required '+n);return process.argv[i+1];};
const cli=arg('--cli'),session=arg('--session'),out=resolve(arg('--out'));
if(existsSync(out))throw Error('Fresh output required');mkdirSync(out,{recursive:true});
const prepare=process.argv.includes('--prepare-sections');
const ledger={maximum_actions:2,attempts:[],trigger:'Stage2 Learn retained50/50, later Sections showed0/50; distinguish real reload from optimistic route state'};
writeFileSync(out+'/policy-before-actions.json',JSON.stringify(ledger,null,2)+'\n');
function action(name,code){if(ledger.attempts.length>=2)throw Error('Two-action reload probe exhausted');const row={name,status:'attempted'};ledger.attempts.push(row);writeFileSync(out+'/actions.json',JSON.stringify(ledger,null,2)+'\n');const r=spawnSync(cli,['-s='+session,'run-code',code],{cwd:resolve('artifacts/output/playwright'),encoding:'utf8',timeout:60000,maxBuffer:4*1024*1024});writeFileSync(out+'/'+name+'.raw.txt',(r.stdout||'')+(r.stderr||''));if(r.status!==0||!r.stdout.includes('### Result\n'))throw Error('No actual source Result');row.result=JSON.parse(r.stdout.split('### Result\n')[1].split('\n### Ran')[0]);row.status='observed';writeFileSync(out+'/actions.json',JSON.stringify(ledger,null,2)+'\n');}
function capture(stem){const r=spawnSync(process.execPath,['projects/duolingo-web/capture-visible-state.mjs','--cli',cli,'--session',session,'--out',out+'/'+stem],{encoding:'utf8',timeout:65000});if(r.status!==0)throw Error(r.stderr||r.stdout);}
if(prepare){
 action('open-sections',`async page=>{if(new URL(page.url()).pathname!=='/learn')throw Error('Prepare from actual home');await page.locator('a[href="/sections"]').click();return {path:new URL(page.url()).pathname};}`);
 action('scroll-top',`async page=>{await page.evaluate(()=>window.scrollTo(0,0));return {path:new URL(page.url()).pathname,scrollY:await page.evaluate(()=>scrollY)};}`);capture('sections-prepared');
}else{
action('back-to-learn',`async page=>{if(new URL(page.url()).pathname!=='/sections')throw Error('Start at actual sections');await page.getByRole('link',{name:'返回',exact:true}).click();await page.getByRole('heading',{name:'第 2 阶段，第 1 部分',exact:true}).waitFor();return {path:new URL(page.url()).pathname,snapshot:await page.locator('body').ariaSnapshot()};}`);capture('before-reload');
action('reload-learn',`async page=>{await page.reload({waitUntil:'domcontentloaded'});await page.getByRole('heading',{name:'第 2 阶段，第 1 部分',exact:true}).waitFor();return {path:new URL(page.url()).pathname,snapshot:await page.locator('body').ariaSnapshot()};}`);capture('after-reload');
console.log(JSON.stringify({actual_actions:2}));

}
