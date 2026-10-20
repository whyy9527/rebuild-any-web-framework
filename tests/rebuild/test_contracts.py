import copy
import json
from pathlib import Path
import sys
import subprocess
import tempfile
import time
import unittest

from capabilities.exploration.storage import digest
from capabilities.rebuild.contracts import coverage, differences, freeze, load, verify

# Explicit test double: its state machine tests the shared assertion/runtime
# contract. This is not browser/native E2E evidence or model-effectiveness data.
DRIVER = '''import importlib, json, sys
request=json.load(sys.stdin)
app=importlib.import_module(sys.argv[1])
operation=request['operation']
response={'operation': operation}
if operation=='reset':
 app.reset(request['fixture']['data'])
 response['state']=app.state()
elif operation=='scenario':
 response['scenario_id']=request['scenario_id']
 response['precondition_state']=app.state()
 response['observations']=[]
 for i,action in enumerate(request['actions']):
  app.act(action)
  response['observations'].append({'step':i,'state':app.state()})
print('APP_REBUILD_RESULT '+json.dumps(response))
'''
APP = '''import json
from pathlib import Path
path=Path('artifacts/state.json')
def reset(data):
 path.parent.mkdir(exist_ok=True)
 path.write_text(json.dumps(data))
def state(): return json.loads(path.read_text())
def act(action):
 value=state()
 if action['type']=='complete': value['completed']=True
 path.write_text(json.dumps(value))
'''


class SharedBusinessContracts(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        (self.root/'driver.py').write_text(DRIVER)
        (self.root/'reference.py').write_text(APP)
        (self.root/'candidate.py').write_text(APP.replace("value['completed']=True", "value['completed']=False"))
        (self.root/'observation.md').write_text('Test fixture, not a real product observation. Completion persists.\n')
        (self.root/'fixture.json').write_text(json.dumps({'data': {'completed': False}, 'initial_state': {'completed': False}}))
        self.spec = {'schema_version': 1, 'revision': 'v1', 'parent_digest': None, 'fixture': 'fixture.json',
                     'source': {'kind': 'local_reference', 'version': 'fixture-v1', 'date': '2026-10-10',
                                'scope': 'test double completion', 'reset_limitations': 'No external account or service'},
                     'behaviors': [
                         {'id': 'complete', 'description': 'Completion persists', 'discovery': 'observed',
                          'evidence': ['observation.md'], 'precondition': {'completed': False},
                          'steps': [{'action': {'type': 'complete'}, 'expect': {'completed': True}}]},
                         {'id': 'exit', 'description': 'Exit behavior not explored', 'discovery': 'unknown'}]}
        self.targets = {'schema_version': 1, 'targets': {
            name: {'kind': 'local_reference' if name == 'reference' else 'candidate', 'layer': 'test_double',
                   'command': [sys.executable, 'driver.py', name], 'acceptance_paths': ['driver.py']}
            for name in ('reference', 'candidate')}}
        self.write()

    def write(self):
        (self.root/'spec.json').write_text(json.dumps(self.spec))
        (self.root/'targets.json').write_text(json.dumps(self.targets))
        return load(self.root, 'spec.json', 'targets.json')

    def test_shared_assertions_detect_candidate_bug_and_accept_real_repair(self):
        contract = self.write()
        reference = verify(self.root, contract, 'reference')
        self.assertEqual(reference['status'], 'pass', reference)
        batch = freeze(contract, reference)
        failed = verify(self.root, contract, 'candidate', frozen=batch)
        self.assertEqual(failed['behaviors'][0]['status'], 'fail')
        self.assertIn('expected True, got False', failed['behaviors'][0]['differences'][0])
        (self.root/'candidate.py').write_text(APP)
        passed = verify(self.root, contract, 'candidate', frozen=batch)
        self.assertEqual(passed['status'], 'pass', passed)
        self.assertEqual(passed['counts']['unknown'], 1)
        self.assertEqual([e['operation'] for e in passed['lifecycle']], ['start', 'reset', 'reset', 'stop'])
        self.assertEqual(json.loads((self.root/'artifacts/state.json').read_text()), {'completed': False})

    def test_coverage_separates_unknown_observed_and_not_run_and_rejects_stale_results(self):
        contract = self.write()
        initial = coverage(contract)
        self.assertEqual(initial['rows'][0]['discovery'], 'observed')
        self.assertEqual(initial['rows'][0]['status'], 'not_run')
        self.assertEqual(initial['rows'][1]['status'], 'unknown')
        receipt = verify(self.root, contract, 'reference')
        self.assertEqual(coverage(contract, receipt)['rows'][0]['status'], 'pass')
        (self.root/'candidate.py').write_text(APP)
        with self.assertRaisesRegex(ValueError, 'stale artifact'):
            coverage(contract, receipt)
        self.spec['revision'] = 'v2'
        with self.assertRaises(ValueError):
            coverage(self.write(), receipt)

    def test_freeze_requires_matching_reference_and_protects_fixtures(self):
        contract = self.write()
        with self.assertRaises(ValueError):
            verify(self.root, contract, 'candidate')
        reference = verify(self.root, contract, 'reference')
        batch = freeze(contract, reference)
        (self.root/'fixture.json').write_text(json.dumps({'data': {'completed': True}, 'initial_state': {'completed': True}}))
        changed = load(self.root, 'spec.json', 'targets.json')
        with self.assertRaises(ValueError):
            verify(self.root, changed, 'candidate', frozen=batch)
        with self.assertRaises(ValueError):
            freeze(changed, reference)

    def test_driver_never_receives_expectations_and_zero_steps_cannot_pass(self):
        (self.root/'driver.py').write_text(DRIVER.replace("operation=request['operation']", "assert 'expect' not in str(request)\noperation=request['operation']"))
        contract = self.write()
        self.assertEqual(verify(self.root, contract, 'reference')['status'], 'pass')
        (self.root/'driver.py').write_text(DRIVER.replace("for i,action in enumerate(request['actions']):", "for i,action in enumerate([]):"))
        contract = self.write()
        result = verify(self.root, contract, 'reference')
        self.assertEqual(result['behaviors'][0]['status'], 'invalid')
        with self.assertRaises(ValueError):
            freeze(contract, result)

    def test_discovery_new_batch_preserves_old_acceptance_and_parent_identity(self):
        contract = self.write()
        first = freeze(contract, verify(self.root, contract, 'reference'))
        self.spec['revision'] = 'v2'
        self.spec['parent_digest'] = digest(first)
        self.spec['behaviors'][1] = {'id': 'exit', 'description': 'Restart keeps completion', 'discovery': 'decision',
                                    'rationale': 'Explicit test case for restart semantics', 'precondition': {},
                                    'steps': [{'action': {'type': 'complete'}, 'expect': {'completed': True}},
                                              {'action': {'type': 'restart'}, 'expect': {'completed': True}}]}
        updated = self.write()
        second = freeze(updated, verify(self.root, updated, 'reference'), parent=first)
        self.assertEqual(second['parent_digest'], digest(first))
        self.assertEqual(len(second['scenario_digests']), 2)
        self.spec['behaviors'][0]['steps'][0]['expect'] = {'completed': False}
        weakened = self.write()
        # Even if a different reference implementation passes a weakened test,
        # an incremental batch may not silently rewrite prior acceptance.
        fake_receipt = copy.deepcopy(verify(self.root, weakened, 'reference'))
        fake_receipt['status'] = 'pass'
        fake_receipt['behaviors'][0]['status'] = 'pass'
        with self.assertRaisesRegex(ValueError, 'remove or weaken'):
            freeze(weakened, fake_receipt, parent=first)

    def test_empty_suite_missing_evidence_and_lying_online_identity_are_rejected(self):
        self.spec['behaviors'] = []
        with self.assertRaises(ValueError): self.write()
        self.setUpFixtureForUnknown()
        contract = self.write()
        self.assertEqual(verify(self.root, contract, 'reference')['status'], 'fail')
        self.spec['behaviors'][0]['discovery'] = 'observed'
        with self.assertRaises(ValueError): self.write()
        self.spec['behaviors'][0]['discovery'] = 'unknown'
        self.targets['targets']['reference']['kind'] = 'original_online'
        with self.assertRaises(ValueError): self.write()

    def setUpFixtureForUnknown(self):
        self.spec['behaviors'] = [{'id': 'unknown', 'description': 'Not explored', 'discovery': 'unknown'}]

    def test_type_strict_assertions_cannot_confuse_true_with_one(self):
        self.assertTrue(differences({'complete': True}, {'complete': 1}))
        self.assertFalse(differences({'items': [1, 2]}, {'items': [1, 2], 'extra': 'allowed'}))
        self.assertTrue(differences({'items': [1, 2]}, {'items': [2, 1]}))

    def test_unavailable_driver_cannot_be_misreported_as_business_success(self):
        (self.root/'driver.py').write_text('import json,sys\nr=json.load(sys.stdin)\nprint(\'APP_REBUILD_RESULT \'+json.dumps({\'operation\':r[\'operation\'],\'status\':\'unavailable\',\'reason\':\'Native UI permission missing\'}))\n')
        contract = self.write()
        result = verify(self.root, contract, 'reference')
        self.assertEqual(result['status'], 'fail')
        self.assertEqual(result['behaviors'][0]['status'], 'unavailable')
        with self.assertRaises(ValueError):
            freeze(contract, result)

    def test_wrong_precondition_cannot_pass_even_when_final_assertions_match(self):
        self.spec['behaviors'][0]['precondition'] = {'completed': True}
        contract = self.write()
        result = verify(self.root, contract, 'reference')
        self.assertEqual(result['behaviors'][0]['status'], 'invalid')
        self.assertEqual(result['behaviors'][0]['reason'], 'scenario precondition was not established')

    def test_batch_deadline_stops_new_actions_and_retains_bounded_cleanup(self):
        (self.root/'driver.py').write_text('import time\ntime.sleep(0.15)\n'+DRIVER)
        contract = self.write()
        result = verify(self.root, contract, 'reference', timeout=1, deadline=time.time()+0.03)
        self.assertEqual(result['status'], 'fail')
        self.assertEqual(result['lifecycle'][0]['receipt']['status'], 'timeout')
        self.assertIn('Not executed',result['lifecycle'][-2]['receipt']['output'])
        self.assertEqual(result['lifecycle'][-1]['operation'], 'stop')
        self.assertEqual(result['lifecycle'][-1]['receipt']['status'], 'pass')

    def test_cli_persists_actual_failure_then_repair_without_overwriting_receipts(self):
        def run(operation, *arguments):
            return subprocess.run([sys.executable, '-m', 'workflows.rebuild.cli', operation,
                                   '--workspace', str(self.root), '--spec', 'spec.json', '--targets', 'targets.json',
                                   *arguments], text=True, capture_output=True, timeout=10)
        reference = run('verify', '--target', 'reference', '--out', 'artifacts/reference.json')
        self.assertEqual(reference.returncode, 0, reference.stderr)
        batch = run('freeze', '--receipt', 'artifacts/reference.json', '--out', 'artifacts/frozen.json')
        self.assertEqual(batch.returncode, 0, batch.stderr)
        failure = run('verify', '--target', 'candidate', '--frozen', 'artifacts/frozen.json', '--out', 'artifacts/failure.json')
        self.assertEqual(failure.returncode, 1, failure.stderr)
        (self.root/'candidate.py').write_text(APP)
        success = run('verify', '--target', 'candidate', '--frozen', 'artifacts/frozen.json', '--out', 'artifacts/success.json')
        self.assertEqual(success.returncode, 0, success.stderr)
        preserved = (self.root/'artifacts/failure.json').read_bytes()
        duplicate = run('verify', '--target', 'candidate', '--frozen', 'artifacts/frozen.json', '--out', 'artifacts/failure.json')
        self.assertEqual(duplicate.returncode, 2)
        self.assertEqual((self.root/'artifacts/failure.json').read_bytes(), preserved)
