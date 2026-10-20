import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from capabilities.exploration.storage import digest
from workflows.rebuild.project import load_project, project_status


class NativeGoalProject(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.project = {
            'schema_version': 1, 'name': 'Example $app', 'source': 'Observed reference',
            'target': 'Another language', 'objective': 'Rebuild the actual experience',
            'completion': ['Homepage, interactions and sound match the reference'],
            'inputs': {}, 'commands': {}}
        self.write()

    def write(self):
        (self.root / 'project.json').write_text(json.dumps(self.project))

    def cli(self, *arguments):
        return subprocess.run([
            sys.executable, '-m', 'workflows.rebuild.project', *arguments,
            '--workspace', str(self.root), '--project', 'project.json'],
            capture_output=True, text=True, timeout=10)

    def test_goal_is_read_only_native_payload_and_allows_an_unexplored_project(self):
        before = set(self.root.iterdir())
        result = self.cli('goal')
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(set(payload), {'objective'})
        self.assertIn('Example $app', payload['objective'])
        self.assertIn('Homepage, interactions and sound match the reference', payload['objective'])
        self.assertIn('workflows/rebuild/WORKFLOW.md', payload['objective'])
        self.assertIn(str(self.root / 'project.json'), payload['objective'])
        self.assertIn('使用 RSI 改进探索', payload['objective'])
        self.assertIn('rsi.config', payload['objective'])
        self.assertIn('project preflight', payload['objective'])
        self.assertNotIn('消融', payload['objective'])
        self.assertEqual(set(self.root.iterdir()), before)
        self.assertFalse((self.root / '.codex').exists())

    def test_preflight_reports_missing_method_without_blocking_bootstrap_commands(self):
        before = {path: path.read_bytes() for path in self.root.iterdir()}
        result = self.cli('preflight')
        self.assertEqual(result.returncode, 1, result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual(report['status'], 'gaps')
        codes = {row['code'] for row in report['gaps']}
        self.assertTrue({'rsi.config', 'rsi.pool', 'rsi.replay', 'e2e.driver'} <= codes)
        self.assertIn('not evaluated', report['completion'])
        self.assertEqual({path: path.read_bytes() for path in self.root.iterdir()}, before)
        self.project['commands']['build'] = [sys.executable, '-c', 'pass']
        self.write()
        self.assertEqual(self.cli('run', '--command', 'build').returncode, 0)

    def test_missing_input_and_workspace_escape_are_reported_before_execution(self):
        for path in ('missing.json', '../outside.json'):
            with self.subTest(path=path):
                self.project['inputs'] = {'fixture': path}
                self.write()
                result = self.cli('goal')
                self.assertEqual(result.returncode, 2)
                self.assertEqual(json.loads(result.stderr)['status'], 'invalid')

    def test_malformed_project_is_not_used_to_create_a_goal(self):
        self.project['completion'] = []
        self.write()
        self.assertEqual(self.cli('goal').returncode, 2)
        self.project['completion'] = ['Observable outcome']
        self.project['schema_version'] = True
        self.write()
        self.assertEqual(self.cli('goal').returncode, 2)
        (self.root / 'project.json').write_text('[]')
        self.assertEqual(self.cli('goal').returncode, 2)

    def test_command_uses_workspace_argv_and_propagates_real_failure(self):
        (self.root / 'record.py').write_text(
            'import json, pathlib, sys\n'
            'pathlib.Path("argv.json").write_text(json.dumps(sys.argv[1:]))\n'
            'raise SystemExit(1)\n')
        literal = '{"value":"$(touch INJECTED) `touch ALSO_INJECTED`"}'
        self.project['commands'] = {'compare': [sys.executable, 'record.py', literal, '{out}']}
        self.write()
        result = self.cli('run', '--command', 'compare', '--out', 'fresh-result')
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertEqual(json.loads((self.root / 'argv.json').read_text()), [literal, 'fresh-result'])
        self.assertFalse((self.root / 'INJECTED').exists())
        self.assertFalse((self.root / 'ALSO_INJECTED').exists())

    def test_dry_run_does_not_launch_and_requires_actual_observation_and_fresh_output(self):
        self.project['commands'] = {'compare': ['never-launch-this', '{observed}', '{out}']}
        self.write()
        (self.root / 'observed.json').write_text('{}')
        result = self.cli('run', '--command', 'compare', '--observed', 'observed.json',
                          '--out', 'fresh', '--dry-run')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(json.loads(result.stdout)['executed'])
        self.assertFalse((self.root / 'fresh').exists())
        (self.root / 'fresh').mkdir()
        refused = self.cli('run', '--command', 'compare', '--observed', 'observed.json',
                           '--out', 'fresh', '--dry-run')
        self.assertEqual(refused.returncode, 2)
        missing = self.cli('run', '--command', 'compare', '--out', 'another', '--dry-run')
        self.assertEqual(missing.returncode, 2)

    def test_status_does_not_promote_a_passing_historical_receipt_to_current_completion(self):
        contract = {'requirements': [{'id': 'home-image', 'kind': 'image_pixels'}]}
        receipt = {'status': 'pass', 'contract_digest': digest(contract),
                   'rows': [{'id': 'home-image', 'status': 'pass'}]}
        (self.root / 'contract.json').write_text(json.dumps(contract))
        (self.root / 'receipt.json').write_text(json.dumps(receipt))
        (self.root / 'history.json').write_text(json.dumps({'states': [], 'transitions': []}))
        self.project['inputs'] = {'frontend_contract': 'contract.json',
                                  'historical_frontend_result': 'receipt.json',
                                  'exploration_history': 'history.json'}
        self.write()
        root, project = load_project(self.root, 'project.json')
        before = {path: path.read_bytes() for path in self.root.iterdir()}
        status = project_status(root, project)
        self.assertTrue(status['historical_frontend']['contract_matches'])
        self.assertIn('historical only', status['historical_frontend']['freshness'])
        self.assertIn('not evaluated', status['completion'])
        self.assertIn('does not prove', status['exploration']['completion'])
        self.assertEqual(status['method']['status'], 'gaps')
        self.assertIn('rsi.pool', {row['code'] for row in status['method']['gaps']})
        self.assertEqual({path: path.read_bytes() for path in self.root.iterdir()}, before)


if __name__ == '__main__':
    unittest.main()
