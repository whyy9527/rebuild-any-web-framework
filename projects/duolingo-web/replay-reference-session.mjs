// Replay a captured public reference session and retain actual UI ordering and interludes.
// Initial-list mode follows capture-reference-session.mjs; current-only reads the visible renderer independently.
import {spawnSync} from 'node:child_process';
import {writeFileSync,mkdirSync,existsSync,readdirSync} from 'node:fs';
import {resolve,dirname,basename} from 'node:path';
import {challengeIdentity,uncoveredReplayType} from './reference-challenge-identity.mjs';
import {referenceFrontendSurface} from './reference-frontend-surface.mjs';
import {publicChallenge} from './public-reference-challenge.mjs';
import {renderedChallenge} from './rendered-reference-challenge.mjs';
import {currentFlowDecision,keyboardTranslationValue} from './reference-current-step.mjs';
function arg(name,fallback){const i=process.argv.indexOf(name);return i<0?fallback:process.argv[i+1];}
for(const name of ['--cli','--session','--out'])if(!arg(name))throw Error('Required: --cli PATH --session NAME --out PATH [--start-index N]');
const uiLanguage=arg('--ui-language','en');
if(!['en','zh'].includes(uiLanguage))throw Error('Unsupported UI language: '+uiLanguage);
const labels=uiLanguage==='zh'?{check:'检查',continue:'继续'}:{check:'Check',continue:'Continue'};
const stopBeforeType=arg('--stop-before-type','');
if(stopBeforeType&&!/^[A-Za-z][A-Za-z0-9]*$/.test(stopBeforeType))throw Error('Invalid stop-before type');
const currentOnly=process.argv.includes('--current-only');
const currentSteps=Number(arg('--current-steps','1'));
if(!Number.isSafeInteger(currentSteps)||currentSteps<1||(!currentOnly&&arg('--current-steps')))throw Error('Current steps require current-only and an explicit positive integer step budget');
const start=Number(arg('--start-index','0'));
if(currentOnly&&start!==0)throw Error('Current-only replay cannot resume an initial-session index');
if(!Number.isInteger(start)||start<0)throw Error('Invalid start index');
const output=resolve(arg('--out'));mkdirSync(dirname(output),{recursive:true});
for(const suffix of ['', '.raw.txt'])if(existsSync(output+suffix))throw Error('Replay output already exists; choose a fresh output before any source action');
const screenshotPrefix=arg('--screenshot-prefix','reference-session');
const absolutePrefix=resolve('artifacts/output/playwright',screenshotPrefix);
if(existsSync(dirname(absolutePrefix))&&readdirSync(dirname(absolutePrefix)).some(n=>n.startsWith(basename(absolutePrefix)+'-')))
 throw Error('Replay screenshots already exist; choose a fresh prefix before any source action');
const callback = async page => {
 const labels=UI_LABELS;
 const frontendSurface=FRONTEND_SURFACE;
 const identity=CHALLENGE_IDENTITY;
 const uncovered=UNCOVERED_TYPE;
 const currentOnly=CURRENT_ONLY;
 const publicOnly=PUBLIC_CHALLENGE;
 const readRendered=READ_RENDERED;
 const flowDecision=FLOW_DECISION;
 const keyboardValue=KEYBOARD_VALUE;
 const currentNode=page.locator('[data-test~="challenge"]');
 const session=currentOnly?{source:'Current rendered challenges; no initial-session or future-sequence read',challenges:[]}:await page.evaluate(()=>window.__referenceSession);
 if(currentOnly)await page.evaluate(()=>{
  if(window.__referenceMediaInstalled)return;
  window.__referenceMediaInstalled=true;window.__referenceMedia=[];
  const play=HTMLMediaElement.prototype.play;
  HTMLMediaElement.prototype.play=function(...args){window.__referenceMedia.push({src:this.currentSrc||this.src,at:performance.now(),muted:this.muted,volume:this.volume});return play.apply(this,args)};
 });
 const observed=[],interludes=[];let failure=null,stopped=null;
 let currentMediaCursor=currentOnly?await page.evaluate(()=>window.__referenceMedia.length):0;
 async function exactVisible(locator,text){
   const labels=await locator.allTextContents();
   const indices=labels.flatMap((label,i)=>label.trim().replace(/^\d\s*|\s*\d$/g,'').trim()===text?[i]:[]);
   if(indices.length!==1)throw new Error('Reference option not unique: '+text+' labels='+JSON.stringify(labels));
   await locator.nth(indices[0]).click();
 }
 async function clickWord(bank,text){
   const matches=bank.getByRole('button',{name:text,exact:true});
   for(let i=0;i<await matches.count();i++){
    const button=matches.nth(i);
    if(await button.isVisible() && await button.isEnabled()) { await button.click(); return i; }
   }
   throw new Error('No available occurrence of word: '+text);
 }
 const records=currentOnly?Array.from({length:CURRENT_STEPS},(_,index)=>({index})):session.challenges.filter(row=>row.index>=START_INDEX);
 for(const record of records){
  let c=record.content;const row={index:record.index,actions:[]};
  try{
   if(currentOnly){
    await page.waitForFunction(labels=>{
     const nodes=[...document.querySelectorAll('[data-test~="challenge"]')].filter(n=>n.checkVisibility());
     const next=document.querySelector('[data-test="player-next"]');
     return (!['/practice','/lesson'].includes(location.pathname)&&!/^\/lesson\/(?:unit|section)\/[1-9]\d*\/test$/.test(location.pathname))||(nodes.length===1&&next?.textContent.trim()===labels.check)||(nodes.length===0&&next?.textContent.trim()===labels.continue)||(nodes.length===0&&[...document.querySelectorAll('button')].some(b=>b.checkVisibility()&&b.innerText.trim()==='开始挑战 +20 经验'));
    },labels,{timeout:15000});
    const facts=await page.evaluate(labels=>{
     const nodes=[...document.querySelectorAll('[data-test~="challenge"]')].filter(n=>n.checkVisibility());
     const buttons=[...document.querySelectorAll('button')].filter(n=>n.checkVisibility()&&n.innerText.trim()===labels.continue);
     const entries=[...document.querySelectorAll('button')].filter(n=>n.checkVisibility()&&n.innerText.trim()==='开始挑战 +20 经验');
     const visible=selector=>[...document.querySelectorAll(selector)].filter(n=>n.checkVisibility());
     return {progress_count:visible('[role=progressbar]').length,quit_count:visible('[data-test=quit-button]').length,duo_count:visible('[data-test=session-duo]').length,encouragement_messages:visible('._36bu_').map(n=>n.innerText.trim()).filter(Boolean),review_entry_count:entries.length,review_entry_enabled:entries.length===1&&!entries[0].disabled&&entries[0].getAttribute('aria-disabled')!=='true',path:location.pathname,challenge_count:nodes.length,challenge_visible:nodes.length===1,
      heading_count:[...document.querySelectorAll('h1')].filter(n=>n.checkVisibility()).length,
      dialog_count:[...document.querySelectorAll('[role="dialog"]')].filter(n=>n.checkVisibility()).length,
      quit_confirmation_count:visible('button').filter(n=>n.innerText.trim()==='继续努力').length,
      next_text:document.querySelector('[data-test="player-next"]')?.textContent.trim(),
      continue_count:buttons.length,continue_enabled:buttons.length===1&&!buttons[0].disabled&&buttons[0].getAttribute('aria-disabled')!=='true',body_text:document.body.innerText};
    },labels);
    const decision=flowDecision(facts,labels);
    if(decision.kind!=='challenge'){
     const receipt={index:record.index,facts,decision,snapshot:await page.locator('body').ariaSnapshot(),screenshot:SCREENSHOT_PREFIX+'-interlude-'+record.index+'.png'};
     await page.screenshot({path:receipt.screenshot});
     if(!['interlude','review_entry'].includes(decision.kind)){stopped={kind:'uncovered_state',...receipt};break;}
     await page.getByRole('button',{name:decision.kind==='review_entry'?decision.text:labels.continue,exact:true}).click();
     receipt.action=decision.kind==='review_entry'?'Actual observed level-review Start challenge':'Actual observed introduction Continue';interludes.push(receipt);continue;
    }
    const live=await currentNode.evaluate(readRendered,publicOnly.toString());
    c=live.content;record.content=c;session.challenges.push({...record,current_observation:live});
   }else{
   for(let transition=0;transition<6;transition++){
    await page.waitForFunction(labels=>{const n=document.querySelectorAll('[data-test="challenge-header"]').length,b=document.querySelector('[data-test="player-next"]');return b&&((n===1&&document.querySelectorAll('[data-test~="challenge"]').length===1&&b.textContent.trim()===labels.check)||(n===0&&b.textContent.trim()===labels.continue));},labels);
    if(await page.getByRole('heading',{level:1}).count()===1)break;
    interludes.push({before_index:record.index,snapshot:await page.locator('body').ariaSnapshot()});
    await page.getByRole('button',{name:labels.continue,exact:true}).click();
   }
   }
   row.type=c.type;observed.push(row);
   await page.getByRole('heading',{level:1}).waitFor();
   row.before=await page.locator('body').ariaSnapshot();
   row.heading=await page.getByRole('heading',{level:1}).textContent();
   row.dom_type=await page.locator('[data-test~="challenge"]').getAttribute('data-test');
   row.images=await page.locator('[data-test~="challenge"] img').evaluateAll(ns=>ns.map(n=>({alt:n.alt,src:n.currentSrc||n.src})));
   row.media_before=currentOnly?await page.evaluate(start=>window.__referenceMedia.slice(start),currentMediaCursor):await page.evaluate(()=>window.__referenceMedia.slice());
   row.frontend_before=await page.evaluate(frontendSurface);
   row.screenshot_before=SCREENSHOT_PREFIX+'-question-'+record.index+'-before.png';
   await page.screenshot({path:row.screenshot_before});
   row.canvases=[];
   const canvases=page.locator('[data-test~="challenge"] canvas');
   for(let j=0;j<await canvases.count();j++){
    const canvas=canvases.nth(j),frame=SCREENSHOT_PREFIX+'-question-'+record.index+'-canvas-'+j+'.png';
    row.canvases.push({source_frame:frame,rect:await canvas.boundingBox(),pixels:await canvas.evaluate(n=>[n.width,n.height])});
    await canvas.screenshot({path:frame,omitBackground:true});
   }
   const mediaStart=await page.evaluate(()=>window.__referenceMedia.length);
   const challenge=page.locator('[data-test~="challenge"]');
   const radioTexts=await challenge.getByRole('radio').allTextContents();
   const bank=challenge.locator('[data-test="word-bank"]');
   const bankTexts=await bank.getByRole('button').allTextContents();
   const buttons=await challenge.getByRole('button').allTextContents();
   let visibleChoices=c.type==='listenMatch' ? await challenge.locator('[data-test="challenge-tap-token-text"]').allTextContents()
    : radioTexts.length ? radioTexts.map(t=>t.trim().replace(/^\d\s*|\s*\d$/g,'').trim()) : bankTexts.length ? bankTexts : buttons.filter(t=>t.trim()&&! [labels.check,labels.continue,'跳过','Skip','使用键盘','Use keyboard'].includes(t.trim()));
   const prompts=await challenge.locator('[data-test=hint-token]').evaluateAll(ns=>[...new Set(ns.map(n=>n.parentElement.innerText.trim()).filter(Boolean))]);
   const completionScaffold=c.type==='orderTapComplete'?await challenge.evaluate(n=>{
    const selector='[aria-label="Selected gap"],[aria-label="Click to select this gap"]';
    const gaps=[...n.querySelectorAll(selector)].filter(g=>g.checkVisibility({checkOpacity:true,checkVisibilityCSS:true}));
    if(!gaps.length||!gaps.every(g=>g.parentElement===gaps[0].parentElement))return null;
    const parent=gaps[0].parentElement;
    const text=[...parent.children].filter(v=>!v.matches(selector)&&!v.matches('[data-test="word-bank"]')&&!v.querySelector('[data-test="word-bank"]')).map(v=>v.innerText).join('');
    return {text,blankCount:gaps.length,source:'Actual visible gap parent children excluding gaps and word bank'};
   }):null;

   if(!prompts.length && c.type==='select'){const quoted=row.heading.match(/[“「](.+?)[”」]/);if(quoted)prompts.push(quoted[1]);}
   const playedAudio=[];
   if(!row.dom_type.split(/\s+/).includes('challenge-'+c.type)){
    row.identity=identity(c,{type:row.dom_type,text:await challenge.innerText(),choices:visibleChoices,prompts,playedAudio,completionScaffold});
    row.divergence={kind:'type_changed',next_action:'Observe the inserted or replacement challenge before any type-specific interaction.'};
    throw Error('Reference UI diverged: type_changed');
   }
   if(c.type===STOP_BEFORE_TYPE){stopped={index:record.index,type:c.type,reason:'Requested exploration boundary; current type observed, no answer submitted'};break;}
   if(c.type==='listenIsolation'){
    const radios=challenge.getByRole('radio');
    if(await radios.count()!==c.options.length)throw Error('Audio option count differs');
    row.audio_options=[];visibleChoices=[];
    for(let j=0;j<c.options.length;j++){
     const start=await page.evaluate(()=>window.__referenceMedia.length);
     await radios.nth(j).click();
     await page.waitForFunction(start=>window.__referenceMedia.slice(start).some(m=>m.src.startsWith('https://d1vq87e9lcf771.cloudfront.net/')),start);
     const urls=await page.evaluate(start=>[...new Set(window.__referenceMedia.slice(start).map(m=>m.src).filter(u=>u.startsWith('https://d1vq87e9lcf771.cloudfront.net/')))],start);
     const options=c.options.filter(o=>urls.includes(o.tts));if(options.length!==1)throw Error('Audio option identity is not unique');
     visibleChoices.push(options[0].text);row.audio_options.push({index:j,text:options[0].text,played_audio:urls,rect:await radios.nth(j).boundingBox()});
    }
   }
   if(['listenTap','listen','listenComplete'].includes(c.type)){
    // Observed normal-speaker SVG, independently inspected on the real source.
    const speaker=challenge.getByRole('button').filter({has:page.locator('svg[viewBox="0 0 94 73"]')});
    const playbackStart=await page.evaluate(()=>window.__referenceMedia.length);
    await speaker.click();
    await page.waitForFunction(start=>window.__referenceMedia.slice(start).some(m=>m.src.startsWith('https://d1vq87e9lcf771.cloudfront.net/')),playbackStart);
    row.identity_playback=await page.evaluate(start=>window.__referenceMedia.slice(start),playbackStart);
    playedAudio.push(...new Set(row.identity_playback.map(m=>m.src).filter(Boolean)));
   }
   if(uncovered(c.type,row.dom_type)){
    row.coverage={kind:'uncovered_type',expected_type:c.type,actual_type:row.dom_type,next_action:'Observe and implement this type; do not classify an unsupported choice schema as source content drift.'};
    throw new Error('Uncovered type: '+c.type);
   }
   row.identity=identity(c,{type:row.dom_type,text:await challenge.innerText(),choices:visibleChoices,prompts,playedAudio,completionScaffold});
   row.dom_fields=await challenge.locator('[data-test]').evaluateAll(ns=>ns.map(n=>({test:n.getAttribute('data-test'),text:n.textContent})));
   if(!row.identity.matches){row.divergence={kind:row.identity.reasons.includes('type_changed')?'type_changed':'same_type_content_changed',next_action:'Read current prompt and complete choice set; do not reuse captured answer. Record new observed branch before resuming.'};throw new Error('Reference UI diverged: '+row.identity.reasons.join(', '));}
   if(['listen','listenComplete'].includes(c.type)){
    const input=challenge.getByRole('textbox');if(await input.count()!==1||!await input.isEnabled())throw Error('Expected one enabled source text field');
    const value=c.type==='listen' ? c.prompt : c.displayTokens.filter(t=>t.isBlank).map(t=>t.text).join('');
    if(!value)throw Error('Missing text solution');
    row.text_input={value,label:await input.getAttribute('placeholder'),rect:await input.boundingBox()};
    await input.fill(value);row.actions.push({input:value});
    await page.getByRole('button',{name:labels.check,exact:true}).click();
   }else if(c.type==='listenIsolation'){
    const target=row.audio_options.filter(o=>o.text===c.options[c.correctIndex].text);if(target.length!==1)throw Error('Correct audio option not unique');
    await challenge.getByRole('radio').nth(target[0].index).click();row.actions.push({select_audio:target[0]});
    await page.getByRole('button',{name:labels.check,exact:true}).click();
   }else if(['select','assist','dialogue','gapFill'].includes(c.type)){
    const choice=c.choices[c.correctIndex],text=typeof choice==='string'?choice:choice.phrase;
    await exactVisible(page.getByRole('radio'),text);row.actions.push({select:text});
    await page.getByRole('button',{name:labels.check,exact:true}).click();
   }else if(['translate','listenTap','completeReverseTranslation','name'].includes(c.type)){
    const input=challenge.getByRole('textbox');
    const value=keyboardValue(c,{textbox_count:await input.count(),textbox_enabled:await input.count()===1&&await input.isEnabled(),textbox_value:await input.count()===1?await input.inputValue():null,bank_count:bankTexts.length});
    if(value!==null){
     row.text_input={value,label:await input.getAttribute('placeholder'),rect:await input.boundingBox()};
     await input.fill(value);row.actions.push({input:value});
    }else{
    const bank=page.locator('[data-test="word-bank"]');row.word_bank=await bank.getByRole('button').allTextContents();
    for(const index of c.correctIndices){const choice=c.choices[index],text=typeof choice==='string'?choice:choice.text;
     const occurrence=await clickWord(bank,text);row.actions.push({word:text,occurrence});}
    }
    await page.getByRole('button',{name:labels.check,exact:true}).click();
   }else if(['orderTapComplete','tapComplete'].includes(c.type)){
    const groups=[];let current=null;
    for(const token of c.displayTokens){
     if(token.isBlank){if(!current){current=[];groups.push(current);}current.push(token.text);}
     else if(token.text.trim())current=null;
    }
    row.word_bank=await bank.getByRole('button').allTextContents();
    const gaps=challenge.locator('[aria-label="Selected gap"],[aria-label="Click to select this gap"]');
    if(c.type==='orderTapComplete'&&await gaps.count()!==groups.length)throw Error('Actual gap structure changed before answer');
    for(let index=0;index<groups.length;index++){
     if(c.type==='orderTapComplete'){await gaps.nth(index).click();row.actions.push({gap:index});}
     for(const text of groups[index]){const occurrence=await clickWord(bank,text);row.actions.push({word:text,occurrence,gap:index});}
    }
    row.answer_before_check=await challenge.innerText();
    await page.getByRole('button',{name:labels.check,exact:true}).click();
   }else if(c.type==='listenMatch'){
    const left=challenge.getByRole('button').filter({hasNot:page.locator('[data-test="challenge-tap-token-text"]')});
    const right=challenge.getByRole('button').filter({has:page.locator('[data-test="challenge-tap-token-text"]')});
    if(await left.count()!==c.pairs.length||await right.count()!==c.pairs.length)throw Error('Observed audio columns differ from captured pairs');
    row.right_text=await right.locator('[data-test="challenge-tap-token-text"]').allTextContents();
    row.pair_audio_order=[];row.left_rects=[];row.right_rects=[];
    for(let j=0;j<c.pairs.length;j++){
     row.left_rects.push(await left.nth(j).boundingBox());row.right_rects.push(await right.nth(j).boundingBox());
     const start=await page.evaluate(()=>window.__referenceMedia.length);
     await left.nth(j).click();
     await page.waitForFunction(start=>window.__referenceMedia.slice(start).some(m=>m.src.startsWith('https://d1vq87e9lcf771.cloudfront.net/')),start);
     const urls=await page.evaluate(start=>[...new Set(window.__referenceMedia.slice(start).map(m=>m.src).filter(u=>u.startsWith('https://d1vq87e9lcf771.cloudfront.net/')))],start);
     const matches=c.pairs.filter(p=>urls.includes(p.tts));if(matches.length!==1)throw Error('Actual played audio has no unique pair identity');
     const target=right.filter({hasText:matches[0].translation});if(await target.count()!==1)throw Error('Actual right target not unique');
     await target.click();row.pair_audio_order.push({left_index:j,played_audio:urls,translation:matches[0].translation});
    }
   }else if(c.type==='match'){

    row.button_order=await page.getByRole('button').allTextContents();
    for(const pair of c.pairs){for(const text of [pair.fromToken,pair.learningToken]){await exactVisible(page.getByRole('button'),text);row.actions.push({match:text});}}
   }else throw new Error('Uncovered type: '+c.type);
   await page.getByRole('button',{name:labels.continue,exact:true}).waitFor();
   row.feedback=await page.locator('body').ariaSnapshot();
   row.media=await page.evaluate(start=>window.__referenceMedia.slice(start),mediaStart);
   row.frontend_feedback=await page.evaluate(frontendSurface);
   row.screenshot_feedback=SCREENSHOT_PREFIX+'-question-'+record.index+'-feedback.png';
   await page.screenshot({path:row.screenshot_feedback});
   row.rejected=await page.locator('[data-test~="blame-incorrect"]').count()>0;
   if(row.rejected)throw new Error('Source answer rejected');
   if(currentOnly)currentMediaCursor=await page.evaluate(()=>window.__referenceMedia.length);
   await page.getByRole('button',{name:labels.continue,exact:true}).click();
  }catch(error){failure=String(error);break;}
 }
 return {session,observed,interludes,failure,stopped,answered:observed.filter(r=>r.feedback).length,accepted:observed.filter(r=>r.feedback&&r.rejected===false).length,
  step_budget:currentOnly?CURRENT_STEPS:null,steps_completed:observed.filter(r=>r.feedback).length+interludes.length,
  outcome:failure?'failed':stopped?.kind==='uncovered_state'?'uncovered_current_state':stopped?'stopped_at_requested_boundary':currentOnly?(interludes.length&&!observed.length?'current_interlude_replayed':CURRENT_STEPS===1?'current_challenge_replayed':'current_steps_replayed'):'replayed_captured_records',
  final:await page.locator('body').ariaSnapshot(),limitations:['Actual generated exercise observations; public solutions are not blind exploration evidence. Media invocations are not acoustic output evidence. Unknown result/profile pages are preserved without clicking Continue. Current-mode media_before contains only events since this invocation or the previous feedback; unrelated earlier history is not duplicated.']};
};
const code=callback.toString().replace('FRONTEND_SURFACE',referenceFrontendSurface.toString()).replace('CURRENT_ONLY',JSON.stringify(currentOnly)).replaceAll('CURRENT_STEPS',String(currentSteps)).replace('FLOW_DECISION',currentFlowDecision.toString()).replace('KEYBOARD_VALUE',keyboardTranslationValue.toString()).replace('PUBLIC_CHALLENGE',publicChallenge.toString()).replace('READ_RENDERED',renderedChallenge.toString()).replace('CHALLENGE_IDENTITY',challengeIdentity.toString()).replace('UNCOVERED_TYPE',uncoveredReplayType.toString()).replace('UI_LABELS',JSON.stringify(labels)).replace('START_INDEX',String(start)).replace('STOP_BEFORE_TYPE',JSON.stringify(stopBeforeType)).replaceAll('SCREENSHOT_PREFIX',JSON.stringify(screenshotPrefix));
const result=spawnSync(arg('--cli'),['-s='+arg('--session'),'run-code',code],{cwd:resolve('artifacts/output/playwright'),encoding:'utf8',timeout:300000,maxBuffer:16*1024*1024});
const raw=(result.stdout||'')+(result.stderr||'');writeFileSync(output+'.raw.txt',raw,{flag:'wx'});
if(result.status!==0||!raw.includes('### Result\n'))throw Error('Unavailable replay; raw output retained, inspect current tab before resuming');
const facts=JSON.parse(raw.split('### Result\n')[1].split('\n### Ran')[0]);
writeFileSync(output,JSON.stringify({...facts,observed_at:new Date().toISOString()},null,2)+'\n',{flag:'wx'});
console.log(JSON.stringify({observed:facts.observed.length,interludes:facts.interludes.length,failure:facts.failure,stopped:facts.stopped,answered:facts.answered,accepted:facts.accepted,steps_completed:facts.steps_completed,step_budget:facts.step_budget,outcome:facts.outcome}));
if(facts.failure||facts.stopped?.kind==='uncovered_state')process.exitCode=1;
