"""Export a framework-only snapshot from committed source files."""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import subprocess
import tomllib
from urllib.parse import urlsplit

ROOT_FILES = {'README.md', 'README.zh-CN.md', 'AGENTS.md', 'CHANGELOG.md', 'THIRD_PARTY_NOTICES.md',
              'LICENSE', '.gitignore', 'pyproject.toml', 'requirements.lock', 'tests/__init__.py'}
SKILLS = {'exploration-lab', 'lottie-svg-dom-rendering', 'macos-owned-app-audio-output'}
FIXTURE = 'projects/dream-rsi-check/'
ARCHIVE_NOTE = '（历史证据未随公开发行）'


def selected(name):
    path = PurePosixPath(name)
    if any(part in {'private', 'artifacts', 'node_modules', '__pycache__'} for part in path.parts):
        return False
    if name in ROOT_FILES or name == 'scripts/package_framework.py':
        return True
    if name.startswith(('capabilities/', 'runtime/', 'workflows/')):
        return path.suffix in {'.py', '.md'}
    if name.startswith('docs/'):
        return path.suffix == '.md'
    if name.startswith(('tests/harness/', 'tests/rebuild/')):
        return path.suffix == '.py'
    if name.startswith('tests/release/'):
        return path.suffix == '.py'
    if name.startswith(FIXTURE):
        return path.suffix in {'.py', '.json', '.md'}
    return (len(path.parts) == 4 and path.parts[:2] == ('.codex', 'skills')
            and path.parts[2] in SKILLS and path.name == 'SKILL.md')


def git(root, *argv):
    return subprocess.check_output(['git', '-C', str(root), *argv])


def adapt(name, text, source, public_repo=None):
    if public_repo and name == 'docs/history/retirement-2026-10-22.md':
        introduction = text.split('\n\n', 1)[0]
        _, marker, research = text.partition('## Research record')
        if not marker:
            raise ValueError('retirement index must retain its research record section')
        text = (introduction + '\n\nThe ended application cases and experiments have been removed from '
                'the current tree. Complete archives belong to private source history; this public '
                'snapshot includes neither those objects nor their recovery commands. '
                'Historical v0.4.0 carried only a curated Swift sample, not the complete archives.\n\n'
                + marker + research)
    if name in ('README.md', 'README.zh-CN.md'):
        if public_repo:
            text = '\n'.join(line for line in text.splitlines()
                             if 'This private repository contains' not in line and '本私有仓库' not in line) + '\n'
            text = text.replace('https://github.com/whyy9527/rebuild-any-web/releases',
                                f'https://github.com/{public_repo}/releases')
        else:
            text += f'[{source}]({source})\n'
        if name == 'README.md':
            text += '\nFramework provenance and file digests: FRAMEWORK-SOURCE.json.\n'
        else:
            text += '\n框架来源和逐文件摘要见 FRAMEWORK-SOURCE.json。\n'
    return text


def is_private_source_link(target, source_repo):
    parsed = urlsplit(target)
    if parsed.hostname != 'github.com':
        return False
    parts = parsed.path.strip('/').split('/')
    owner_repo = source_repo.split('/')
    return len(parts) >= 4 and parts[:2] == owner_repo and parts[2] in {'blob', 'tree', 'commit'}


def export(root, ref, output, source_repo, public_repo=None):
    root, output = Path(root).resolve(), Path(output).resolve()
    if output.exists():
        raise ValueError('choose a new output directory')
    if not re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+', source_repo):
        raise ValueError('source repository must be owner/name')
    if public_repo and not re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+', public_repo):
        raise ValueError('public repository must be owner/name')
    commit = git(root, 'rev-parse', '--verify', ref + '^{commit}').decode().strip()
    paths = git(root, 'ls-tree', '-r', '--name-only', commit).decode().splitlines()
    modes = {line.split('\t', 1)[1]: line.split(' ', 1)[0]
             for line in git(root, 'ls-tree', '-r', commit).decode().splitlines()}
    names = {name for name in paths if selected(name)}
    source = f'https://github.com/{source_repo}/tree/{commit}'
    files = {}
    adapted = []
    for name in sorted(names):
        raw = git(root, 'show', commit + ':' + name)
        if not name.endswith('.md'):
            files[name] = raw
            continue
        text = adapt(name, raw.decode('utf-8'), source, public_repo)

        def link(match):
            label, target = match.groups()
            if public_repo and is_private_source_link(target, source_repo):
                return f'{label}{ARCHIVE_NOTE}'
            if re.match(r'^[a-zA-Z]+:', target) or target.startswith(('#', '/')):
                return match.group(0)
            path, _, anchor = target.partition('#')
            resolved = (root / PurePosixPath(name).parent / path).resolve()
            if not resolved.is_relative_to(root):
                return match.group(0)
            relative = resolved.relative_to(root).as_posix()
            if relative in names or any(n.startswith(relative + '/') for n in names):
                return match.group(0)
            if relative in paths:
                if public_repo:
                    return f'{label}{ARCHIVE_NOTE}'
                url = f'https://github.com/{source_repo}/blob/{commit}/{relative}'
                return f'[{label}]({url}' + (('#' + anchor) if anchor else '') + ')'
            return f'{label}（历史或私有证据，发行版未附带）'

        text = re.sub(r'\[([^\]\n]+)\]\(([^)\s]+)\)', link, text)
        files[name] = text.encode('utf-8')
        if files[name] != raw:
            adapted.append(name)
    version = tomllib.loads(files['pyproject.toml'].decode())['project']['version']
    manifest = {'schema_version': 1, 'kind': 'framework_release_snapshot', 'version': version,
                'source_repository': source_repo, 'source_commit': commit,
                'scope': 'framework, documentation, tests, and synthetic protocol fixture; no product apps or private inputs',
                'adapted': adapted,
                'files': {name: hashlib.sha256(data).hexdigest() for name, data in files.items()}}
    output.mkdir(parents=True)
    for name, data in files.items():
        target = output / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        if modes[name] == '100755':
            target.chmod(0o755)
    (output / 'FRAMEWORK-SOURCE.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--workspace', default='.')
    parser.add_argument('--ref', default='HEAD')
    parser.add_argument('--source-repo', default='whyy9527/rebuild-any-web')
    parser.add_argument('--out', required=True)
    parser.add_argument('--public-repo', help='Public snapshot repository; omit links to excluded private source files')
    args = parser.parse_args()
    result = export(args.workspace, args.ref, args.out, args.source_repo, args.public_repo)
    print(json.dumps({'source_commit': result['source_commit'], 'version': result['version'],
                      'files': len(result['files']), 'out': args.out}))


if __name__ == '__main__':
    main()
