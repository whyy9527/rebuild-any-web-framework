from pathlib import Path
import sys
import tempfile
import unittest
from capabilities.exploration.harness import Harness
from runtime.runner import evaluate, input_manifest, manifest


class AcceptanceInputs(unittest.TestCase):
    def test_commonjs_source_changes_in_evaluator_invalidate_success(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            (root/'app.cjs').write_text('module.exports = 1;')
            before=manifest(root)
            self.assertIn('app.cjs',before)
            result=evaluate(root,[sys.executable,'-c',
                "from pathlib import Path; Path('app.cjs').write_text('module.exports = 2;')"])
            self.assertEqual(result['exit_code'],0)
            self.assertEqual(result['status'],'invalid')
            self.assertEqual(result['integrity'],'source_changed')
            self.assertEqual(result['source_files'],before)
            self.assertNotEqual(before,manifest(root))

    def test_ts_swift_and_fixture_changes_block_success(self):
        for name in ['e2e/course.spec.ts','Tests/LessonTests.swift','fixtures/lesson.json','playwright.config.ts']:
            with self.subTest(name=name), tempfile.TemporaryDirectory() as folder:
                root=Path(folder)
                path=root/name
                path.parent.mkdir(parents=True,exist_ok=True)
                path.write_text('original')
                harness=Harness(root/'.codex/state')
                task=harness.start(workspace=folder,session_id='one',objective='rebuild',
                                   verifier=[sys.executable,'-c','pass'],acceptance_paths=[name])
                harness.begin(task['id'],'must not weaken business acceptance')
                path.write_text('weakened')
                result=harness.verify(task['id'])
                self.assertEqual(result['phase'],'blocked')
                self.assertEqual(result['attempts'][-1]['evaluation']['status'],'invalid')

    def test_declared_directory_detects_new_test_and_missing_fixture(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            (root/'e2e').mkdir()
            initial=input_manifest(root,['e2e','fixture.json'])
            (root/'e2e/new.spec.ts').write_text('test')
            self.assertNotEqual(initial,input_manifest(root,['e2e','fixture.json']))
            (root/'fixture.json').write_text('{}')
            self.assertNotEqual(initial,input_manifest(root,['e2e','fixture.json']))

    def test_source_repair_allowed_while_acceptance_stays_fixed(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            (root/'src').mkdir()
            (root/'src/course.swift').write_text('before')
            (root/'e2e').mkdir()
            (root/'e2e/course.spec.ts').write_text('frozen')
            harness=Harness(root/'.codex/state')
            task=harness.start(workspace=folder,session_id='one',objective='rebuild',
                               verifier=[sys.executable,'-c','pass'])
            harness.begin(task['id'],'repair implementation')
            (root/'src/course.swift').write_text('after')
            self.assertEqual(harness.verify(task['id'])['phase'],'complete')

    def test_explicit_timeout_is_executed_and_total_budget_still_bounds_it(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            harness=Harness(root/'.codex/state')
            task=harness.start(workspace=folder,session_id='one',objective='rebuild',
                               verifier=[sys.executable,'-c','import time; time.sleep(1)'],
                               verify_seconds=0.03,max_iterations=1)
            harness.begin(task['id'],'observe actual timeout')
            result=harness.verify(task['id'])
            self.assertEqual(result['attempts'][-1]['evaluation']['status'],'timeout')
            self.assertEqual(result['phase'],'budget_exhausted')

    def test_paths_cannot_escape_workspace(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)/'project'
            root.mkdir()
            outside=Path(folder)/'private.txt'
            outside.write_text('not acceptance')
            (root/'linked').symlink_to(outside)
            for paths in [['../private.txt'],[str(outside)],['linked'],[]]:
                with self.subTest(paths=paths), self.assertRaises(ValueError):
                    input_manifest(root,paths)
