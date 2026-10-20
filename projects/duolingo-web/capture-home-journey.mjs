// Actual source navigation branches selected before online collection.
import {spawnSync} from 'node:child_process';
import {mkdirSync,writeFileSync,readFileSync} from 'node:fs';
import {resolve} from 'node:path';
const arg=n=>{const i=process.argv.indexOf(n);if(i<0||!process.argv[i+1])throw Error('Required '+n);return process.argv[i+1];};
const cli=arg('--cli'),session=arg('--session'),out=resolve(arg('--out'));mkdirSync(out,{recursive:false});
const seal=JSON.parse(readFileSync(arg('--seal'),'utf8'));
const order=seal.candidates.find(x=>x.id===seal.selected).order;
const only=process.argv.includes('--only')?arg('--only').split(','):order;const cases=order.filter(id=>only.includes(id));
const targets={profile:{role:'link',name:'个人档案'},login:{role:'button',name:'登录'},shop:{role:'link',name:'宝石小店',test:'shop-nav'},more:{role:'button',name:'更多',hover:true}};
function run(code){const r=spawnSync(cli,['-s='+session,'run-code',code],{cwd:resolve('artifacts/output/playwright'),encoding:'utf8',timeout:30000,maxBuffer:4*1024*1024});if(r.status!==0||!r.stdout.includes('### Result\n'))throw Error('Source operation unavailable; inspect active session before retry: '+r.stdout);return JSON.parse(r.stdout.split('### Result\n')[1].split('\n### Ran')[0]);}
function capture(name){const r=spawnSync(process.execPath,['projects/duolingo-web/capture-visible-state.mjs','--cli',cli,'--session',session,'--out',out+'/'+name],{encoding:'utf8',timeout:65000});if(r.status!==0)throw Error(r.stdout+r.stderr);}
run(`async page=>{await page.setViewportSize({width:1200,height:732});await page.addInitScript(()=>{if(globalThis.__rebuildAudioInstalled)return;globalThis.__rebuildAudioInstalled=true;globalThis.__rebuildAudio=[];const record=(kind,extra)=>globalThis.__rebuildAudio.push({kind,at:performance.now(),...extra});const play=HTMLMediaElement.prototype.play;HTMLMediaElement.prototype.play=function(...args){record('media.play',{src:this.currentSrc||this.src});return play.apply(this,args);};const start=AudioBufferSourceNode.prototype.start;AudioBufferSourceNode.prototype.start=function(...args){record('buffer.start',{duration:this.buffer?.duration,channels:this.buffer?.numberOfChannels,sampleRate:this.buffer?.sampleRate});return start.apply(this,args);};});return {installed:true};}`);
const transitions=[];
for(const id of cases){
 if(!targets[id])throw Error('Unobserved action target');
 run(`async page=>{await page.goto('https://www.duolingo.com/learn',{waitUntil:'domcontentloaded'});await page.getByRole('heading',{name:'第 1 阶段，第 1 部分',exact:true}).waitFor({timeout:15000});await page.mouse.move(1190,730);return {path:new URL(page.url()).pathname};}`);
 capture(id+'-before');
 const result=run(`async page=>{const target=${JSON.stringify(targets[id])};const control=target.test?page.locator('[data-test="'+target.test+'"]'):page.getByRole(target.role,{name:target.name,exact:true});if(await control.count()!==1)throw Error('Source action ambiguous');await page.evaluate(()=>globalThis.__rebuildAudio=[]);const started=Date.now();await control[target.hover?'hover':'click']();let previous='',stable=0,samples=0;while(Date.now()-started<10000){const current=await page.locator('body').ariaSnapshot();stable=current===previous?stable+1:0;previous=current;samples++;if(stable>=3)break;await page.waitForTimeout(200);}return {at:new Date().toISOString(),path:new URL(page.url()).pathname,stable_repeats:stable,samples,wall_ms:Date.now()-started,audio_events:await page.evaluate(()=>globalThis.__rebuildAudio??[]),audio_limitations:['Media/WebAudio start hooks only; no acoustic silence or phase equality claim']};}`);
 capture(id+'-after');
 const returnResult=run(`async page=>{${id==='profile'||id==='login'?"await page.locator('[data-test=close-button]').click();":"await page.getByRole('link',{name:'学习',exact:true}).click();"}await page.getByRole('heading',{name:'第 1 阶段，第 1 部分',exact:true}).waitFor({timeout:15000});await page.mouse.move(1190,730);await page.waitForTimeout(500);return {path:new URL(page.url()).pathname,snapshot:await page.locator('body').ariaSnapshot()};}`);
 capture(id+'-return');result.return=returnResult;
 transitions.push({id,target:targets[id],...result});writeFileSync(out+'/transitions.json',JSON.stringify(transitions,null,2)+'\n');console.log(JSON.stringify({id,path:result.path,stable:result.stable_repeats,audio:result.audio_events.length}));
}
