"""Opt-in public CLI checks against a source-owned HTTP site and real Chromium."""
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import importlib.util
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import threading
import time
import unittest

from capabilities.rebuild.frontend import compare


SITE = '''<!doctype html><html><head><style>
body{margin:0;font:16px sans-serif} #spacer{height:900px}
#controls{position:fixed;top:0;left:0;z-index:2;background:white}
#motion{margin-top:90px;width:30px;height:30px;background:red;transition:transform 60s linear}
#motion.go{transform:translateX(300px)} #hover:hover{background:blue}
</style></head><body><div id="controls">
<button id="search">Search</button><div id="result" data-version="old">Old result</div>
<input id="input" value="initial"><button id="hover">Hover</button>
<button id="drift">Drift</button><button id="font">Load font</button>
<button id="animate">Animate</button><input id="motion-state" value="idle">
<button id="register">Register worker</button><input id="worker-state" value="idle">
</div><div id="motion"></div><div id="spacer"></div><p id="bottom">Bottom</p>
<script>
search.onclick=()=>{result.dataset.version='loading';setTimeout(()=>{result.textContent=location.search ? 'Wrong result' : 'New result';result.dataset.version='new'},150)};
drift.onclick=()=>{setInterval(()=>{result.textContent=String(performance.now())},5)};
font.onclick=()=>{const s=document.createElement('style');s.textContent="@font-face{font-family:slow;src:url('/font')}body{font-family:slow}";document.head.append(s)};
animate.onclick=()=>{document.querySelector('#motion-state').value='running';motion.classList.add('go')};
motion.ontransitionend=()=>{document.querySelector('#motion-state').value='ended'};
register.onclick=async()=>{await navigator.serviceWorker.register('/sw.js');await navigator.serviceWorker.ready;
 const mark=()=>{if(navigator.serviceWorker.controller){document.querySelector('#worker-state').dataset.ready='yes'}};
 navigator.serviceWorker.addEventListener('controllerchange',mark);mark()};
</script></body></html>'''


class SiteHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/font':
            time.sleep(3)
        data = ("self.addEventListener('install',()=>self.skipWaiting());"
                "self.addEventListener('activate',e=>e.waitUntil(clients.claim()));").encode() if self.path == '/sw.js' else SITE.encode()
        self.send_response(200)
        self.send_header('Content-Type', 'text/javascript' if self.path == '/sw.js' else 'text/html; charset=utf-8')
        self.send_header('Content-Length', str(len(data)))
        self.end_headers()
        try: self.wfile.write(data)
        except (BrokenPipeError, ConnectionResetError): pass

    def log_message(self, *args):
        pass


EXECUTABLE = os.environ.get('REBUILD_BROWSER_EXECUTABLE')
AVAILABLE = bool(EXECUTABLE and Path(EXECUTABLE).is_file() and importlib.util.find_spec('playwright'))


@unittest.skipUnless(AVAILABLE, 'set REBUILD_BROWSER_EXECUTABLE and install the browser extra for real-browser verification')
class BrowserLiveTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(('127.0.0.1', 0), SiteHandler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.url = f'http://127.0.0.1:{cls.server.server_port}/'

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join()

    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)

    def scenario(self, steps=None):
        return {'schema_version': 1, 'browser': {'mode': 'launch', 'executable': EXECUTABLE},
                'start_url': self.url, 'viewport': {'width': 800, 'height': 600}, 'timeout_ms': 3000,
                'elements': {'input': '#input', 'motion-state': '#motion-state', 'hover': '#hover'},
                'steps': steps or [{'id': 'result', 'action': {'type': 'click', 'selector': '#search'},
                                   'ready': {'selector': '#result[data-version="new"]', 'state': 'visible'}}]}

    def run_cli(self, scenario, name):
        (self.root / (name + '.json')).write_text(json.dumps(scenario))
        completed = subprocess.run([sys.executable, '-m', 'workflows.rebuild.browser', '--workspace', str(self.root),
                                    '--scenario', name + '.json', '--out', name], capture_output=True, text=True, timeout=30)
        self.assertIn(completed.returncode, (0, 1), completed.stdout + completed.stderr)
        result = json.loads((self.root / name / 'observed.json').read_text())
        return completed, result

    def guarded_requirement(self, reference, kind='accessible_text'):
        row = {'id': 'result', 'state': 'result', 'kind': kind, 'text': 'New result',
               'evidence': [reference['steps'][0]['receipt_path']],
               'browser_capture': {'reference': reference['steps'][0]['receipt_path'], 'required': ['dom', 'text', 'screenshot']}}
        if kind == 'image_pixels':
            row.update(reference_image=reference['states']['result']['capture']['path'], pixels=[800, 600],
                       reference_capture=reference['states']['result']['capture'])
        return row

    def test_delayed_result_cli_shared_mold_and_wrong_candidate(self):
        first, reference = self.run_cli(self.scenario(), 'reference')
        second, candidate = self.run_cli(self.scenario(), 'candidate')
        self.assertEqual((first.returncode, second.returncode), (0, 0))
        contract = {'requirements': [self.guarded_requirement(reference), self.guarded_requirement(reference, 'image_pixels')]}
        contract['requirements'][1]['id'] = 'image'
        self.assertEqual(compare(self.root, contract, candidate)['status'], 'pass')
        wrong = self.scenario()
        wrong['start_url'] += '?wrong=1'
        _, observed = self.run_cli(wrong, 'wrong')
        report = compare(self.root, contract, observed)
        self.assertEqual([row['status'] for row in report['rows']], ['fail', 'fail'])
        image = self.root / candidate['states']['result']['capture']['path']
        image.unlink()
        self.assertTrue(all(row['status'] == 'unavailable' for row in compare(self.root, contract, candidate)['rows']))

    def test_ready_timeout_keeps_later_actions_not_run(self):
        scenario = self.scenario()
        scenario['timeout_ms'] = 400
        scenario['steps'][0]['ready']['selector'] = '#never'
        scenario['steps'].append({'id': 'later', 'action': {'type': 'fill', 'selector': '#input', 'value': 'changed'},
                                  'ready': {'selector': '#input', 'state': 'visible'}})
        completed, result = self.run_cli(scenario, 'timeout')
        self.assertEqual(completed.returncode, 1)
        self.assertEqual([r['action_status'] for r in result['steps']], ['executed', 'not_run'])
        self.assertEqual(result['cleanup'], 'released')

    def test_dom_changes_during_capture_remain_incomparable(self):
        scenario = self.scenario([{'id': 'result', 'action': {'type': 'click', 'selector': '#drift'},
                                   'ready': {'selector': 'body', 'state': 'visible'}}])
        completed, result = self.run_cli(scenario, 'drift')
        self.assertEqual(completed.returncode, 1)
        self.assertNotEqual(result['steps'][0]['before'], result['steps'][0]['after'])

    def test_text_is_retained_when_screenshot_waits_for_unavailable_font(self):
        scenario = self.scenario([{'id': 'result', 'action': {'type': 'click', 'selector': '#font'},
                                   'ready': {'selector': 'body', 'state': 'visible'}}])
        scenario['timeout_ms'] = 500
        completed, result = self.run_cli(scenario, 'font')
        self.assertEqual(completed.returncode, 1)
        artifacts = result['steps'][0]['artifacts']
        self.assertEqual(artifacts['screenshot']['state'], 'unavailable')
        self.assertEqual(artifacts['text']['state'], 'captured')

    def test_motion_is_not_fast_forwarded_and_inputs_modes_are_observed(self):
        actions = [('motion', {'type': 'click', 'selector': '#animate'}),
                   ('fill', {'type': 'fill', 'selector': '#input', 'value': 'changed'}),
                   ('press', {'type': 'press', 'selector': '#input', 'key': 'End'}),
                   ('hover', {'type': 'hover', 'selector': '#hover'}),
                   ('scroll', {'type': 'scroll', 'x': 0, 'y': 500})]
        scenario = self.scenario([{'id': name, 'action': action, 'ready': {'selector': 'body', 'state': 'visible'}}
                                  for name, action in actions])
        completed, result = self.run_cli(scenario, 'modes')
        self.assertEqual(completed.returncode, 0, json.dumps(result))
        samples = {r['id']: r['after'] for r in result['steps']}
        self.assertEqual(samples['motion']['elements']['motion-state']['value'], 'running')
        self.assertFalse(samples['motion']['environment']['reduced_motion'])
        self.assertEqual(samples['fill']['elements']['input']['value'], 'changed')
        self.assertEqual(samples['press']['focus'], {'elements': ['input']})
        self.assertIn({'elements': ['hover']}, samples['hover']['hover'])
        self.assertEqual(samples['scroll']['scroll'][0], 0)
        self.assertGreater(samples['scroll']['scroll'][1], 0)
        self.assertLess(samples['scroll']['scroll'][1], 500)  # The short page clamps the actual scroll.
        requirement = {'id': 'value', 'state': 'fill', 'kind': 'element_value', 'element': 'input',
                       'value': 'changed', 'evidence': [result['steps'][1]['receipt_path']],
                       'browser_capture': {'reference': result['steps'][1]['receipt_path'], 'required': ['dom']}}
        contract = {'requirements': [requirement]}
        self.assertEqual(compare(self.root, contract, result)['status'], 'pass')
        result['states']['fill']['elements']['input']['value'] = 'fabricated'
        self.assertEqual(compare(self.root, contract, result)['rows'][0]['status'], 'unavailable')

    def test_service_worker_is_allowed_and_reported(self):
        scenario = self.scenario([{'id': 'worker', 'action': {'type': 'click', 'selector': '#register'},
                                  'ready': {'selector': '#worker-state[data-ready="yes"]', 'state': 'visible'}}])
        completed, result = self.run_cli(scenario, 'worker')
        self.assertEqual(completed.returncode, 0, json.dumps(result))
        self.assertTrue(result['steps'][0]['after']['environment']['service_worker_controlled'])

    @contextmanager
    def external_browser(self):
        profile = self.root / 'external-profile'
        process = subprocess.Popen([EXECUTABLE, '--headless=new', '--remote-debugging-port=0',
                                    '--user-data-dir=' + str(profile), '--no-first-run', '--no-default-browser-check',
                                    self.url], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
        try:
            port_file = profile / 'DevToolsActivePort'
            deadline = time.monotonic() + 10
            while not port_file.exists() and time.monotonic() < deadline and process.poll() is None:
                time.sleep(.05)
            self.assertTrue(port_file.exists(), 'owned external-browser fixture failed to start')
            port = int(port_file.read_text().splitlines()[0])
            yield process, f'http://127.0.0.1:{port}'
        finally:
            if process.poll() is None:
                os.killpg(process.pid, signal.SIGTERM)
                try: process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    os.killpg(process.pid, signal.SIGKILL)
                    process.wait()

    def test_connect_keeps_external_browser_alive_and_releases_probe(self):
        from playwright.sync_api import sync_playwright
        with self.external_browser() as (process, endpoint):
            scenario = self.scenario()
            scenario['browser'] = {'mode': 'connect', 'endpoint': endpoint, 'target_url': self.url}
            scenario.pop('start_url')
            scenario.pop('viewport')
            completed, result = self.run_cli(scenario, 'connected')
            self.assertEqual(completed.returncode, 0, json.dumps(result))
            self.assertIsNone(process.poll())
            with sync_playwright() as playwright:
                browser = playwright.chromium.connect_over_cdp(endpoint)
                page = next(p for c in browser.contexts for p in c.pages if p.url == self.url)
                self.assertEqual(page.locator('#result').inner_text(), 'New result')
                self.assertEqual(page.evaluate('Object.keys(window).filter(k=>k.startsWith("__rebuild_capture_"))'), [])
                browser.close()

    @unittest.skipUnless(os.name == 'posix', 'process-tree cleanup verification uses POSIX ps')
    def test_launch_cli_leaves_no_owned_browser_processes(self):
        scenario = self.scenario()
        (self.root / 'launch.json').write_text(json.dumps(scenario))
        process = subprocess.Popen([sys.executable, '-m', 'workflows.rebuild.browser', '--workspace', str(self.root),
                                    '--scenario', 'launch.json', '--out', 'launch'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        descendants = set()
        try:
            deadline = time.monotonic() + 20
            while process.poll() is None and time.monotonic() < deadline:
                rows = subprocess.check_output(['ps', '-axo', 'pid,ppid'], text=True).splitlines()[1:]
                parents = {int(parts[0]): int(parts[1]) for row in rows if len(parts := row.split()) == 2}
                active = {process.pid}
                while new := {pid for pid, parent in parents.items() if parent in active} - active:
                    active |= new
                descendants |= active - {process.pid}
                time.sleep(.05)
            stdout, stderr = process.communicate(timeout=5)
            self.assertEqual(process.returncode, 0, stdout + stderr)
            self.assertTrue(descendants, 'real driver/browser descendants must have been observed')
            live = {int(row) for row in subprocess.check_output(['ps', '-axo', 'pid'], text=True).splitlines()[1:]}
            self.assertFalse(descendants & live, 'owned browser/driver processes survived CLI cleanup')
        finally:
            if process.poll() is None:
                process.kill()
                process.communicate()
