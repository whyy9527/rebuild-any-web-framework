from pathlib import Path
import tempfile
import unittest
from capabilities.exploration.harness import Harness

class IterationReservation(unittest.TestCase):
    def test_begin_is_idempotent_and_cannot_bypass_budget(self):
        with tempfile.TemporaryDirectory() as folder:
            harness=Harness(Path(folder)/'state')
            task=harness.start(workspace=folder,session_id='s',objective='fix',verifier=['python3','-m','unittest'],max_iterations=1)
            first=harness.begin(task['id'],'check the cause')
            self.assertEqual(first['iterations'],1)
            self.assertEqual(harness.begin(task['id'],'duplicate')['iterations'],1)
            self.assertEqual(first['phase'],'working')
