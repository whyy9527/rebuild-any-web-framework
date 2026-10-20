from pathlib import Path
import sys
import tempfile
import unittest
from capabilities.exploration.harness import Harness


class Contracts(unittest.TestCase):
    def test_failed_last_attempt_stops_at_budget(self):
        with tempfile.TemporaryDirectory() as folder:
            harness=Harness(Path(folder)/'state')
            task=harness.start(workspace=folder,session_id='s',objective='repair',
                               verifier=[sys.executable,'-c','raise SystemExit(1)'],max_iterations=1)
            harness.begin(task['id'],'measure failure')
            state=harness.verify(task['id'])
            self.assertEqual(state['phase'],'budget_exhausted')
            with self.assertRaises(ValueError): harness.begin(task['id'],'must not retry')

    def test_changed_acceptance_cannot_complete_task(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            tests=root/'tests'
            tests.mkdir()
            acceptance=tests/'test_target.py'
            acceptance.write_text('raise AssertionError("original acceptance")\n')
            harness=Harness(root/'state')
            task=harness.start(workspace=folder,session_id='s',objective='repair',
                               verifier=[sys.executable,str(acceptance)])
            harness.begin(task['id'],'attempt to bypass acceptance')
            acceptance.write_text('pass\n')
            state=harness.verify(task['id'])
            self.assertEqual(state['phase'],'blocked')
            self.assertEqual(state['attempts'][-1]['evaluation']['status'],'invalid')
