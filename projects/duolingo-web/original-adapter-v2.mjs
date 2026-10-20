// Online UI driver, not a local replica. No expectations are supplied to this process.
import { chromium } from 'playwright';
import { readFileSync } from 'node:fs';

const request = JSON.parse(readFileSync(0, 'utf8'));
const entry = 'https://www.duolingo.com/course/es/en/Learn-Spanish';
const vocabulary = { cat: 'gato', dog: 'perro', water: 'agua', milk: 'leche', mom: 'mamá', dad: 'papá', book: 'libro', house: 'casa', suitcase: 'maleta' };
let browser, page;
const trace = [];

async function snapshot() {
  return page.locator('body').ariaSnapshot();
}

async function openGuest() {
  // Each command owns a fresh browser/context, closed in finally. No saved user session.
  browser = await chromium.launch({ channel: 'chromium', headless: process.env.REBUILD_HEADED !== '1' });
  const context = await browser.newContext({ locale: 'en-US' });
  page = await context.newPage();
  page.setDefaultTimeout(15000);
  await page.goto(entry, { waitUntil: 'domcontentloaded', timeout: 45000 });
  await page.getByRole('button', { name: 'Get started', exact: true }).first().waitFor();
}

async function firstLesson() {
  await page.getByRole('button', { name: 'Get started', exact: true }).first().click();
  await page.getByRole('button', { name: 'Continue', exact: true }).waitFor({ timeout: 30000 });
  for (let stage = 0; stage < 20; stage++) {
    let ready = false, selectedGroup = null;
    const deadline = Date.now() + 30000;
    while (Date.now() < deadline) {
      if (await page.getByRole('button', { name: 'Check', exact: true }).count()) { ready = true; break; }
      for (const name of [/^Other$/, /new to Spanish/, /^5 min.*Casual$/, /^Start from scratch/]) {
        const radio = page.getByRole('radio', { name });
        if (await radio.count() === 1 && await radio.isVisible() && await radio.isEnabled() && !await radio.isChecked()) {
          selectedGroup = await radio.evaluate(el => el.closest('[role="radiogroup"]').getAttribute('aria-label'));
          await radio.click();
          break;
        }
      }
      const block = page.getByRole('button', { name: 'Block', exact: true });
      const next = page.getByRole('button', { name: 'Continue', exact: true }).last();
      if (await block.count() && await block.isVisible() || await next.count() && await next.isEnabled()) { ready = true; break; }
      await page.waitForTimeout(100); // Bounded poll for an actionable state, not an assumed animation delay.
    }
    trace.push({ stage, selected_group: selectedGroup, visible_text: (await page.locator('body').innerText()).slice(0,350) });
    if (!ready) throw new Error('No recognized actionable onboarding state');
    if (await page.getByRole('button', { name: 'Check', exact: true }).count()) {
      await page.getByRole('radio').first().click({ trial: true }); // Loading overlay must actually release interaction.
      return;
    }
    const text = await page.locator('body').innerText();
    const block = page.getByRole('button', { name: 'Block', exact: true });
    if (await block.count() && await block.isVisible()) await block.click();
    else await page.getByRole('button', { name: 'Continue', exact: true }).last().click();
    if (selectedGroup) await page.getByRole('radiogroup', { name: selectedGroup, exact: true }).waitFor({ state: 'hidden', timeout: 30000 });
    else await page.waitForFunction(old => document.body.innerText !== old, text, { timeout: 30000 });
  }
  throw new Error('Onboarding action budget exhausted');
}

let current, firstPrompt, currentLesson = 0;
const learningTrace = [];
const translations = { 'mi maleta': ['my','suitcase'], 'mi casa': ['my','house'], 'mi libro': ['my','book'] };
async function identify() {
  const containers = page.locator('[data-test^="challenge "]');
  for (let i = 0; i < await containers.count(); i++) {
    const c = containers.nth(i);
    const controls = c.getByRole('radio').or(c.getByRole('button'));
    for (let j = 0; j < await controls.count(); j++) if (await controls.nth(j).isVisible() && await controls.nth(j).isEnabled()) return c.elementHandle();
  }
  return null;
}
async function kind() {
  if (!current) return null;
  const data = await current.getAttribute('data-test');
  if (data.includes('challenge-match')) return 'matching';
  if (data.includes('challenge-translate')) return 'word_tiles';
  if (await current.$('[role="radio"]')) return 'choice';
  throw new Error('Unobserved challenge type: ' + data);
}
async function prompt() { return current ? current.$eval('h1', el => el.innerText) : ''; }
async function questionIdentity() {
  const heading=await prompt();
  if(heading==='Select the correct meaning') {
    const lines=(await current.innerText()).split('\n').map(s=>s.trim());
    const word=Object.keys(vocabulary).find(w=>lines.includes(w));
    if(!word)throw new Error('Unobserved meaning prompt identity');
    return heading+': '+word;
  }
  return heading;
}
async function completeScreen() { return await page.getByText('Lesson Complete!', { exact: true }).count() > 0; }
async function settle() {
  const deadline = Date.now() + 20000;
  while (Date.now() < deadline) {
    current = await identify();
    if (current || await completeScreen()) return;
    const next = page.getByRole('button', { name: 'Continue', exact: true }).last();
    if (await next.count() && await next.isVisible() && await next.isEnabled()) {
      const old = await page.locator('body').innerText();
      await next.click();
      await page.waitForFunction(s => document.body.innerText !== s, old, { timeout: 15000 });
    } else await page.waitForTimeout(100);
  }
  throw new Error('No recognized next question or completion screen');
}
async function advance() {
  const old = current;
  await page.getByRole('button', { name: 'Continue', exact: true }).last().click();
  if (old) await old.waitForElementState('hidden', { timeout: 15000 });
  await settle();
}
async function readWords() {
  const tokens = await current.$$eval('[data-test="hint-token"]', es => es.map(e => e.getAttribute('aria-label')));
  const key = tokens.join(' ').trim();
  if (!translations[key]) throw new Error('Unobserved visible translation: ' + key);
  return translations[key];
}
async function selectAnswer(intent) {
  if (!['correct','wrong'].includes(intent)) throw new Error('Unknown semantic answer');
  const heading = await prompt();
  const quoted = heading.match(/[“"]([^”"]+)[”"]/);
  let word = quoted?.[1];
  if (!word && heading === 'Select the correct meaning') {
    const text = await current.innerText();
    word = Object.keys(vocabulary).find(w => text.includes(heading + w) || text.split('\n').some(s => s.trim() === w));
  }
  const answer = vocabulary[word];
  if (!answer) throw new Error('Unobserved choice prompt: ' + heading);
  const options = await current.$$('[role="radio"]');
  let correct = null, wrong = null;
  for (const option of options) {
    const text = (await option.innerText()).replace(/^\s*\d+\s*|\s*\d+\s*$/g,'').trim();
    if (text === answer) correct = option; else wrong ??= option;
  }
  const option = intent === 'correct' ? correct : wrong;
  if (!option) throw new Error('No uniquely mapped option');
  await option.click();
}
async function submit() {
  await page.getByRole('button', { name: 'Check', exact: true }).click();
  await page.getByRole('button', { name: 'Continue', exact: true }).last().waitFor();
  const keep = page.getByRole('button', { name: 'Keep going', exact: true });
  if (await keep.count() && await keep.isVisible()) await keep.click();
}
async function addWord(index) {
  const answer = await readWords();
  const word = answer[index];
  if (!word) throw new Error('Unknown answer token index');
  const bank = await current.$('[data-test="word-bank"]');
  if (!bank) throw new Error('No visible word bank');
  const buttons = await bank.$$('button');
  const choices = [];
  for (const b of buttons) if ((await b.innerText()).trim() === word && await b.isEnabled()) choices.push(b);
  if (choices.length !== 1) throw new Error('Answer token is not uniquely available');
  await choices[0].click();
}
async function removeWord(index) {
  const word = (await readWords())[index];
  // Selection animation can reorder equal-name buttons; bind by the observed
  // enabled state rather than retaining a DOM ordinal from before animation.
  const chosen = page.getByRole('button', { name: word, exact: true }).and(page.locator('button[aria-disabled="false"]'));
  await chosen.click();
  await page.waitForFunction(word => [...document.querySelectorAll('[data-test="word-bank"] button')].some(e=>e.innerText.trim()===word && e.getAttribute('aria-disabled')==='false'), word, {timeout:5000});
}
async function matchRemaining() {
  const buttons = await current.$$('button');
  const words = [];
  for (const b of buttons) if (await b.isEnabled()) words.push((await b.innerText()).replace(/^\d\s*/,'').trim());
  const pairs = words.filter(w=>vocabulary[w] && words.includes(vocabulary[w]));
  if (!pairs.length) throw new Error('No observed matching pairs');
  for (const a of pairs) {
    const b = vocabulary[a];
    const controls = await current.$$('button');
    for (const word of [a,b]) {
      let button = null;
      for (const c of controls) if ((await c.innerText()).replace(/^\d\s*/,'').trim() === word && await c.isEnabled()) button = c;
      if (!button) throw new Error('Matching control unavailable');
      await button.click();
    }
  }
  await page.getByRole('button',{name:'Continue',exact:true}).last().waitFor();
}
async function answerCurrent() {
  const k = await kind();
  if (k === 'choice') { await selectAnswer('correct'); await submit(); }
  else if (k === 'word_tiles') { for(let i=0;i<(await readWords()).length;i++) await addWord(i); await submit(); }
  else if (k === 'matching') await matchRemaining();
  else throw new Error('Cannot automatically answer unobserved type');
  learningTrace.push({kind:k,prompt:await prompt(),feedback:(await snapshot()).includes('Correct solution:')?'incorrect':'positive'});
}
async function finishLesson(stopAtReview=false) {
  for (let i=0;i<35;i++) {
    if (await completeScreen()) return;
    if (stopAtReview && /Previous mistake/.test(await snapshot()) && current) return;
    if (current) {
      if (!await page.getByRole('button',{name:'Continue',exact:true}).count()) await answerCurrent();
      await advance();
    } else await settle();
  }
  throw new Error('Lesson action budget exhausted');
}
async function pathIndex() {
  const buttons = page.getByRole('button',{name:/^Lesson \d+ of \d+$/});
  for(let i=0;i<await buttons.count();i++) { const name=await buttons.nth(i).getAttribute('aria-label');const m=name?.match(/^Lesson (\d+) of/);if(m)return Number(m[1])-1; }
  return null;
}
async function returnToPath() {
  const deadline=Date.now()+90000;
  let clicks=0;
  while(Date.now()<deadline && clicks<18) {
    if (new URL(page.url()).pathname === '/learn' && await pathIndex() !== null) {current=null;return;}
    const later=page.getByRole('button',{name:/^later$/i});
    const next=page.getByRole('button',{name:'Continue',exact:true}).last();
    const text=await page.locator('body').innerText();
    const streak=page.getByRole('button',{name:'I can do it!',exact:true});
    if(await streak.count() && await streak.isVisible()) {
      const goal=page.getByRole('radiogroup',{name:'goal',exact:true}).getByRole('radio',{name:/^7 day streak/});
      if(await goal.count()===1 && await goal.isVisible()) {
        if(!await goal.isChecked()) await goal.click();
        learningTrace.push({stage:'post-lesson-goal',visible_text:await snapshot(),selection:'7 day streak Good'});
        await streak.click();
      } else {
        if(!await streak.isEnabled()) {await page.waitForTimeout(100);continue;}
        const button=await streak.elementHandle();
        try {await button.click({timeout:2000});}
        catch(error) {
          if(!/Timeout|not attached/.test(error.message))throw error;
          learningTrace.push({stage:'post-lesson-transition-reinspect',reason:error.message.split('\n')[0]});
          continue;
        }
      }
    }
    else if(await later.count() && await later.isVisible()) await later.click();
    else if(await next.count() && await next.isVisible() && await next.isEnabled()) await next.click();
    else {await page.waitForTimeout(200);continue;}
    clicks++;
    await page.waitForFunction(s=>document.body.innerText!==s,text,{timeout:15000});
  }
  throw new Error('Unobserved post-lesson path; inspect current UI');
}
async function openPathLesson() {
  const node=page.locator('[data-test="skill-path-level-0 skill-path-level-skill"]');
  await node.click();
  await page.getByRole('link',{name:/^Start.*XP$/i}).click();
  await settle();
  currentLesson = await pathIndex() ?? currentLesson;
}
async function prepare(precondition) {
  current = await identify();
  if (precondition.lesson_index === 1) { await finishLesson();await returnToPath();currentLesson=1;await openPathLesson(); }
  if (precondition.question_kind) {
    for(let i=0;i<45;i++) {
      if(current && await kind()===precondition.question_kind)break;
      if(await completeScreen()){await returnToPath();currentLesson++;await openPathLesson();}
      else {await answerCurrent();await advance();}
      if(i===44)throw new Error('Requested question type not reached within preparation budget');
    }
  }
  firstPrompt = await questionIdentity();
}
async function observe() {
  const raw=await snapshot();
  const check=page.getByRole('button',{name:'Check',exact:true});
  const next=page.getByRole('button',{name:'Continue',exact:true}).last();
  const quit=page.locator('[data-test="quit-button"]');
  const headerLines=await quit.count()?(await quit.locator('..').innerText()).split('\n').map(s=>s.trim()):[];
  const heartLine=headerLines.at(-1);
  const hearts=heartLine && /^\d+$/.test(heartLine)?Number(heartLine):null;
  const k = current ? await kind() : null;
  const radios=current?await current.$$('[role="radio"]'):[];
  const bank=current?await current.$('[data-test="word-bank"]'):null;
  const bankButtons=bank?await bank.$$('button'):[];
  let selected=0,locked=0;
  for(const r of radios){selected+=Number(await r.getAttribute('aria-checked')==='true');locked+=Number(!await r.isEnabled());}
  let selectedWords=0;
  for(const b of bankButtons)selectedWords+=Number(!await b.isEnabled());
  const correction=/Correct solution:/.test(raw);
  const matchingButtons=k==='matching'?await current.$$('button'):[];
  let allMatched=matchingButtons.length>0;
  for(const b of matchingButtons)allMatched=allMatched&&!await b.isEnabled();
  const feedback=correction?'incorrect':await next.count()&&current&&(radios.length>0&&locked===radios.length||k==='word_tiles'&&bankButtons.length>0&&selectedWords>0||allMatched)?'correct':'none';
  const exit=await page.getByRole('button',{name:'End session',exact:true}).count()>0;
  const index=await pathIndex();
  const completed = new URL(page.url()).pathname==='/learn'&&index!==null?index:null;
  return {screen:exit?'exit_confirmation':await completeScreen()?'lesson_complete':completed!==null?'course_path':current?'question':'other',
    authenticated:false,question_kind:k,lesson_index:currentLesson,answer_selected:selected>0||selectedWords>0,
    check_enabled:await check.count()?await check.isEnabled():false,options_locked:radios.length>0&&locked===radios.length||k==='word_tiles'&&feedback!=='none'||allMatched,
    feedback,continue_enabled:await next.count()?await next.isEnabled():false,
    hearts,
    selected_word_count:selectedWords,matching_complete:allMatched,reviewing:/Previous mistake/.test(raw),
    initial_question_revisited:current?(await questionIdentity())===firstPrompt:false,question_changed:current?(await questionIdentity())!==firstPrompt:false,
    completed_lessons:completed,current_lesson_index:completed,ui_snapshot:raw};
}
async function act(action) {
  switch(action.type) {
    case 'inspect':break;
    case 'select':await selectAnswer(action.answer);break;
    case 'submit':await submit();break;
    case 'continue':await advance();break;
    case 'quit':await page.locator('[data-test="quit-button"]').click();await page.getByRole('button',{name:'Keep learning',exact:true}).waitFor();break;
    case 'cancel_quit':await page.getByRole('button',{name:'Keep learning',exact:true}).click();await page.getByRole('button',{name:'End session',exact:true}).waitFor({state:'hidden'});break;
    case 'confirm_quit':await page.getByRole('button',{name:'End session',exact:true}).click();await page.waitForURL('**/learn');current=null;await page.getByRole('button',{name:/^Lesson \d+ of \d+$/}).first().waitFor();break;
    case 'reopen_lesson':await openPathLesson();break;
    case 'add_word':await addWord(action.index);break;
    case 'remove_word':await removeWord(action.index);break;
    case 'fill_words':{const answer=await readWords();const indices=answer.map((_,i)=>i);if(action.order==='reversed')indices.reverse();else if(action.order!=='correct')throw new Error('Unknown token order');for(const i of indices)await addWord(i);break;}
    case 'match_all':await matchRemaining();break;
    case 'finish_main_questions':await finishLesson(true);break;
    case 'finish_lesson':await finishLesson();break;
    case 'return_to_path':await returnToPath();break;
    case 'reload':await page.reload({waitUntil:'domcontentloaded'});await page.getByRole('button',{name:/^Lesson \d+ of \d+$/}).first().waitFor();current=null;break;
    default:throw new Error('Unsupported action: '+action.type);
  }
  return observe();
}
let response;
try {
  if(request.operation==='stop')response={operation:'stop',resources:[]};
  else if(['start','reset','scenario'].includes(request.operation)) {
    await openGuest();
    if(request.operation==='scenario') {
      await firstLesson();await prepare(request.precondition??{});const precondition_state=await observe();const observations=[];
      for(const [step,action] of request.actions.entries())observations.push({step,state:await act(action)});
      response={operation:'scenario',scenario_id:request.scenario_id,precondition_state,observations,onboarding:trace,preparation:learningTrace};
    }else response={operation:request.operation,state:{screen:'course_entry',authenticated:false},reset_scope:'Fresh ephemeral browser context; no remote backend reset'};
  }else throw new Error('Unsupported operation');
}catch(error){response={operation:request.operation,status:'unavailable',reason:error.message.slice(0,8000).replaceAll(process.env.HOME??'\0','<home>'),onboarding:trace,preparation:learningTrace};if(page){response.url=page.url();response.visible_text=await page.locator('body').innerText().catch(()=>'unavailable');response.ui_snapshot=await snapshot().catch(()=>'snapshot unavailable');}}
finally{if(browser)await browser.close();}
console.log('APP_REBUILD_RESULT '+JSON.stringify(response));
