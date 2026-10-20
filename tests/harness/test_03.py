from pathlib import Path
import tempfile
import unittest
from capabilities.exploration.harness import Harness

class RealVerifier(unittest.TestCase):
    def test_failure_then_repair_and_no_self_certified_success(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            (root/'answer.py').write_text('value=1\n')
            (root/'tests').mkdir()
            (root/'tests/test_answer.py').write_text('import unittest\nimport answer\nclass Check(unittest.TestCase):\n def test_answer(self): self.assertEqual(answer.value,2)\n')
            harness=Harness(root/'state')
            task=harness.start(workspace=folder,session_id='s',objective='repair',verifier=['python3','-m','unittest','discover','-s','tests'])
            harness.begin(task['id'],'inspect failure')
            failed=harness.verify(task['id'])
            self.assertEqual(failed['phase'],'ready')
            self.assertEqual(failed['attempts'][-1]['evaluation']['status'],'fail')
            (root/'answer.py').write_text('value=2\n')
            harness.begin(task['id'],'repair target')
            self.assertEqual(harness.verify(task['id'])['phase'],'complete')
