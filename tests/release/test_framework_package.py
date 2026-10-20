import hashlib
from pathlib import Path
import tempfile
import unittest

from scripts.package_framework import adapt, export, git, selected

class FrameworkPackage(unittest.TestCase):
    def test_public_readme_keeps_sample_and_removes_private_workspace_notice(self):
        text = ('# Framework\nThis private repository contains the complete working history and cases.\n'
                '## Getting started\nprojects/duolingo-web/rebuild.json\n'
                '## Case studies\n[Swift](projects/education-swift/README.md)\n'
                '## Documentation and verification\n')
        result = adapt('README.md', text, 'https://github.com/owner/private/tree/abc',
                       'duolingo-swift', 'owner/public')
        self.assertIn('projects/duolingo-web/rebuild.json', result)
        self.assertIn('[Swift](projects/education-swift/README.md)', result)
        self.assertIn('one Duolingo → Swift case', result)
        self.assertNotIn('This private repository', result)
        self.assertNotIn('https://github.com/owner/private', result)

    def test_scope_keeps_runtime_fixture_but_excludes_cases_private_and_case_tests(self):
        for name in ('runtime/dream.py', 'capabilities/rebuild/frontend.py',
                     'tests/rebuild/test_dream.py', 'projects/dream-rsi-check/worker.py',
                     'runtime/browser.py', 'capabilities/rebuild/browser.py', 'workflows/rebuild/browser.py',
                     'tests/rebuild/test_browser_live.py', 'docs/BROWSER-CAPTURE.md'):
            self.assertTrue(selected(name))
        for name in ('projects/excluded-app/private/local-auth.json', 'projects/duolingo-web/image.png',
                     'projects/education-swift/Sources/LingoSeed/LearningView.swift',
                     'tests/rebuild/test_exploration_tree.py', 'projects/dream-rsi-check/private/key.json'):
            self.assertFalse(selected(name))

    def test_sample_scope_keeps_app_and_replay_inputs_without_other_cases_or_full_history(self):
        for name in ('projects/education-swift/Sources/LingoSeed/Resources/Reference/owl.riv',
                     'projects/duolingo-web/rebuild.json', 'projects/duolingo-web/run-native-course.sh',
                     'projects/duolingo-web/evidence/english-unit12-lesson4-v1/seed-progress.json'):
            self.assertTrue(selected(name, 'duolingo-swift'))
        for name in ('projects/other-app/app.py', 'projects/education-swift/.build/app',
                     'projects/duolingo-web/private/session.json',
                     'projects/duolingo-web/evidence/unrelated-session/cookies.json'):
            self.assertFalse(selected(name, 'duolingo-swift'))

    def test_committed_snapshot_preserves_framework_bytes_and_rejects_overwrite(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / 'source'
            source.mkdir()
            git(source, 'init', '-q')
            samples = {'pyproject.toml': '[project]\nversion = "0.2.0"\n',
                       'README.md': '# Fixture framework\n[中文](README.zh-CN.md)\n## Case studies\n[Case](projects/excluded-app/README.md)\n## Documentation and verification\n',
                       'README.zh-CN.md': '# 框架\n[English](README.md)\n## Duolingo 实践\n[案例](projects/duolingo-web/README.md)\n## 文档与验证\n',
                       'runtime/dream.py': '# committed runtime\n',
                       'capabilities/rebuild/frontend.py': '# committed comparator\n',
                       'projects/dream-rsi-check/worker.py': '# synthetic fixture\n'}
            for name, text in samples.items():
                path = source / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(text)
            git(source, 'add', '--', *samples)
            git(source, '-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid',
                'commit', '-qm', 'fixture')
            (source / 'runtime/dream.py').write_text('# unrelated dirty work\n')
            output = Path(directory) / 'snapshot'
            manifest = export(source, 'HEAD', output, 'whyy9527/rebuild-any-web')
            for name in manifest['files']:
                self.assertEqual(hashlib.sha256((output / name).read_bytes()).hexdigest(), manifest['files'][name])
                if name.startswith(('capabilities/', 'runtime/')):
                    self.assertEqual((output / name).read_bytes(), git(source, 'show', 'HEAD:' + name))
            self.assertTrue(all(name.startswith('projects/dream-rsi-check/') for name in manifest['files'] if name.startswith('projects/')))
            self.assertNotIn('projects/excluded-app', (output / 'README.md').read_text())
            self.assertIn('## Distribution scope', (output / 'README.md').read_text())
            self.assertIn('[中文](README.zh-CN.md)', (output / 'README.md').read_text())
            self.assertIn('## 发行范围', (output / 'README.zh-CN.md').read_text())
            self.assertNotIn('projects/duolingo-web/', (output / 'README.zh-CN.md').read_text())
            with self.assertRaisesRegex(ValueError, 'new output'):
                export(source, 'HEAD', output, 'whyy9527/rebuild-any-web')

    def test_sample_exports_binary_bytes_and_executable_mode_from_commit(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / 'source'; root.mkdir()
            git(root, 'init', '-q')
            files = {'pyproject.toml': b'[project]\nversion = "0.3.0"\n',
                     'projects/duolingo-web/rebuild.json': b'{"inputs":{"frontend_contract":"projects/duolingo-web/contract.json"}}',
                     'projects/duolingo-web/contract.json': b'{"reference_image":"projects/duolingo-web/evidence/older/reference.png","evidence":"projects/exploration-ablation/evidence/legacy.json"}',
                     'projects/exploration-ablation/evidence/legacy.json': b'{"source":"observed Duolingo"}',
                     'projects/duolingo-web/evidence/older/reference.png': b'\x89PNG\x00',
                     'projects/duolingo-web/evidence/older/unrelated.png': b'excluded',
                     'projects/education-swift/Sources/LingoSeed/Resources/Reference/owl.riv': b'\xff\x00\x80',
                     'projects/duolingo-web/run-native-course.sh': b'#!/bin/sh\nexit 0\n',
                     'projects/other-app/secret.txt': b'excluded'}
            for name, data in files.items():
                target = root / name; target.parent.mkdir(parents=True, exist_ok=True); target.write_bytes(data)
            script = root / 'projects/duolingo-web/run-native-course.sh'; script.chmod(0o755)
            git(root, 'add', '--', *files)
            git(root, '-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid', 'commit', '-qm', 'fixture')
            script.write_text('uncommitted change')
            out = Path(directory) / 'public'
            manifest = export(root, 'HEAD', out, 'owner/private', 'duolingo-swift', 'owner/public')
            self.assertEqual(manifest['sample'], 'duolingo-swift')
            self.assertFalse((out / 'projects/other-app').exists())
            self.assertTrue((out / 'projects/duolingo-web/evidence/older/reference.png').exists())
            self.assertTrue((out / 'projects/exploration-ablation/evidence/legacy.json').exists())
            self.assertFalse((out / 'projects/duolingo-web/evidence/older/unrelated.png').exists())
            for name, data in files.items():
                if name in manifest['files']:
                    self.assertEqual((out / name).read_bytes(), data)
            self.assertEqual((out / script.relative_to(root)).stat().st_mode & 0o777, 0o755)
