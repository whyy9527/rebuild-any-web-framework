"""Export a framework snapshot, optionally with the public Duolingo Swift sample."""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import subprocess
import tomllib

ROOT_FILES = {'README.md', 'README.zh-CN.md', 'AGENTS.md', 'CHANGELOG.md', 'THIRD_PARTY_NOTICES.md',
              'LICENSE', '.gitignore', 'pyproject.toml', 'requirements.lock', 'tests/__init__.py'}
CASE_TESTS = {'test_enrollment_choices.py', 'test_exploration_replay.py',
              'test_guide_replay04.py', 'test_exploration_tree.py'}
SKILLS = {'exploration-lab', 'lottie-svg-dom-rendering', 'macos-owned-app-audio-output'}
FIXTURE = 'projects/dream-rsi-check/'
SAMPLE_ROOTS = ('projects/duolingo-web/', 'projects/education-swift/')
SAMPLE_INPUT_ROOTS = SAMPLE_ROOTS + ('projects/exploration-ablation/evidence/',)
SAMPLE_EVIDENCE = ('english-frontend-repair-v80/', 'english-unit12-lesson4-v1/',
                   'english-unit12-lesson3-v1/native-final/progress.json.preferences.json')


def selected(name, sample=None):
    path = PurePosixPath(name)
    if any(part in {'private', 'artifacts', 'node_modules', '__pycache__'} for part in path.parts):
        return False
    if sample == 'duolingo-swift' and name.startswith(SAMPLE_ROOTS):
        evidence = 'projects/duolingo-web/evidence/'
        if name.startswith(evidence):
            return name[len(evidence):].startswith(SAMPLE_EVIDENCE)
        return not any(part in {'.build', 'build', 'dist', '.DS_Store'} for part in path.parts)
    if name in ROOT_FILES or name == 'scripts/package_framework.py':
        return True
    if name.startswith(('capabilities/', 'runtime/', 'workflows/')):
        return path.suffix in {'.py', '.md'}
    if name.startswith('docs/'):
        return path.suffix == '.md'
    if name.startswith(('tests/harness/', 'tests/rebuild/')):
        return path.suffix == '.py' and path.name not in CASE_TESTS
    if name.startswith('tests/release/'):
        return path.suffix == '.py'
    if name.startswith(FIXTURE):
        return path.suffix in {'.py', '.json', '.md'}
    return (len(path.parts) == 4 and path.parts[:2] == ('.codex', 'skills')
            and path.parts[2] in SKILLS and path.name == 'SKILL.md')


def git(root, *argv):
    return subprocess.check_output(['git', '-C', str(root), *argv])


def sample_inputs(root, commit, paths):
    """Keep the configured sample's transitive file inputs, not its entire archive."""
    known, found = set(paths), set()
    pending = ['projects/duolingo-web/rebuild.json']
    def strings(value):
        if isinstance(value, str):
            yield value
        elif isinstance(value, dict):
            for child in value.values():
                yield from strings(child)
        elif isinstance(value, list):
            for child in value:
                yield from strings(child)
    while pending:
        name = pending.pop()
        if name in found or name not in known:
            continue
        found.add(name)
        if name.endswith('.json'):
            data = json.loads(git(root, 'show', commit + ':' + name))
            pending.extend(value for value in strings(data)
                           if value in known and value.startswith(SAMPLE_INPUT_ROOTS)
                           and not any(part in {'private', 'artifacts'} for part in PurePosixPath(value).parts))
    return found


def adapt(name, text, source, sample=None, public_repo=None):
    if name in ('README.md', 'README.zh-CN.md'):
        english=name=='README.md'
        start=text.find('## Case studies' if english else '## Duolingo 实践')
        end=text.find('## Documentation and verification' if english else '## 文档与验证')
        if start >= 0 and end > start:
            scope=('## Distribution scope\n\nThis framework snapshot excludes App implementations, reference assets, and private history. '
                   '`projects/` includes only the synthetic Dream-RSI protocol fixture. Create your own app configuration with the project entry point. '
                   'See the [Duolingo](docs/DUOLINGO-LESSONS.md) lessons.\n\n' if english else
                   '## 发行范围\n\n本发行版不包含App实现、原版素材与私有历史。'
                   '`projects/`保留合成的Dream-RSI协议夹具；新App按项目入口建立自己的配置。'
                   '案例复盘见[Duolingo](docs/DUOLINGO-LESSONS.md)。\n\n')
            if sample:
                scope = text[start:end]
            text=text[:start]+scope+text[end:]
        if not sample:
            text=text.replace('projects/duolingo-web/rebuild.json', 'projects/my-app/rebuild.json')
        text += ('\nFramework provenance and file digests: `FRAMEWORK-SOURCE.json`.\n' if english else
                 '\n框架来源和逐文件摘要见 `FRAMEWORK-SOURCE.json`。\n')
        if not public_repo:
            text += f'[{source}]({source})\n'
    elif name == 'AGENTS.md':
        if sample:
            text = re.sub(r'。方块杀手本轮已由用户.*?不自动继续迭代。', '。', text)
        else:
            text = re.sub(r'先遵循用户当前要求。.*?(?=\n\n)',
                          '先遵循用户当前要求。结束案例后不自动恢复探索。本发行版只附带框架协议夹具，'
                          '不包含历史App案例；复盘引用源仓库的固定提交，不能当作本仓库当前产品交付。', text)
    elif name == 'docs/ARCHITECTURE.md' and not sample:
        text = text.split('## 案例实现')[0] + ('## 发行边界\n\n本快照包含框架代码、测试和'
               '`projects/dream-rsi-check`合成协议夹具。App实现、观察器、私有历史和媒体由消费项目拥有，'
               '不在此快照内。历史反例见[Duolingo复盘](DUOLINGO-LESSONS.md)。\n')
    elif name == 'workflows/rebuild/PROJECT.md' and not sample:
        text = text.replace('[Duolingo 配置](../../projects/duolingo-web/rebuild.json)是完整已有案例。',
                            '本发行版不包含历史App案例；新项目从上面的最小配置开始。')
        text = text.replace('projects/duolingo-web/rebuild.json', 'projects/my-app/rebuild.json')
    elif name == 'THIRD_PARTY_NOTICES.md':
        if sample:
            text = re.sub(r'## Bilibili Toy S16 案例.*?(?=## 依赖与研究来源)', '', text, flags=re.S)
            return text.split('## VALORANT 预测器案例')[0].rstrip() + '\n'
        start, end = text.find('## Duolingo 案例'), text.find('## 依赖与研究来源')
        text = text[:start] + ('## 案例与素材\n\n本发行版不包含App案例的第三方媒体、授权账号或私有观察。'
                '源仓库历史案例的内容归其权利人；框架MIT许可不授予再分发第三方素材的权利。\n\n') + text[end:]
        case_only = ('| Rive iOS ', '| Lottie ', '| Apache ECharts ', '| @nestjs/jwt ',
                     '| bcryptjs ', '| cookie-parser ', '| pinyin-pro ')
        text = '\n'.join(line for line in text.splitlines() if not line.startswith(case_only)) + '\n'
        text = text.replace('当前案例引用：', '框架按需使用的依赖：')
        text = text.split('## VALORANT 预测器案例')[0]
    if name == 'docs/ARCHITECTURE.md':
        text = text.split('## 独立网站')[0].rstrip() + '\n'
    if public_repo and name in ('README.md', 'README.zh-CN.md'):
        text = '\n'.join(line for line in text.splitlines()
                         if 'This private repository contains' not in line and '本私有仓库' not in line) + '\n'
        text = text.replace('https://github.com/whyy9527/rebuild-any-web/releases',
                            f'https://github.com/{public_repo}/releases')
        scope = ('This public snapshot contains the framework and one Duolingo → Swift case, including its Swift client. '
                 'The synthetic Dream-RSI fixture tests the protocol. Other apps and the full exploration archive are excluded.\n\n'
                 if name == 'README.md' else
                 '本公开快照包含框架与一个 Duolingo → Swift 案例（含 Swift 客户端）；'
                 '合成 Dream-RSI 夹具用于验证协议。其他 App 和完整探索档案不在发行范围内。\n\n')
        marker = '## Getting started' if name == 'README.md' else '## 开始使用'
        text = text.replace(marker, scope + marker, 1)
    return text


def export(root, ref, output, source_repo, sample=None, public_repo=None):
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
    if sample not in (None, 'duolingo-swift'):
        raise ValueError('unsupported sample')
    names = {name for name in paths if selected(name, sample)}
    if sample:
        names.update(sample_inputs(root, commit, paths))
    source = f'https://github.com/{source_repo}/tree/{commit}'
    files = {}
    adapted = []
    for name in sorted(names):
        raw = git(root, 'show', commit + ':' + name)
        if not name.endswith('.md'):
            files[name] = raw
            continue
        text = raw.decode('utf-8')
        if name.endswith('.md'):
            text = adapt(name, text, source, sample, public_repo)
            def link(match):
                label, target = match.groups()
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
                        return f'{label}（归档证据未附带）'
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
                'scope': ('framework, documentation, tests, synthetic protocol fixture and Duolingo Swift sample; no private inputs'
                          if sample else 'framework, documentation, tests and synthetic protocol fixture; no App cases or private inputs'),
                'sample': sample,
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
    parser.add_argument('--sample', choices=['duolingo-swift'])
    parser.add_argument('--public-repo', help='Public snapshot repository; omit links to excluded private source files')
    args = parser.parse_args()
    result = export(args.workspace, args.ref, args.out, args.source_repo, args.sample, args.public_repo)
    print(json.dumps({'source_commit': result['source_commit'], 'version': result['version'],
                      'files': len(result['files']), 'out': args.out}))


if __name__ == '__main__':
    main()
