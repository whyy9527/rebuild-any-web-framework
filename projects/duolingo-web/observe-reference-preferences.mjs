// Collect reference facts for the same geometry/persistence contract as Swift.
import { spawnSync } from 'node:child_process';
import { writeFileSync, mkdirSync } from 'node:fs';
import { dirname, resolve } from 'node:path';

function argument(name) { return process.argv[process.argv.indexOf(name) + 1]; }
if (!['--cli', '--session', '--out'].every(name => process.argv.includes(name))) throw Error('Required: --cli PATH --session NAME --out PATH');
const output = resolve(argument('--out'));
const code = async page => {
  const controls = [['sound-effects','Sound effects'], ['animations','Animations'], ['motivational-messages','Motivational messages'], ['listening-exercises','Listening exercises']];
  const acknowledgements = [];
  async function setSwitch(name, enabled) {
    const button = page.getByRole('button', {name,exact:true});
    if (await button.getAttribute('aria-pressed') === String(enabled)) return;
    const saved = page.waitForResponse(response => {
      const request = response.request(), url = new URL(response.url());
      if (request.method() !== 'PATCH' || url.hostname !== 'www.duolingo.com' || !url.pathname.includes('/users/')) return false;
      if (name === 'Motivational messages') return url.pathname.includes('/containers/learning_app_ui_preferences/users/');
      const field = {'Sound effects':'enableSoundEffects', 'Animations':'animationEnabled', 'Listening exercises':'enableSpeaker'}[name];
      try { return request.postDataJSON()[field] === enabled; } catch { return false; }
    });
    await button.click();
    const response = await saved; await response.finished();
    if (!response.ok()) throw Error('Preference save was not acknowledged: '+name+' HTTP '+response.status());
    const request = response.request(), url = new URL(response.url());
    acknowledgements.push({control:name, status:response.status(), path:url.pathname.replace(/[0-9]{5,}/g, ':id'),
      boolean_fields:Object.fromEntries(Object.entries(request.postDataJSON()).filter(([,value]) => typeof value === 'boolean'))});
  }
  await page.setViewportSize({width:1200,height:732});
  await page.goto('https://www.duolingo.com/settings/account', {waitUntil:'domcontentloaded'});
  await page.getByRole('heading',{name:'Preferences',exact:true}).waitFor();
  for (const [,name] of controls) await setSwitch(name, true);
  await page.getByRole('combobox',{name:'Dark mode',exact:true}).selectOption({label:'System Default'});
  await page.reload({waitUntil:'domcontentloaded'});
  await page.getByRole('heading',{name:'Preferences',exact:true}).waitFor();
  for (const [,name] of controls) {
    if (await page.getByRole('button',{name,exact:true}).getAttribute('aria-pressed') !== 'true') throw Error('Reference initial state not restored: '+name);
  }
  const elements = {};
  for (const [id,name] of controls) elements[id] = await page.getByRole('button',{name,exact:true}).evaluate(element => {
    const rect = element.getBoundingClientRect();
    return {rect:[rect.x,rect.y,rect.width,rect.height], value:element.getAttribute('aria-pressed')};
  });
  const states = {preferences:{accessible_text:(await page.locator('body').innerText()).split('\n').map(text=>text.trim()).filter(Boolean), elements}};
  for (const [,name] of controls) await setSwitch(name, false);
  await page.getByRole('combobox',{name:'Dark mode',exact:true}).selectOption({label:'On'});
  await page.waitForFunction(()=>getComputedStyle(document.body).backgroundColor === 'rgb(19, 31, 36)');
  await page.reload({waitUntil:'domcontentloaded'});
  await page.getByRole('button',{name:'Sound effects',exact:true}).waitFor();
  const interactions = {};
  for (const [id,name] of controls) interactions[id+'-off-persisted'] = await page.getByRole('button',{name,exact:true}).getAttribute('aria-pressed') === 'false';
  interactions['dark-mode-on-persisted'] = await page.getByRole('combobox',{name:'Dark mode',exact:true}).inputValue() === 'on';
  states['preferences-reopened'] = {interactions};
  for (const [,name] of controls) await setSwitch(name, true);
  await page.getByRole('combobox',{name:'Dark mode',exact:true}).selectOption({label:'System Default'});
  return {kind:'actual_reference_preferences_observation', states, acknowledgements,
    actions:'Normalize, measure, toggle off and await save acknowledgement, select On, reload, read actual states, restore defaults',
    limitations:['Lesson effects not exercised; save acknowledgement differs from immediate UI state']};
};
const result = spawnSync(argument('--cli'), ['-s='+argument('--session'), 'run-code', code.toString()], {
  cwd:resolve('artifacts/output/playwright'), encoding:'utf8', timeout:90000, maxBuffer:8*1024*1024
});
mkdirSync(dirname(output), {recursive:true});
const raw = (result.stdout || '') + (result.stderr || '');
writeFileSync(output+'.raw.txt', raw, {flag:'wx'});
if (result.status !== 0 || !raw.includes('### Result\n')) throw Error('Reference observation unavailable; inspect preserved CLI output');
const facts = JSON.parse(raw.split('### Result\n')[1].split('\n### Ran')[0]);
writeFileSync(output, JSON.stringify(facts,null,2)+'\n', {flag:'wx'});
console.log(JSON.stringify({observed:true, acknowledgements:facts.acknowledgements.length}));
