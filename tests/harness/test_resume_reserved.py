from pathlib import Path
import tempfile
import unittest
from capabilities.exploration.harness import Harness

class ReservedAttemptResume(unittest.TestCase):
    def test_last_reserved_attempt_can_resume_without_new_iteration(self):
        with tempfile.TemporaryDirectory() as folder:
            harness=Harness(Path(folder)/'state')
            task=harness.start(workspace=folder,session_id='s',objective='fix',verifier=['python3','-m','unittest'],max_iterations=1)
            harness.begin(task['id'],'reserved last attempt')
            harness.pause(task['id'],'user paused before verification')
            resumed=harness.resume(task['id'])
            self.assertEqual(resumed['phase'],'working')
            self.assertEqual(resumed['iterations'],1)
