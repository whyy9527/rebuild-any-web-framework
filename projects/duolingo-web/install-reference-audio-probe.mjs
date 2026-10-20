// Observe current owned source-page audio invocations; decoded public UI audio is
// distinct from acoustic loopback. Preserve the original receiver, args and result.
import {spawnSync} from 'node:child_process';
import {writeFileSync,existsSync,mkdirSync} from 'node:fs';
import {dirname,resolve} from 'node:path';
function arg(n){const i=process.argv.indexOf(n);if(i<0)throw Error('Required '+n);return process.argv[i+1]}
const out=resolve(arg('--out'));if(existsSync(out))throw Error('Choose fresh probe receipt');mkdirSync(dirname(out),{recursive:true});
const callback=async page=>await page.evaluate(()=>{
 if(location.hostname!=='www.duolingo.com')throw Error('Expected owned reference page');
 if(window.__referenceAudioProbe)return {installed:false,path:location.pathname,reason:'Existing current-page probe retained'};
 const events=[];window.__referenceAudioProbe={events};
 const play=HTMLMediaElement.prototype.play;
 HTMLMediaElement.prototype.play=function(...args){const result=play.apply(this,args);events.push({kind:'html_media_play_invocation',src:this.currentSrc||this.src,at:performance.now(),muted:this.muted,volume:this.volume});return result};
 const start=AudioBufferSourceNode.prototype.start;
 AudioBufferSourceNode.prototype.start=function(...args){
  const result=start.apply(this,args);const b=this.buffer;
  const event={kind:'web_audio_buffer_start_invocation',at:performance.now(),contextTime:this.context.currentTime,scheduledArgs:args,sampleRate:b?.sampleRate,length:b?.length,channels:b?.numberOfChannels,loop:this.loop,playbackRate:this.playbackRate.value};
  if(b){event.pcm=b.length<=b.sampleRate*15?Array.from({length:b.numberOfChannels},(_,i)=>{
    const bytes=new Uint8Array(b.getChannelData(i).slice().buffer);let binary='';for(let n=0;n<bytes.length;n+=0x8000)binary+=String.fromCharCode(...bytes.subarray(n,n+0x8000));return btoa(binary);
   }):null;event.limit=b.length>b.sampleRate*15?'Decoded buffer exceeds15s probe capture budget':null}
  events.push(event);return result;
 };
 return {installed:true,path:location.pathname,types:['HTMLMediaElement.play','AudioBufferSourceNode.start'],limits:['Current-page call invocations and decoded UI buffers only','Not acoustic output, final mixer gain, microphone recording or sound equality','Only buffers up to15s retained; longer starts remain recorded without PCM']};
});
const r=spawnSync(arg('--cli'),['-s='+arg('--session'),'run-code',callback.toString()],{cwd:'artifacts/output/playwright',encoding:'utf8',timeout:60000});writeFileSync(out,r.stdout+r.stderr);if(r.status!==0||!r.stdout.includes('### Result\n'))throw Error('Source probe installation failed; preserve receipt');
process.stdout.write('Current-page audio probe installed/retained; inspect receipt\n');
