import hashlib
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from scripts.package_framework import adapt, export, git, selected

SCRIPT = Path(__file__).resolve().parents[2] / 'scripts/package_framework.py'


class FrameworkPackage(unittest.TestCase):
    def test_private_recovery_commands_are_not_public_instructions(self):
        original = ('# Retirement\n\nSource maintainers may restore private history.\n'
                    '```sh\ngit archive 781999b projects/duolingo-web | tar -x\n```\n'
                    '## Research record\nThe experiment found no measured gain.\n')
        public = adapt('docs/history/retirement-2026-10-22.md', original, 'source', 'owner/public')
        self.assertNotIn('git archive', public)
        self.assertNotIn('781999b', public)
        self.assertIn('The experiment found no measured gain.', public)
        self.assertEqual(adapt('docs/history/retirement-2026-10-22.md', original, 'source'), original)

    def test_selection_contains_framework_and_synthetic_fixture_only(self):
        for name in (
                'runtime/dream.py',
                'capabilities/rebuild/frontend.py',
                'tests/rebuild/test_frontend.py',
                'projects/dream-rsi-check/rebuild.json',
                'projects/dream-rsi-check/worker.py'):
            self.assertTrue(selected(name), name)
        for name in (
                'projects/example-app/rebuild.json',
                'projects/native-client/Package.swift',
                'projects/dream-rsi-check/private/key.json',
                'tests/business_ablation/test_controls.py'):
            self.assertFalse(selected(name), name)

    def test_sample_cli_flag_is_retired(self):
        with tempfile.TemporaryDirectory() as directory:
            result = subprocess.run(
                [sys.executable, str(SCRIPT), '--out', str(Path(directory) / 'snapshot'),
                 '--sample'], capture_output=True, text=True)
            self.assertEqual(result.returncode, 2)
            self.assertIn('unrecognized arguments', result.stderr)
            self.assertFalse((Path(directory) / 'snapshot').exists())

    def test_export_preserves_current_fixture_and_sanitizes_excluded_history(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / 'source'
            root.mkdir()
            git(root, 'init', '-q')
            fixture_link = '[synthetic protocol config](../../projects/dream-rsi-check/rebuild.json)'
            files = {
                'pyproject.toml': '[project]\nversion = "0.4.1"\n',
                'README.md': (
                    '# Framework\n\nThis repository owns the framework, tests, and synthetic fixture. '
                    'Product applications live in independent consumer repositories.\n'
                    '## Getting started\nCreate an independent consumer workspace.\n'),
                'README.zh-CN.md': (
                    '# Framework\n\n本仓库维护框架和合成夹具。\n'
                    '## 开始使用\n创建独立消费工作区。\n'),
                'AGENTS.md': 'Use the locked framework environment.\n',
                'CHANGELOG.md': '# Changelog\n',
                'THIRD_PARTY_NOTICES.md': '# Licenses\n\nFramework dependency notices.\n',
                'LICENSE': 'MIT fixture\n',
                '.gitignore': 'private/\n',
                'tests/__init__.py': '',
                'scripts/package_framework.py': '# packager snapshot\n',
                'capabilities/rebuild/frontend.py': '# framework comparator\n',
                'runtime/dream.py': '# framework runtime\n',
                'workflows/rebuild/WORKFLOW.md': '# framework workflow\n',
                'workflows/rebuild/PROJECT.md': (
                    '# Project configuration\n\n'
                    f'The bundled fixture is linked here: {fixture_link}.\n'),
                'tests/rebuild/test_frontend.py': '# generic test\n',
                'tests/release/test_framework_package.py': '# release test\n',
                'projects/dream-rsi-check/rebuild.json': '{"schema_version": 1}\n',
                'projects/dream-rsi-check/worker.py': '# synthetic protocol fixture\n',
                'projects/example-app/rebuild.json': '{}',
                'projects/example-app/README.md': 'consumer app\n',
                'projects/native-client/Package.swift': 'product source\n',
                'projects/native-client/private/key.json': b'private credential',
                'docs/history.md': (
                    '[Source file](https://github.com/owner/private/blob/abc123/private/source.md)\n'
                    '[Excluded path](../projects/native-client/Package.swift)\n'),
            }
            for name, content in files.items():
                target = root / name
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(content if isinstance(content, bytes) else content.encode())
            git(root, 'add', '--', *(name for name in files
                                     if name != 'projects/native-client/private/key.json'))
            git(root, 'add', '-f', '--', 'projects/native-client/private/key.json')
            git(root, '-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid',
                'commit', '-qm', 'framework fixture')

            # The exporter reads the committed tree and ignores worktree modifications.
            (root / 'runtime/dream.py').write_text('uncommitted change')
            output = Path(directory) / 'public'
            manifest = export(root, 'HEAD', output, 'owner/private', 'owner/public')
            exported = set(manifest['files'])

            project_paths = {name.split('/')[1] for name in exported if name.startswith('projects/')}
            self.assertEqual(project_paths, {'dream-rsi-check'})
            self.assertIn('projects/dream-rsi-check/rebuild.json', exported)
            self.assertNotIn('projects/example-app/rebuild.json', exported)
            self.assertNotIn('projects/native-client/Package.swift', exported)
            self.assertNotIn('projects/native-client/private/key.json', exported)

            for name, digest in manifest['files'].items():
                self.assertEqual(hashlib.sha256((output / name).read_bytes()).hexdigest(), digest)
            self.assertEqual((output / 'runtime/dream.py').read_text(), '# framework runtime\n')
            project_doc = (output / 'workflows/rebuild/PROJECT.md').read_text()
            self.assertIn(fixture_link, project_doc)
            self.assertNotIn('projects/my-app/rebuild.json', project_doc)

            history = (output / 'docs/history.md').read_text()
            self.assertNotIn('github.com/owner/private/blob/', history)
            self.assertEqual(history.count('历史证据未随公开发行'), 2)
            readme = (output / 'README.md').read_text()
            self.assertIn('Product applications live in independent consumer repositories.', readme)
            self.assertIn('FRAMEWORK-SOURCE.json', readme)


if __name__ == '__main__':
    unittest.main()
