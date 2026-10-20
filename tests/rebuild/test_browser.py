from copy import deepcopy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from capabilities.rebuild.browser import evidence_problems
from capabilities.rebuild.frontend import compare
from runtime.browser import capture, validate_scenario


class BrowserEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.artifacts = {}
        for kind, content in {'dom': '<body>Result</body>', 'text': 'Result', 'screenshot': 'fixture-png'}.items():
            path = self.root / (kind + '.txt')
            path.write_text(content)
            self.artifacts[kind] = {'state': 'captured', 'path': path.name,
                                   'bytes': len(path.read_bytes()), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}
        sample = {'environment': {'viewport': [800, 600], 'device_scale': 1, 'locale': 'en-US',
                                 'timezone': 'UTC', 'color_scheme': 'light', 'reduced_motion': False,
                                 'service_worker_controlled': False}, 'scroll': [0, 0], 'focus': None,
                  'hover': [], 'document': 'original', 'revision': 0, 'elements': {}, 'url': 'https://example.test/'}
        self.reference = {'schema_version': 1, 'kind': 'browser_step', 'id': 'result', 'action_status': 'executed',
                          'ready': {'status': 'observed'}, 'cleanup': 'released', 'probe_cleanup': 'released',
                          'requested': ['dom', 'text', 'screenshot'], 'artifacts': self.artifacts,
                          'before': sample, 'after': deepcopy(sample)}
        self.candidate = deepcopy(self.reference)
        self.candidate['before']['document'] = self.candidate['after']['document'] = 'candidate'
        self.requirement = {'id': 'result', 'state': 'result', 'kind': 'accessible_text', 'text': 'Result',
                            'evidence': ['reference.json'],
                            'browser_capture': {'reference': 'reference.json', 'required': ['dom', 'text']}}
        self.state = {'browser_evidence': 'candidate.json', 'accessible_text': ['Result']}

    def result(self):
        (self.root / 'reference.json').write_text(json.dumps(self.reference))
        (self.root / 'candidate.json').write_text(json.dumps(self.candidate))
        return compare(self.root, {'requirements': [self.requirement]}, {'states': {'result': self.state}})['rows'][0]

    def test_actual_text_is_compared_after_evidence_gate(self):
        self.assertEqual(self.result()['status'], 'pass')
        path = self.root / 'wrong.txt'
        path.write_text('Different')
        self.candidate['artifacts']['text'] = {'state': 'captured', 'path': path.name,
            'bytes': len(path.read_bytes()), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}
        self.state['accessible_text'] = ['Different']
        self.assertEqual(self.result()['status'], 'fail')
        self.requirement['text'] = 'Different'
        self.assertEqual(self.result()['status'], 'unavailable')
        self.assertIn('Reference', self.result()['reason'])
        self.requirement['text'] = 'Result'
        self.state['accessible_text'] = ['Result']
        self.assertEqual(self.result()['status'], 'unavailable')

    def test_successful_text_does_not_replace_failed_screenshot(self):
        self.candidate['artifacts']['screenshot'] = {'state': 'unavailable', 'reason': 'capture failed'}
        row = self.result()
        self.assertEqual(row['status'], 'unavailable')
        self.assertIn('screenshot', row['reason'])

    def test_tampered_artifact_and_removed_evidence_are_rejected(self):
        (self.root / 'dom.txt').write_text('tampered')
        self.assertEqual(self.result()['status'], 'unavailable')
        self.state.pop('browser_evidence')
        self.assertEqual(self.result()['status'], 'unavailable')

    def test_not_requested_does_not_mean_absent(self):
        self.candidate['requested'] = ['dom']
        self.candidate['artifacts']['text'] = {'state': 'not_requested'}
        self.assertIn('not_requested', self.result()['reason'])

    def test_unready_action_drift_and_cleanup_cannot_pass(self):
        original = deepcopy(self.candidate)
        changes = [('ready', {'status': 'unavailable'}), ('action_status', 'not_run'),
                   ('cleanup', 'failed'), ('after', {**original['after'], 'revision': 1})]
        for key, value in changes:
            with self.subTest(key=key):
                self.candidate = deepcopy(original)
                self.candidate[key] = value
                self.assertEqual(self.result()['status'], 'unavailable')

    def test_preparation_fields_are_compared_between_sites(self):
        original = deepcopy(self.candidate)
        for key, value in [('environment', {**original['after']['environment'], 'viewport': [801, 600]}), ('scroll', [0, 20]),
                           ('focus', {'elements': ['other']}), ('hover', [{'elements': ['other']}])]:
            with self.subTest(key=key):
                self.candidate = deepcopy(original)
                self.candidate['before'][key] = self.candidate['after'][key] = value
                self.assertIn(key, self.result()['reason'])

    def test_artifact_path_cannot_escape_workspace(self):
        self.candidate['artifacts']['dom']['path'] = '../outside'
        self.assertEqual(self.result()['status'], 'unavailable')

    def test_malformed_state_wrong_identity_and_unsupported_origin_are_rejected(self):
        original = deepcopy(self.candidate)
        self.candidate['id'] = 'other'
        self.assertIn('identity', self.result()['reason'])
        self.candidate = deepcopy(original)
        self.candidate['before'] = self.candidate['after'] = {'environment': {}}
        self.assertEqual(self.result()['status'], 'unavailable')
        self.candidate = deepcopy(original)
        self.candidate['ready'] = []
        self.assertEqual(self.result()['status'], 'unavailable')
        self.candidate = deepcopy(original)
        self.requirement['relative_to_state'] = 'other'
        self.assertEqual(self.result()['status'], 'unavailable')


class BrowserScenarioTests(unittest.TestCase):
    def scenario(self):
        return {'schema_version': 1, 'browser': {'mode': 'connect', 'endpoint': 'http://127.0.0.1:9222',
                                               'target_url': 'https://example.test/'},
                'steps': [{'id': 'entry', 'action': {'type': 'observe'},
                           'ready': {'selector': 'body', 'state': 'visible'}}]}

    def test_requires_exact_target_readiness_and_unique_steps(self):
        scenario = self.scenario()
        self.assertEqual(validate_scenario(scenario), scenario)
        scenario['steps'].append(deepcopy(scenario['steps'][0]))
        with self.assertRaisesRegex(ValueError, 'unique'):
            validate_scenario(scenario)
        scenario = self.scenario()
        scenario['steps'][0].pop('ready')
        with self.assertRaisesRegex(ValueError, 'readiness'):
            validate_scenario(scenario)

    def test_rejects_remote_cdp_and_connected_viewport_override(self):
        for endpoint in ['https://example.test:9222', 'http://127.0.0.1', 'http://user:pass@127.0.0.1:9222']:
            with self.subTest(endpoint=endpoint), self.assertRaises(ValueError):
                scenario = self.scenario()
                scenario['browser']['endpoint'] = endpoint
                validate_scenario(scenario)
        scenario = self.scenario()
        scenario['viewport'] = {'width': 800, 'height': 600}
        with self.assertRaises(ValueError):
            validate_scenario(scenario)

    def test_missing_dependency_and_existing_output_do_not_launch_or_overwrite(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with patch.dict('sys.modules', {'playwright': None}):
                with self.assertRaisesRegex(ValueError, 'optional dependency'):
                    capture(root, self.scenario(), 'new')
            self.assertFalse((root / 'new').exists())
            (root / 'old').mkdir()
            (root / 'old' / 'evidence').write_text('retain')
            with self.assertRaisesRegex(ValueError, 'new browser output'):
                capture(root, self.scenario(), 'old')
            self.assertEqual((root / 'old' / 'evidence').read_text(), 'retain')
