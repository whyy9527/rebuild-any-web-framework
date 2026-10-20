// Advance one actually observed, uniquely enabled Continue control. Never answer,
// infer a question index, or retry a click after an observation failure.
import {spawnSync} from 'node:child_process';
import {resolve,dirname} from 'node:path';
import {writeFileSync,mkdirSync} from 'node:fs';
function arg(name){const i=process.argv.indexOf(name);if(i<0||!process.argv[i+1])throw Error('Required '+name);return process.argv[i+1];}
const output=resolve(arg('--out')),cwd=resolve('artifacts/output/playwright');
mkdirSync(dirname(output),{recursive:true});
function cli(...args){
 const r=spawnSync(arg('--cli'),['-s='+arg('--session'),...args],{cwd,encoding:'utf8',timeout:60000,maxBuffer:4*1024*1024});
 if(r.status!==0)throw Error('CLI failed; inspect live page before retry: '+r.stdout+r.stderr);
 return r.stdout;
}
const before=cli('snapshot');
const refs=[...before.matchAll(/- button "继续"[^\n]*\[ref=([^\]]+)\][^\n]*/g)].filter(m=>!m[0].includes('[disabled]'));
if(refs.length!==1)throw Error('Expected exactly one visible enabled Continue; no action executed');
writeFileSync(output+'.before.txt',before,{flag:'wx'});
const result=cli('click',refs[0][1]);
writeFileSync(output+'.click.txt',result,{flag:'wx'});
const snapshot=cli('snapshot');
writeFileSync(output+'.json',JSON.stringify({observed_at:new Date().toISOString(),action:'继续',source_ref:refs[0][1],before,after:snapshot},null,2)+'\n',{flag:'wx'});
console.log(snapshot);
