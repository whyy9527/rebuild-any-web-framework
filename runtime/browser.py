"""Capture explicit browser actions and facts; frontend owns acceptance."""
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import struct
import time
from urllib.parse import urlsplit
import uuid

from capabilities.rebuild.browser import ARTIFACTS, evidence_problems, observed_state
from capabilities.rebuild.contracts import local_file


SAMPLE = r"""({key, selectors}) => {
  const probe = window[key];
  if (!probe) throw Error('capture document changed');
  const entries = Object.entries(selectors).map(([name, selector]) => {
    const nodes = document.querySelectorAll(selector);
    if (nodes.length > 1) throw Error('ambiguous observed element: ' + name);
    return [name, nodes[0]];
  });
  const identity = el => {
    if (!el) return null;
    const named = entries.filter(([, node]) => node === el).map(([name]) => name);
    return named.length ? {elements: named} : {tag: el.tagName, id: el.id, role: el.getAttribute('role')};
  };
  const role = el => el.getAttribute('role') || ({BUTTON:'button',TEXTAREA:'textbox',SELECT:'combobox'}[el.tagName]) ||
    (el.tagName === 'A' && el.hasAttribute('href') ? 'link' : null) ||
    (el.tagName === 'INPUT' ? ({radio:'radio',checkbox:'checkbox',button:'button',submit:'button',reset:'button',
      range:'slider',number:'spinbutton',search:'searchbox',hidden:null}[el.type] ??
      (el.type === 'hidden' ? null : 'textbox')) : null);
  const elements = Object.fromEntries(entries.map(([name, el]) => {
    if (!el) return [name, null];
    const r = el.getBoundingClientRect();
    const value = {role: role(el), rect:[r.x,r.y,r.width,r.height],
      enabled:!el.matches(':disabled') && !el.closest('[aria-disabled="true"]')};
    if ('value' in el) value.value = el.value;
    if ('checked' in el) value.checked = el.checked;
    return [name, value];
  }));
  return {document: probe.document, revision: probe.revision,
    url: location.href, scroll:[scrollX,scrollY], focus:identity(document.activeElement),
    hover: [...document.querySelectorAll(':hover')].map(identity), elements,
    environment: {viewport:[innerWidth,innerHeight], device_scale:devicePixelRatio,
      locale:navigator.language, timezone:Intl.DateTimeFormat().resolvedOptions().timeZone,
      color_scheme:matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light',
      reduced_motion:matchMedia('(prefers-reduced-motion: reduce)').matches,
      service_worker_controlled:!!navigator.serviceWorker?.controller}};
}"""


def positive(value, name):
    if type(value) not in (int, float) or not math.isfinite(value) or value <= 0:
        raise ValueError('positive finite ' + name + ' required')


def http_url(value):
    if not isinstance(value, str):
        raise ValueError('explicit HTTP(S) URL required')
    url = urlsplit(value)
    if url.scheme not in ('http', 'https') or not url.hostname or url.username or url.password:
        raise ValueError('HTTP(S) URL without embedded credentials required')
    return url


def validate_scenario(scenario):
    if not isinstance(scenario, dict) or type(scenario.get('schema_version')) is not int or scenario['schema_version'] != 1:
        raise ValueError('browser scenario schema_version 1 required')
    if set(scenario) - {'schema_version', 'browser', 'start_url', 'viewport', 'elements', 'steps', 'timeout_ms'}:
        raise ValueError('unknown browser scenario field')
    browser = scenario.get('browser', {})
    if not isinstance(browser, dict):
        raise ValueError('browser object required')
    mode = browser.get('mode')
    if mode == 'launch':
        if set(browser) != {'mode', 'executable'} or not Path(browser['executable']).is_absolute() or not Path(browser['executable']).is_file():
            raise ValueError('launch requires an existing absolute browser executable')
        http_url(scenario.get('start_url'))
    elif mode == 'connect':
        if set(browser) != {'mode', 'endpoint', 'target_url'}:
            raise ValueError('connect requires endpoint and exact target_url')
        url = http_url(browser['endpoint'])
        if url.hostname not in ('127.0.0.1', '::1', 'localhost') or not url.port or url.path not in ('', '/') or url.query or url.fragment:
            raise ValueError('connect requires a loopback CDP origin with explicit port')
        http_url(browser['target_url'])
        if 'start_url' in scenario or 'viewport' in scenario:
            raise ValueError('connect preserves the selected page; use explicit goto/scroll actions')
    else:
        raise ValueError('explicit launch or connect browser mode required')
    if 'viewport' in scenario:
        viewport = scenario['viewport']
        if not isinstance(viewport, dict) or set(viewport) != {'width', 'height'} or any(type(v) is not int or v <= 0 for v in viewport.values()):
            raise ValueError('positive integer viewport width/height required')
    selectors = scenario.get('elements', {})
    if not isinstance(selectors, dict) or any(not isinstance(k, str) or not k or not isinstance(v, str) or not v for k, v in selectors.items()):
        raise ValueError('named element CSS selectors required')
    steps = scenario.get('steps')
    if not isinstance(steps, list) or not steps:
        raise ValueError('nonempty browser steps required')
    positive(scenario.get('timeout_ms', 10000), 'timeout_ms')
    seen = set()
    fields = {'observe': set(), 'click': {'selector'}, 'fill': {'selector', 'value'},
              'press': {'selector', 'key'}, 'hover': {'selector'}, 'scroll': {'x', 'y'}, 'goto': {'url'}}
    for step in steps:
        if not isinstance(step, dict) or set(step) - {'id', 'action', 'ready', 'capture'}:
            raise ValueError('unknown browser step field')
        identifier = step.get('id')
        if not isinstance(identifier, str) or not identifier or identifier in seen:
            raise ValueError('unique nonempty step ids required')
        seen.add(identifier)
        action = step.get('action', {})
        if not isinstance(action, dict):
            raise ValueError('action object required')
        kind = action.get('type')
        if kind not in fields or set(action) != fields[kind] | {'type'}:
            raise ValueError('unsupported action or action fields')
        for field in fields[kind] - {'x', 'y'}:
            if not isinstance(action[field], str) or (field != 'value' and not action[field]):
                raise ValueError('string action ' + field + ' required')
        if kind == 'scroll' and any(type(action[k]) not in (int, float) or not math.isfinite(action[k]) for k in ('x', 'y')):
            raise ValueError('finite scroll coordinates required')
        if kind == 'goto':
            http_url(action['url'])
        ready = step.get('ready', {})
        if not isinstance(ready, dict) or set(ready) != {'selector', 'state'} or not isinstance(ready['selector'], str) or not ready['selector'] or ready['state'] not in ('visible', 'hidden', 'attached', 'detached'):
            raise ValueError('explicit readiness selector and state required')
        selected = step.get('capture', sorted(ARTIFACTS))
        if not isinstance(selected, list) or not selected or any(not isinstance(k, str) for k in selected) or len(set(selected)) != len(selected) or not set(selected) <= ARTIFACTS:
            raise ValueError('nonempty unique supported capture artifacts required')
    return scenario


def write_json(path, value):
    with path.open('x') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write('\n')


def perform(page, action):
    kind = action['type']
    if kind == 'observe':
        return
    if kind == 'scroll':
        page.evaluate('p => window.scrollTo({left:p.x, top:p.y, behavior:"instant"})', action)
    elif kind == 'goto':
        page.goto(action['url'], wait_until='load')
    else:
        locator = page.locator(action['selector'])
        if kind == 'click': locator.click()
        elif kind == 'fill': locator.fill(action['value'])
        elif kind == 'press': locator.press(action['key'])
        elif kind == 'hover': locator.hover()


def collect_step(page, root, output, index, step, selectors):
    record = {'schema_version': 1, 'kind': 'browser_step', 'id': step['id'],
              'action': step['action'], 'action_status': 'executed',
              'ready': {**step['ready'], 'status': 'observed'},
              'requested': step.get('capture', sorted(ARTIFACTS)),
              'artifacts': {kind: {'state': 'not_requested'} for kind in ARTIFACTS}}
    key = '__rebuild_capture_' + uuid.uuid4().hex
    arguments = {'key': key, 'selectors': selectors}
    try:
        page.evaluate('key => {const probe = {revision:0, document:key + ":" + performance.timeOrigin}; '
                      'probe.observer = new MutationObserver(() => probe.revision++); '
                      'probe.observer.observe(document,{subtree:true,attributes:true,childList:true,characterData:true}); '
                      'window[key]=probe;}', key)
        # Input dispatch can finish before browser scroll/focus/hover recalculation.
        # Observe two equal preparation samples on successive frames, bounded by
        # the caller's timeout. Changes during artifact reads remain visible.
        sample_function = '(' + SAMPLE + ')'
        page.wait_for_function('args => {const s=' + sample_function + '(args); '
            'const current=JSON.stringify([s.environment,s.scroll,s.focus,s.hover,Object.values(s.elements).map(e=>e?.rect)]); '
            'const p=window[args.key]; const stable=p.preparation===current; p.preparation=current; return stable;}',
            arg=arguments, polling='raf')
        record['before'] = page.evaluate(SAMPLE, arguments)
        for kind in record['requested']:
            try:
                if kind == 'screenshot':
                    data = page.screenshot(type='png', full_page=False, animations='allow', caret='initial')
                    suffix = '.png'
                else:
                    text = (page.content() if kind == 'dom' else page.locator('html').aria_snapshot()
                            if kind == 'accessibility' else page.locator('body').inner_text())
                    data, suffix = text.encode(), '.txt'
                path = output / f'{index:04d}-{kind}{suffix}'
                with path.open('xb') as stream: stream.write(data)
                record['artifacts'][kind] = {'state': 'captured', 'path': path.relative_to(root).as_posix(),
                                            'sha256': hashlib.sha256(data).hexdigest(), 'bytes': len(data)}
                if kind == 'screenshot':
                    record['artifacts'][kind]['pixels'] = list(struct.unpack('>II', data[16:24]))
            except Exception as error:
                record['artifacts'][kind] = {'state': 'unavailable', 'reason': str(error)}
        record['after'] = page.evaluate(SAMPLE, arguments)
    except Exception as error:
        record['capture_error'] = str(error)
    finally:
        try:
            page.evaluate('key => {const probe=window[key]; if(probe) {probe.observer.disconnect(); delete window[key];}}', key)
            record['probe_cleanup'] = 'released'
        except Exception as error:
            record['probe_cleanup'] = 'unavailable'
            record['probe_cleanup_error'] = str(error)
    return record


def capture(root, scenario, out):
    root = Path(root).resolve()
    validate_scenario(scenario)
    output = local_file(root, out, must_exist=False)
    if output.exists():
        raise ValueError('choose a new browser output directory')
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as error:
        raise ValueError('install the browser optional dependency: pip install ".[browser]"') from error
    output.mkdir(parents=True)
    result = {'schema_version': 1, 'kind': 'browser_capture', 'created_at': datetime.now(timezone.utc).isoformat(),
              'mode': scenario['browser']['mode'], 'steps': [], 'states': {}, 'cleanup': 'not_acquired'}
    browser = None
    playwright = None
    started = time.monotonic()
    try:
        playwright = sync_playwright().start()
        try:
            selected = scenario['browser']
            timeout = scenario.get('timeout_ms', 10000)
            if selected['mode'] == 'launch':
                browser = playwright.chromium.launch(executable_path=selected['executable'], headless=True, timeout=timeout)
                context = browser.new_context(viewport=scenario.get('viewport', {'width': 1280, 'height': 720}),
                                              reduced_motion='no-preference', service_workers='allow')
                page = context.new_page()
            else:
                browser = playwright.chromium.connect_over_cdp(selected['endpoint'], timeout=timeout)
                pages = [page for context in browser.contexts for page in context.pages if page.url == selected['target_url']]
                if len(pages) != 1:
                    raise ValueError('target_url must identify exactly one existing page')
                page = pages[0]
            page.set_default_timeout(timeout)
            page.set_default_navigation_timeout(timeout)
            result['browser_version'] = browser.version
            if selected['mode'] == 'launch':
                page.goto(scenario['start_url'], wait_until='load')
            failed = False
            for index, step in enumerate(scenario['steps']):
                step_started = time.monotonic()
                record = {'schema_version': 1, 'kind': 'browser_step', 'id': step['id'], 'action': step['action'],
                          'action_status': 'not_run', 'ready': {**step['ready'], 'status': 'not_run'},
                          'requested': step.get('capture', sorted(ARTIFACTS)), 'artifacts': {}}
                if not failed:
                    try:
                        record['action_status'] = 'attempted'
                        perform(page, step['action'])
                        record['action_status'] = 'executed'
                        page.locator(step['ready']['selector']).wait_for(state=step['ready']['state'])
                        record['ready']['status'] = 'observed'
                        record = collect_step(page, root, output, index, step, scenario.get('elements', {}))
                    except Exception as error:
                        failed = True
                        record['error'] = str(error)
                        if record['action_status'] == 'attempted':
                            record['action_status'] = 'failed'
                        if record['ready']['status'] == 'not_run':
                            record['ready']['status'] = 'unavailable'
                record['elapsed_seconds'] = time.monotonic() - step_started
                record['receipt_path'] = (output / f'{index:04d}-step.json').relative_to(root).as_posix()
                result['steps'].append(record)
        except (Exception, KeyboardInterrupt) as error:
            result['error'] = str(error)
        finally:
            if browser is not None:
                try:
                    # Playwright Browser.close disconnects an attached CDP client.
                    browser.close()
                    result['cleanup'] = 'released'
                except Exception as error:
                    result['cleanup'] = 'failed'
                    result['cleanup_error'] = str(error)
    except (Exception, KeyboardInterrupt) as error:
        result['error'] = str(error)
    finally:
        if playwright is not None:
            try:
                playwright.stop()
            except Exception as error:
                result['cleanup'] = 'failed'
                result['driver_cleanup_error'] = str(error)
    for record in result['steps']:
        record['cleanup'] = result['cleanup']
        write_json(local_file(root, record['receipt_path'], must_exist=False), record)
        result['states'][record['id']] = observed_state(root, record, record['receipt_path'])
    result['elapsed_seconds'] = time.monotonic() - started
    result['status'] = ('captured' if len(result['steps']) == len(scenario['steps']) and result['steps']
                        and not result.get('error') and result['cleanup'] == 'released'
                        and all(not evidence_problems(root, record, record['requested']) for record in result['steps']) else 'incomplete')
    write_json(output / 'observed.json', result)
    return result
