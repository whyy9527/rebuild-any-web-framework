// Read only the challenge attached to the one actually visible DOM node.
// Initial session order does not identify a post-decline replacement.
import {spawnSync} from 'node:child_process';
import {writeFileSync,mkdirSync,existsSync} from 'node:fs';
import {resolve,dirname,basename} from 'node:path';
import {publicChallenge} from './public-reference-challenge.mjs';
import {renderedChallenge} from './rendered-reference-challenge.mjs';
function arg(name){const i=process.argv.indexOf(name);if(i<0||!process.argv[i+1])throw Error('Required '+name);return process.argv[i+1];}
const output=resolve(arg('--out'));mkdirSync(dirname(output),{recursive:true});
for(const suffix of ['.json','.raw.txt','.png'])if(existsSync(output+suffix))throw Error('Observation output exists; choose a fresh stem before accessing browser');
const callback=async page=>{
 const sanitize=PUBLIC_CHALLENGE;
 const node=page.locator('[data-test~="challenge"]');
 if(await node.count()!==1||!await node.isVisible())throw Error('One visible challenge required; no action executed');
 const before=await page.locator('body').ariaSnapshot();
 const facts=await node.evaluate(READ_RENDERED,sanitize.toString());
 const after=await page.locator('body').ariaSnapshot();
 if(before!==after)throw Error('Visible state changed during observation; no receipt claimed');
 await page.screenshot({path:SCREENSHOT});
 return {observed_at:new Date().toISOString(),path:new URL(page.url()).pathname,viewport:page.viewportSize(),
  snapshot:after,...facts,source:'Current rendered challenge public fields; initial session/future sequence and challengeState not read',
  limitations:['Public content may include grading solutions, not an independent blind exploration score.', 'DOM linkage proves current type/content association, not pixels, actual audio output or an adaptive algorithm.']};
};
const code=callback.toString().replace('PUBLIC_CHALLENGE',publicChallenge.toString()).replace('READ_RENDERED',renderedChallenge.toString()).replace('SCREENSHOT',JSON.stringify(output+'.png'));
const result=spawnSync(arg('--cli'),['-s='+arg('--session'),'run-code',code],{cwd:resolve('artifacts/output/playwright'),encoding:'utf8',timeout:60000,maxBuffer:8*1024*1024});
const raw=(result.stdout||'')+(result.stderr||'');writeFileSync(output+'.raw.txt',raw,{flag:'wx'});
if(result.status!==0||!raw.includes('### Result\n'))throw Error('Current observation unavailable; raw output preserved, no source action executed');
const facts=JSON.parse(raw.split('### Result\n')[1].split('\n### Ran')[0]);
facts.screenshot=basename(output)+'.png';
writeFileSync(output+'.json',JSON.stringify(facts,null,2)+'\n',{flag:'wx'});
console.log(JSON.stringify({observed:true,type:facts.content.type,has_character:!!facts.content.character}));
