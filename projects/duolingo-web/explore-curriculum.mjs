// Online UI driver, not a local replica. No expectations are supplied to this process.
import { chromium } from 'playwright';
import { writeFileSync, readFileSync } from 'node:fs';

const output=process.argv[2];
if(!output)throw new Error('Explicit output path required');
const entry = 'https://www.duolingo.com/course/es/en/Learn-Spanish';
const knowledge = JSON.parse(readFileSync(new URL('./reference-vocabulary.json', import.meta.url),'utf8'));
const vocabulary = Object.fromEntries(Object.entries(knowledge.entries).map(([english, entry])=>[english,entry.spanish]));
// These five possessives were separately confirmed by the reference matching run.
for(const word of ['dad','house','mom','cat','dog']) vocabulary['my '+word]='mi '+vocabulary[word];
const lessonArgument=process.argv.indexOf('--lessons');
const lessonBudget=lessonArgument<0?1:Number(process.argv[lessonArgument+1]);
if(!Number.isInteger(lessonBudget)||lessonBudget<1)throw Error('Positive explicit lesson budget required');
let browser, page;
const trace = [];

async function snapshot() {
  return page.locator('body').ariaSnapshot();
}

async function openGuest() {
  // Each command owns a fresh browser/context, closed in finally. No saved user session.
  browser = await chromium.launch({ channel: 'msedge', headless: process.env.REBUILD_HEADED !== '1' });
  const context = await browser.newContext({ locale: 'en-US', viewport: {width:1200,height:732} });
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

// Observe complete trajectories instead of selecting a prewritten scenario.
// Unrecognized states preserve the trace and become exploration feedback.
const observed=[];
let result;
try {
 await openGuest(); await firstLesson(); await settle();
 let completions=0;
 for(let lesson=1;lesson<=lessonBudget;lesson++) {
  for(let i=0;i<35;i++) {
   if(await completeScreen()) {completions++;break;}
   const k=await kind();
   const row={lesson,step:i,kind:k,prompt:await questionIdentity(),before:await snapshot(),text:await current.innerText()};
   if(k==='choice' && row.prompt.startsWith('Which one')) row.illustrations=await current.$$eval('[role="radio"]',es=>es.map(e=>({text:e.innerText,backgrounds:[e,...e.querySelectorAll('*')].map(n=>{const style=getComputedStyle(n),r=n.getBoundingClientRect();return {background:style.backgroundImage,size:style.backgroundSize,rect:[r.x,r.y,r.width,r.height]};}).filter(x=>x.background!=='none')})));
   if(k==='word_tiles') row.hints=await page.locator('[data-test="hint-token"]').evaluateAll(es=>es.map(e=>e.getAttribute('aria-label')));
   observed.push(row);
   await answerCurrent();row.feedback=await snapshot();await advance();
  }
  if(!await completeScreen()) throw Error('Per-lesson action budget exhausted');
  if(lesson===lessonBudget) {result={complete:true,completed_lessons:completions,observed,completion:await snapshot(),knowledge};break;}
  // The reference has already acknowledged completion. Continue exploration at
  // the actual next incomplete path node, rather than inventing its content.
  await page.goto('https://www.duolingo.com/learn',{waitUntil:'domcontentloaded'});
  await page.getByRole('button',{name:/Lesson [0-9]+ of [0-9]+/}).first().click();
  await page.getByRole('link',{name:/Start/}).click();await settle();
 }
} catch(error) { result={complete:false,error:String(error),observed,blocked_state:page?await snapshot().catch(()=>null):null,knowledge}; }
finally { await browser?.close(); }
writeFileSync(output,JSON.stringify(result,null,2)+'\n',{flag:'wx'});
console.log(JSON.stringify({complete:result.complete,questions:observed.length,error:result.error}));
