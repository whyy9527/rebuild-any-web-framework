// Online UI driver, not a local replica. No expectations are supplied to this process.
import { chromium } from 'playwright';
import { readFileSync } from 'node:fs';

const request = JSON.parse(readFileSync(0, 'utf8'));
const entry = 'https://www.duolingo.com/course/es/en/Learn-Spanish';
const vocabulary = { cat: 'gato', dog: 'perro', water: 'agua', milk: 'leche', mom: 'mamá', dad: 'papá' };
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
    trace.push({ stage, ui_snapshot: await snapshot() });
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

async function activeChallenge() {
  const radios = page.getByRole('radio');
  for (let i = 0; i < await radios.count(); i++) {
    const radio = radios.nth(i);
    if (await radio.isVisible() && await radio.isEnabled())
      return radio.locator('xpath=ancestor::*[starts-with(@data-test,"challenge ")][1]');
  }
  throw new Error('No active selectable challenge');
}

async function observe() {
  const raw = await snapshot();
  const radios = page.getByRole('radio');
  const count = await radios.count();
  let selected = 0, disabled = 0;
  for (let i = 0; i < count; i++) {
    selected += Number(await radios.nth(i).isChecked());
    disabled += Number(!await radios.nth(i).isEnabled());
  }
  const quit = page.locator('[data-test="quit-button"]');
  const hearts = await quit.count() ? Number((await quit.locator('..').innerText()).trim()) : null;
  const check = page.getByRole('button', { name: 'Check', exact: true });
  const continuing = page.getByRole('button', { name: 'Continue', exact: true });
  const confirming = await page.getByRole('button', { name: 'End session', exact: true }).count() > 0;
  return {
    screen: confirming ? 'exit_confirmation' : count ? 'question' : 'other',
    answer_selected: selected > 0,
    check_enabled: await check.count() ? await check.isEnabled() : false,
    options_locked: count > 0 && disabled === count,
    feedback: /Correct solution:/.test(raw) ? 'incorrect' : await continuing.count() && count && disabled === count ? 'correct' : 'none',
    continue_enabled: await continuing.count() ? await continuing.last().isEnabled() : false,
    hearts,
    ui_snapshot: raw,
  };
}

async function act(action) {
  switch (action.type) {
    case 'inspect': break;
    case 'select': {
      const challenge = await activeChallenge();
      const heading = await challenge.getByRole('heading', { level: 1 }).innerText();
      const word = heading.match(/[“"]([^”"]+)[”"]/);
      const translation = word && vocabulary[word[1]];
      if (!translation) throw new Error('Unobserved question mapping: ' + heading);
      const radios = challenge.getByRole('radio');
      const correct = challenge.getByRole('radio', { name: new RegExp('^' + translation + ' \\d+$') });
      if (await correct.count() !== 1) throw new Error('Observed answer mapping is not uniquely visible');
      if (action.answer === 'correct') await correct.click();
      else if (action.answer === 'wrong') {
        const correctName = await correct.innerText();
        let chosen = false;
        for (let i = 0; i < await radios.count(); i++) {
          if (await radios.nth(i).innerText() !== correctName) { await radios.nth(i).click(); chosen = true; break; }
        }
        if (!chosen) throw new Error('No distinct wrong option');
      } else throw new Error('Unknown semantic answer');
      break;
    }
    case 'submit': {
      await page.getByRole('button', { name: 'Check', exact: true }).click();
      await page.getByRole('button', { name: 'Continue', exact: true }).waitFor();
      const keepGoing = page.getByRole('button', { name: 'Keep going', exact: true });
      if (await keepGoing.count() && await keepGoing.isVisible()) await keepGoing.click();
      break;
    }
    case 'quit': await page.locator('[data-test="quit-button"]').click(); await page.getByRole('button', { name: 'Keep learning', exact: true }).waitFor(); break;
    case 'cancel_quit': await page.getByRole('button', { name: 'Keep learning', exact: true }).click(); await page.getByRole('button', { name: 'End session', exact: true }).waitFor({ state: 'hidden' }); break;
    default: throw new Error('Unsupported action: ' + action.type);
  }
  return observe();
}

let response;
try {
  if (request.operation === 'stop') response = { operation: 'stop', resources: [] };
  else if (['start', 'reset', 'scenario'].includes(request.operation)) {
    await openGuest();
    if (request.operation === 'scenario') {
      await firstLesson();
      const precondition_state = await observe();
      const observations = [];
      for (const [step, action] of request.actions.entries()) observations.push({ step, state: await act(action) });
      response = { operation: 'scenario', scenario_id: request.scenario_id, precondition_state, observations, onboarding: trace };
    } else response = { operation: request.operation, state: { screen: 'course_entry', authenticated: false }, reset_scope: 'fresh ephemeral browser context; does not reset remote service' };
  } else throw new Error('Unsupported operation');
} catch (error) {
  // Keep failed UI evidence; no cookies, network bodies or arbitrary error dumps.
  response = { operation: request.operation, status: 'unavailable', reason: error.message.split('\n')[0], onboarding: trace };
  if (page) response.ui_snapshot = await snapshot().catch(() => 'snapshot unavailable');
} finally {
  if (browser) await browser.close();
}
console.log('APP_REBUILD_RESULT ' + JSON.stringify(response));
