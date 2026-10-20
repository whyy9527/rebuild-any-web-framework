from pathlib import Path
import tempfile
import unittest
from capabilities.exploration.harness import Harness

class SessionTasks(unittest.TestCase):
    def test_task_survives_restart_without_cross_session_activation(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            workspace=root/'input'
            workspace.mkdir()
            harness=Harness(root/'state')
            task=harness.start(workspace=str(workspace),session_id='one',objective='repair',verifier=['python3','-m','unittest'])
            resumed=Harness(root/'state')
            self.assertEqual(resumed.active(str(workspace),'one')['id'],task['id'])
            self.assertIsNone(resumed.active(str(workspace),'two'))
            with self.assertRaises(ValueError): resumed.start(workspace=str(workspace),session_id='one',objective='other',verifier=['python3','-m','unittest'])
