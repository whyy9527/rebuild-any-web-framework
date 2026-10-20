// Observe the actual unlocked home and previously inventoried entries.
// Every click is centrally metered; new destinations are captured, not guessed.
import {spawnSync} from 'node:child_process';
import {existsSync,mkdirSync,writeFileSync} from 'node:fs';
import {resolve} from 'node:path';
const arg=n=>{const i=process.argv.indexOf(n);if(i<0||!process.argv[i+1])throw Error('Required '+n);return process.argv[i+1];};
const cli=arg('--cli'),session=arg('--session'),out=resolve(arg('--out'));
const readOnly=process.argv.includes('--read-sections-layout');
const repair=process.argv.includes('--repair-sections-layout')||readOnly;
const extend=process.argv.includes('--extend-sections')||repair;
if(existsSync(out)&&!extend)throw Error('Fresh output required');if(!extend)mkdirSync(out,{recursive:true});
const ledger=extend?JSON.parse((await import('node:fs')).readFileSync(out+'/actions.json')):{maximum_actions:12,attempts:[]};
if(!extend)writeFileSync(out+'/policy-before-actions.json',JSON.stringify({trigger:'Observed post-placement stage2 home with story/radio and missing native state synchronization',source:'english-sections-v1 exploration-feedback and actual 57-control inventory',plan:['Read actual header/path rendered layout','Open lesson/story/guide/radio entries without starting a new exercise','Record every result and unknown destination; do not assume locked controls are inert'],budget:ledger.maximum_actions,limitations:['Not a matched-budget RSI ablation','Current source is unlocked; no server reset or fixed initial lesson inference']},null,2)+'\n');
function run(code){const r=spawnSync(cli,['-s='+session,'run-code',code],{cwd:resolve('artifacts/output/playwright'),encoding:'utf8',timeout:60000,maxBuffer:12*1024*1024});if(r.status!==0||!r.stdout.includes('### Result\n'))throw Error('Source did not return actual Result: '+(r.stderr||r.stdout).slice(0,500));return JSON.parse(r.stdout.split('### Result\n')[1].split('\n### Ran')[0]);}
function action(name,code){if(ledger.attempts.length>=ledger.maximum_actions)throw Error('Central action budget exhausted');const row={name,status:'attempted',started_at:new Date().toISOString()};ledger.attempts.push(row);writeFileSync(out+'/actions.json',JSON.stringify(ledger,null,2)+'\n');try{row.result=run(code);row.status='observed';}catch(e){row.status='failed';row.failure=String(e);throw e;}finally{writeFileSync(out+'/actions.json',JSON.stringify(ledger,null,2)+'\n');}}
function capture(stem){const r=spawnSync(process.execPath,['projects/duolingo-web/capture-visible-state.mjs','--cli',cli,'--session',session,'--out',out+'/'+stem],{encoding:'utf8',timeout:65000});if(r.status!==0)throw Error(r.stderr||r.stdout);}
if(extend){
 writeFileSync(out+(readOnly?'/sections-layout-readonly-policy.json':repair?'/sections-layout-repair-before-actions.json':'/sections-extension-before-actions.json'),JSON.stringify({trigger:'Need exact unlocked section cards before implementation',remaining_actions:ledger.maximum_actions-ledger.attempts.length,plan:['Open actual section link','Capture all nine current cards','Return by actual Back link']},null,2)+'\n');
 if(!readOnly)action('open unlocked sections',`async page=>{await page.locator('a[href="/sections"]').click();return {path:new URL(page.url()).pathname};}`);capture(readOnly?'unlocked-sections-stable-02':repair?'unlocked-sections-rechecked':'unlocked-sections');
 const data=run(`async page=>{return await page.evaluate(()=>{const rect=n=>{const r=n.getBoundingClientRect();return [r.x,r.y,r.width,r.height];};const css=n=>Object.fromEntries(['backgroundColor','borderColor','borderWidth','borderRadius','color','fontFamily','fontSize','fontWeight','lineHeight','letterSpacing','padding','display'].map(k=>[k,getComputedStyle(n)[k]]));const heads=[...document.querySelectorAll('h1')].filter(n=>/^第[1-8]阶段$/.test(n.innerText.replace(/\\s/g,''))||n.innerText==='每日巩固练习');return {path:location.pathname,viewport:{width:innerWidth,height:innerHeight},cards:heads.map(h=>{let c=h.parentElement;while(c&&!(getComputedStyle(c).display==='grid'&&getComputedStyle(c).borderRadius==='16px'))c=c.parentElement;if(!c)throw Error('Observed grid card missing');return {heading:h.innerText,rect:rect(c),css:css(c),nodes:[...c.querySelectorAll('*')].map(n=>({tag:n.tagName,className:typeof n.className==='string'?n.className:null,text:['H1','BUTTON','P'].includes(n.tagName)?n.innerText:n.children.length===0?n.textContent:null,rect:rect(n),css:css(n),src:n.tagName==='IMG'?n.currentSrc:null,svg:n.tagName==='svg'?n.outerHTML:null}))};})};});}`);
 writeFileSync(out+'/sections-layout-last-attempt.json',JSON.stringify(data,null,2)+'\n');
 if(data.cards.length!==9)throw Error('Incomplete original nine-card inventory');
 writeFileSync(out+(repair?'/sections-layout-corrected.json':'/sections-layout-after.json'),JSON.stringify(data,null,2)+'\n');
 if(!repair)action('return after unlocked sections',`async page=>{await page.getByRole('link',{name:'返回',exact:true}).click();return {path:new URL(page.url()).pathname};}`);if(!repair)capture('unlocked-sections-return');
 console.log(JSON.stringify({actual_actions:ledger.attempts.length,extended:true}));
}else{
run(`async page=>{if(new URL(page.url()).pathname!=='/learn')throw Error('Start at actual home');await page.getByRole('heading',{name:'第 2 阶段，第 1 部分',exact:true}).waitFor();return {ready:true};}`);capture('home-before');
const layout=run(`async page=>{return await page.evaluate(()=>{const rect=n=>{const r=n.getBoundingClientRect();return [r.x,r.y,r.width,r.height];};return {path:location.pathname,observed_at:new Date().toISOString(),viewport:[innerWidth,innerHeight],nodes:[...document.querySelectorAll('[data-test^="skill-path-level-"], [data-test^="skill-path-state-"],h1,h2')].map(n=>({test:n.getAttribute('data-test'),tag:n.tagName,text:n.innerText,rect:rect(n),html:n.outerHTML,css:Object.fromEntries(['color','backgroundColor','borderRadius','boxShadow'].map(k=>[k,getComputedStyle(n)[k]]))})),header:document.querySelector('[data-test="guidebook-button-11"]').parentElement.outerHTML};});}`);
writeFileSync(out+'/path-layout-before.json',JSON.stringify(layout,null,2)+'\n');
const result=`return {path:new URL(page.url()).pathname,snapshot:await page.locator('body').ariaSnapshot()};`;
action('first lesson entry',`async page=>{await page.locator('[data-test="skill-path-level-0 skill-path-level-skill"]').click();${result}}`);capture('lesson-popover');
action('open sections from actual heading',`async page=>{await page.getByRole('heading',{name:'第 2 阶段，第 1 部分',exact:true}).click();${result}}`);capture('sections-after-lesson');
action('return from sections',`async page=>{await page.getByRole('link',{name:'返回',exact:true}).click();${result}}`);capture('lesson-dismiss');
action('first story entry',`async page=>{await page.locator('[data-test="skill-path-level-1 skill-path-level-story"]').click();${result}}`);capture('story-entry');
action('return learning after story',`async page=>{await page.getByRole('link',{name:'学习',exact:true}).click();${result}}`);capture('story-return');
action('actual stage2 guide link',`async page=>{await page.getByRole('link',{name:'打开这个部分的指南',exact:true}).click();${result}}`);capture('guide');
action('return learning after guide',`async page=>{await page.getByRole('link',{name:'学习',exact:true}).click();${result}}`);capture('guide-return');
action('first rendered radio entry',`async page=>{await page.locator('[data-test="skill-path-level-2 skill-path-level-duo_radio"]').click();${result}}`);capture('radio-entry');
action('return learning after radio',`async page=>{await page.getByRole('link',{name:'学习',exact:true}).click();${result}}`);capture('radio-return');
console.log(JSON.stringify({actual_actions:ledger.attempts.length,states:10}));

}
