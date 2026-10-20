from pathlib import Path
import sys
import tempfile
import threading
import time
import unittest
from capabilities.exploration.harness import Harness
from runtime.harness_mcp import invoke


class ExplicitAdoption(unittest.TestCase):
    def test_reopened_session_keeps_feedback_and_budget_and_transfers_scope(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            harness=Harness(root/'.codex/state')
            task=harness.start(workspace=directory,session_id='old',objective='repair',
                               verifier=[sys.executable,'-c','raise SystemExit(1)'],max_iterations=3)
            harness.begin(task['id'],'first real failure')
            failed=harness.verify(task['id'])
            harness.pause(task['id'],'user will continue in another session')
            reopened=Harness(root/'.codex/state')
            self.assertIsNone(reopened.active(directory,'new'))
            transferred=invoke(reopened,'exploration_adopt',{'task_id':task['id'],'workspace':directory,'session_id':'new'})
            self.assertEqual(transferred['phase'],'paused')
            self.assertIsNone(reopened.active(directory,'old'))
            continued=reopened.resume(task['id'])
            self.assertEqual(continued['attempts'],failed['attempts'])
            self.assertEqual(continued['deadline'],failed['deadline'])
            self.assertEqual(continued['iterations'],1)

    def test_active_cross_workspace_and_destination_tasks_cannot_be_taken_over(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            harness=Harness(root/'.codex/state')
            task=harness.start(workspace=directory,session_id='old',objective='repair',verifier=[sys.executable,'-c','pass'])
            with self.assertRaises(ValueError): harness.adopt(task['id'],directory,'new')
            harness.pause(task['id'],'explicit transfer')
            with self.assertRaises(ValueError): harness.adopt(task['id'],str(root/'elsewhere'),'new')
            harness.start(workspace=directory,session_id='new',objective='other',verifier=[sys.executable,'-c','pass'])
            with self.assertRaises(ValueError): harness.adopt(task['id'],directory,'new')

    def test_paused_verification_cannot_be_resumed_or_transferred_while_in_flight(self):
        with tempfile.TemporaryDirectory() as directory:
            harness=Harness(Path(directory)/'.codex/state')
            task=harness.start(workspace=directory,session_id='old',objective='repair',
                               verifier=[sys.executable,'-c','import time; time.sleep(0.3)'],max_iterations=1)
            harness.begin(task['id'],'actual concurrent verification')
            errors=[]
            def verify():
                try: harness.verify(task['id'])
                except Exception as error: errors.append(error)
            thread=threading.Thread(target=verify)
            thread.start()
            deadline=time.monotonic()+2
            while not harness.read(task['id']).get('verification_in_flight') and time.monotonic()<deadline:
                time.sleep(.005)
            self.assertTrue(harness.read(task['id']).get('verification_in_flight'))
            harness.pause(task['id'],'pause while real command is running')
            with self.assertRaises(ValueError): harness.adopt(task['id'],directory,'new')
            with self.assertRaises(ValueError): harness.resume(task['id'])
            thread.join(timeout=2)
            self.assertFalse(thread.is_alive())
            self.assertFalse(errors)
            self.assertEqual(harness.read(task['id'])['phase'],'paused')
            harness.adopt(task['id'],directory,'new')
            resumed=harness.resume(task['id'])
            self.assertEqual(resumed['phase'],'complete')
            self.assertEqual(resumed['iterations'],1)
