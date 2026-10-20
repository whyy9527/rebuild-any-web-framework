// Export actual canvas drawing buffers; compositor screenshots remain separate evidence.
// No screenshot crops are treated as transparent character assets.
import {spawnSync} from 'node:child_process';
import {writeFileSync,mkdirSync} from 'node:fs';
import {resolve,dirname,basename} from 'node:path';
import {createHash} from 'node:crypto';
function arg(name){const i=process.argv.indexOf(name);return i<0?null:process.argv[i+1];}
for(const name of ['--cli','--session','--out'])if(!arg(name))throw Error('Required '+name);
const bufferOnly=process.argv.includes('--drawing-buffer-only');
const out=resolve(arg('--out'));mkdirSync(dirname(out),{recursive:true});
const callback=async page=>{
 await page.waitForFunction(()=>document.querySelectorAll('[data-test~="challenge"]').length===1 && document.querySelectorAll('[data-test="challenge-header"]').length===1);
 const canvas=page.locator('[data-test~="challenge"] canvas');
 if(await canvas.count()!==1)throw Error('Expected exactly one source challenge canvas');
 const before=await page.locator('body').ariaSnapshot();
 const prompt=await page.locator('[data-test~="challenge"]').innerText();
 const renderer=await canvas.evaluate(n=>{
  let fiber=n[Object.keys(n).find(k=>k.startsWith('__reactFiber'))];
  for(let i=0;fiber&&i<16;i++,fiber=fiber.return){
   const p=fiber.memoizedProps||{};
   if(p.buffer instanceof ArrayBuffer && p.animation?.url?.startsWith('https://d35aaqx5ub95lt.cloudfront.net/rive/') && !p.animation.url.includes('?')){
    const bytes=new Uint8Array(p.buffer);
    if(String.fromCharCode(...bytes.slice(0,4))!=='RIVE')throw Error('Unexpected source renderer buffer');
    let binary='';for(let j=0;j<bytes.length;j+=8192)binary+=String.fromCharCode(...bytes.slice(j,j+8192));
    return {animation:p.animation,correct:p.correct ?? null,bufferBase64:btoa(binary)};
   }
  }
  return null;
 });
 const metadata=await canvas.evaluate(n=>({width:n.width,height:n.height,rect:n.getBoundingClientRect().toJSON(),style:n.style.cssText,parent_style:n.parentElement.style.cssText,ancestors:[n.parentElement,n.parentElement.parentElement,n.parentElement.parentElement.parentElement].map(a=>({tag:a.tagName,style:a.style.cssText,rect:a.getBoundingClientRect().toJSON()}))}));
 if(!BUFFER_ONLY){
  await page.screenshot({path:OUTPUT+'-page.png'});
  await canvas.screenshot({path:OUTPUT+'-composited-region.png',omitBackground:true});
 }
 const frames=[];
 for(let i=0;i<12;i++){
  frames.push(await canvas.evaluate(n=>new Promise(resolve=>requestAnimationFrame(()=>resolve({at:performance.now(),data:n.toDataURL('image/png')})))));
  await page.waitForTimeout(150);
 }
 return {before,prompt,metadata,renderer,frames,after:await page.locator('body').ariaSnapshot()};
};
const code=callback.toString().replaceAll('OUTPUT',JSON.stringify(out)).replaceAll('BUFFER_ONLY',JSON.stringify(bufferOnly));
const r=spawnSync(arg('--cli'),['-s='+arg('--session'),'run-code',code],{cwd:resolve('artifacts/output/playwright'),encoding:'utf8',timeout:60000,maxBuffer:16*1024*1024});
const raw=(r.stdout||'')+(r.stderr||'');writeFileSync(out+'.raw.txt',raw,{flag:'wx'});
if(r.status!==0||!raw.includes('### Result\n'))throw Error('Canvas capture failed; preserve source page and raw output');
const data=JSON.parse(raw.split('### Result\n')[1].split('\n### Ran')[0]);
if(data.renderer){
 const bytes=Buffer.from(data.renderer.bufferBase64,'base64');
 writeFileSync(out+'.riv',bytes,{flag:'wx'});
 delete data.renderer.bufferBase64;
 data.renderer.buffer={file:basename(out)+'.riv',bytes:bytes.length,sha256:createHash('sha256').update(bytes).digest('hex')};
}
data.frames=data.frames.map((frame,i)=>{
 if(!frame.data.startsWith('data:image/png;base64,'))throw Error('Source canvas is not exportable PNG');
 const bytes=Buffer.from(frame.data.split(',')[1],'base64'),name=basename(out)+'-buffer-'+String(i).padStart(2,'0')+'.png';
 writeFileSync(resolve(dirname(out),name),bytes,{flag:'wx'});
 return {at:frame.at,file:name,bytes:bytes.length,sha256:createHash('sha256').update(bytes).digest('hex')};
});
data.drawing_buffer_only=bufferOnly;
data.observed_at=new Date().toISOString();data.source=bufferOnly?'Actual source drawing buffer within requestAnimationFrame; compositor/page screenshots intentionally absent; timing and native fidelity not yet verified':'Actual source drawing buffer, captured within requestAnimationFrame; composited region retained separately; timing and native fidelity not yet verified';
writeFileSync(out+'.json',JSON.stringify(data,null,2)+'\n',{flag:'wx'});
console.log(JSON.stringify({frames:data.frames.length,distinct_hashes:new Set(data.frames.map(f=>f.sha256)).size,canvas:[data.metadata.width,data.metadata.height]}));
