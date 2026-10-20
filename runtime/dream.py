"""Snapshot/command adapters for Dream-RSI, without a second task lifecycle."""
import hashlib
import json
from pathlib import Path
import shutil
import sys

from capabilities.exploration import dream
from capabilities.exploration.storage import digest
from capabilities.rebuild.contracts import local_file, require_text
from runtime.runner import evaluate, input_manifest


POLICY_API = """Implement select(view, rho) -> list[str]. Return distinct ids from
view['eligible'], at most view['max_parallelism']; [] stops. view['nodes'] is the
revealed prefix, with id/parent/seq/score/observation/generation_history. rho is
fixed for this run, in [0,1]. Reconstruct trajectories from the prefix. Use only
revealed facts; do not read files, infer hidden scores, hardcode winning ids,
modify the evaluator, or replace the discovery agent. Return JSON {"code":
"self-contained Python source"}. Prior feedback includes every evaluated world,
every budget preference, failures and previous policy versions. Improve the
quality/call/parallelism objective using that feedback."""

POLICY_RUNNER = """import json,sys
scope = {}
with open(sys.argv[1]) as f:
    exec(compile(f.read(), '<exploration-policy>', 'exec'), scope)
request = json.load(sys.stdin)
print(json.dumps(scope['select'](request['view'], request['rho']), allow_nan=False))
"""


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write('\n')


def read(path):
    return json.loads(Path(path).read_text())


def copy_snapshot(source, destination):
    source, destination = Path(source), Path(destination)
    if not source.is_dir() or source.is_symlink() or any(p.is_symlink() for p in source.rglob('*')):
        raise ValueError('explicit snapshot directory without symlinks required')
    shutil.copytree(source, destination)


def load_pool(root, name, protocol=None):
    root = Path(root).resolve()
    pool = read(local_file(root, name))
    if pool.get('schema_version') != 1 or pool.get('kind') != 'dream_pool':
        raise ValueError('dream_pool schema_version 1 required')
    if protocol is not None and pool['protocol'] != protocol:
        raise ValueError('fixed discovery/evaluation protocol changed; use a separate pool')
    worlds = []
    for entry in pool['worlds']:
        path = local_file(root, entry['path'])
        if sha(path) != entry['sha256']:
            raise ValueError('historical world changed')
        tree = dream.validate_tree(read(path))
        if tree['protocol'] != pool['protocol']:
            raise ValueError('mixed evaluator protocols in simulator pool')
        if input_manifest(root, list(tree['artifacts'])) != tree['artifacts']:
            raise ValueError('historical evidence changed')
        for node in tree['nodes']:
            if digest(input_manifest(root, [node['snapshot']])) != node['snapshot_digest']:
                raise ValueError('historical snapshot changed')
        worlds.append(tree)
    selected = local_file(root, pool['policy']['path'])
    if sha(selected) != pool['policy']['sha256']:
        raise ValueError('selected policy changed')
    return pool, worlds, selected


class Commands:
    def __init__(self, root, config):
        self.root = Path(root).resolve()
        self.config = config
        if config.get('schema_version') != 1:
            raise ValueError('Dream-RSI config schema_version 1 required')
        self.timeout = dream.finite(config['timeout_seconds'], 'command timeout')
        if self.timeout <= 0:
            raise ValueError('positive command timeout required')
        for field in ('workers', 'online_rounds', 'replay_rounds', 'versions'):
            dream.positive_int(config[field], field)
        dream.finite(config['parallelism_penalty'], 'parallelism_penalty')
        if config['parallelism_penalty'] < 0:
            raise ValueError('nonnegative parallelism penalty required')
        require_text(config.get('score_semantics'), 'fixed case score semantics')
        if not isinstance(config.get('root_observation'), dict):
            raise ValueError('prepared root observation required')
        self.seed = local_file(self.root, config['seed'], must_exist=False)
        if not self.seed.is_dir():
            raise ValueError('prepared seed snapshot directory required')
        self.inputs = input_manifest(self.root, config['fixed_inputs'])
        if any(v is None for v in self.inputs.values()):
            raise ValueError('fixed agent/evaluator/developer inputs must exist')
        self.seed_inputs = input_manifest(self.root, [config['seed']])
        self.argv = {}
        executables = {}
        self.binaries = {str(Path(sys.executable).resolve()): sha(sys.executable)}
        self.command_files = {}
        for name in ('agent', 'evaluator', 'reviser'):
            if name == 'reviser' and name not in config:
                continue  # The current Codex can write policies between collect/replay calls.
            argv = config[name]
            if not isinstance(argv, list) or not argv or any(not isinstance(a, str) or not a for a in argv):
                raise ValueError('explicit ' + name + ' argv required')
            executable = shutil.which(argv[0])
            if not executable:
                raise ValueError('missing command executable: ' + argv[0])
            executables[name] = sha(executable)
            self.binaries[str(Path(executable).resolve())] = executables[name]
            self.argv[name] = [executable] + [str(self.root / a) if (self.root / a).is_file() else a
                                             for a in argv[1:]]
            for argument in self.argv[name][1:]:
                path = Path(argument)
                if path.is_absolute() and path.is_file():
                    self.command_files[str(path)] = sha(path)
        self.protocol = digest({'commands': {k: config[k] for k in self.argv},
                                'executables': executables, 'policy_python': sha(sys.executable), 'fixed_inputs': self.inputs,
                                'command_files': {str(Path(p).relative_to(self.root)) if Path(p).is_relative_to(self.root)
                                                  else f'external-{i}': value
                                                  for i, (p, value) in enumerate(self.command_files.items())},
                                'seed': self.seed_inputs, 'root_observation': config['root_observation'],
                                'score_semantics': config['score_semantics'],
                                'interface': 'dream-rsi-section-3-v1'})

    def verify(self):
        if (input_manifest(self.root, self.config['fixed_inputs']) != self.inputs
                or input_manifest(self.root, [self.config['seed']]) != self.seed_inputs
                or any(sha(path) != value for path, value in {**self.binaries, **self.command_files}.items())):
            raise RuntimeError('fixed agent/evaluator/developer or initial state changed')

    def call(self, argv, request, directory):
        self.verify()
        directory = Path(directory)
        directory.mkdir(parents=True, exist_ok=False)
        write(directory / 'request.json', request)
        result = evaluate(directory, argv, timeout=self.timeout,
                          environment={'PYTHONPATH': str(self.root), 'PYTHONDONTWRITEBYTECODE': '1'},
                          input_text=json.dumps(request, ensure_ascii=False))
        write(directory / 'receipt.json', result)
        self.verify()
        if result['status'] != 'pass' or result['output_truncated']:
            raise RuntimeError('command did not return an intact result; see ' + str(directory))
        value = json.loads(result['output'])
        write(directory / 'response.json', value)
        return value


class ExecutablePolicy:
    """Trusted policy source runs separately with only the supplied prefix JSON.

    This is an API boundary, not an OS sandbox for malicious Python programs.
    """
    def __init__(self, commands, source, logs):
        self.commands = commands
        self.source = Path(source).resolve()
        self.source_sha256 = sha(self.source)
        self.logs, self.calls = Path(logs), 0

    def __call__(self, view, rho):
        if sha(self.source) != self.source_sha256:
            raise RuntimeError('policy version changed during evaluation')
        self.calls += 1
        return self.commands.call([sys.executable, '-I', '-c', POLICY_RUNNER, str(self.source)],
                                  {'view': view, 'rho': rho}, self.logs / f'decision-{self.calls}')


def online(commands, policy, worlds, directory):
    root = commands.root
    directory = Path(directory)
    copy_snapshot(commands.seed, directory / 'root')
    snapshot = lambda p: p.relative_to(root).as_posix()
    root_node = {'id': 'r', 'parent': None, 'seq': 0, 'score': 0,
                 'observation': commands.config['root_observation'], 'generation_history': [],
                 'snapshot': snapshot(directory / 'root')}
    root_node['snapshot_digest'] = digest(input_manifest(root, [root_node['snapshot']]))

    def generate(parent, prefix, history, seq):
        target = directory / f'attempt-{seq}'
        target.mkdir()
        parent_snapshot = local_file(root, parent['snapshot'], must_exist=False)
        if digest(input_manifest(root, [parent['snapshot']])) != parent['snapshot_digest']:
            raise ValueError('parent snapshot changed before restoration')
        copy_snapshot(parent_snapshot, target / 'workspace')
        request = {'workspace': str(target / 'workspace'), 'parent': dream.public_node(parent),
                   'prefix': prefix, 'completed_history': history, 'attempt': seq}
        proposal = commands.call(commands.argv['agent'], request, target / 'agent')
        if 'generation' not in proposal or not isinstance(proposal.get('observation'), dict):
            raise ValueError('agent must return generation and observation')
        evaluation = commands.call(commands.argv['evaluator'],
                                   {'workspace': str(target / 'workspace')}, target / 'evaluator')
        score = dream.finite(evaluation['score'], 'fixed evaluator score')
        if not isinstance(evaluation.get('observation'), dict):
            raise ValueError('fixed evaluator must return an observation')
        if digest(input_manifest(root, [parent['snapshot']])) != parent['snapshot_digest']:
            raise ValueError('attempt altered its saved parent')
        saved = snapshot(target / 'workspace')
        return {'score': score, 'observation': {'proposal': proposal['observation'],
                                               'evaluation': evaluation['observation']},
                'generation_history': parent['generation_history'] + [proposal['generation']],
                'snapshot': saved, 'snapshot_digest': digest(input_manifest(root, [saved]))}

    # Completed history is separate from the new tree. Do not expose snapshot paths.
    history = [[dream.public_node(n) for n in w['nodes']] for w in worlds]
    tree = dream.rollout(root_node, policy, generate, protocol=commands.protocol, history=history,
                         workers=commands.config['workers'], rounds=commands.config['online_rounds'])
    tree['policy_sha256'] = policy.source_sha256
    tree['artifacts'] = input_manifest(root, [snapshot(directory)])
    write(directory / 'tree.json', tree)
    return tree, {'path': snapshot(directory / 'tree.json'), 'sha256': sha(directory / 'tree.json')}


def dreaming(commands, worlds, source, directory):
    if 'reviser' not in commands.argv and commands.config['versions'] > 1:
        raise ValueError('configure a reviser, or use collect/replay with policy revisions from the current Codex')
    directory = Path(directory)
    directory.mkdir(parents=True)
    shutil.copyfile(source, directory / 'v0.py')
    incumbent = ExecutablePolicy(commands, directory / 'v0.py', directory / 'v0-replay')

    def revise(current, feedback, index):
        response = commands.call(commands.argv['reviser'],
                                 {'interface': POLICY_API, 'policy_code': current.source.read_text(),
                                  'feedback': feedback, 'version': index}, directory / f'v{index}-revision')
        code = response.get('code')
        require_text(code, 'revised executable policy code')
        path = directory / f'v{index}.py'
        with path.open('x') as stream:
            stream.write(code)
        return ExecutablePolicy(commands, path, directory / f'v{index}-replay')

    selected, receipt = dream.improve(worlds, incumbent, revise, versions=commands.config['versions'],
                                      workers=commands.config['workers'], rounds=commands.config['replay_rounds'],
                                      penalty=commands.config['parallelism_penalty'])
    commands.verify()
    shutil.copyfile(selected.source, directory / 'selected.py')
    receipt['policy_sha256'] = sha(directory / 'selected.py')
    receipt['candidate_sha256'] = [sha(directory / f'v{i}.py') for i in range(commands.config['versions'])]
    receipt['settings'] = {k: commands.config[k] for k in ('workers', 'replay_rounds', 'versions', 'parallelism_penalty')}
    write(directory / 'evaluation.json', receipt)
    return directory / 'selected.py', receipt


def cycle(root, config, out, *, iterations, pool=None, offline=False, collect_only=False):
    """An explicit work unit; native Goal remains the only continuation owner."""
    root = Path(root).resolve()
    dream.positive_int(iterations, 'iterations')
    commands = Commands(root, config)
    if pool:
        prior, worlds, selected = load_pool(root, pool, commands.protocol)
        entries = prior['worlds'][:]
    else:
        worlds, entries = [], []
        selected = local_file(root, config['initial_policy'])
    if offline and not worlds:
        raise ValueError('offline dreaming requires an actual saved pool')
    output = local_file(root, out, must_exist=False)
    output.mkdir(parents=True, exist_ok=False)
    summaries = []
    for index in range(iterations):
        directory = output / f'iteration-{index + 1}'
        directory.mkdir()
        if not offline:
            shutil.copyfile(selected, directory / 'online-policy.py')
            deployed = ExecutablePolicy(commands, directory / 'online-policy.py', directory / 'online-decisions')
            tree, entry = online(commands, deployed, worlds, directory / 'online')
            worlds.append(tree); entries.append(entry)
        # Preserve a resumable pool even when the new world has no positive
        # score or the developer fails. This checkpoint makes no selection claim.
        write(directory / 'collected-pool.json', {
            'schema_version': 1, 'kind': 'dream_pool', 'protocol': commands.protocol,
            'worlds': entries[:], 'policy': {'path': selected.relative_to(root).as_posix(),
                                           'sha256': sha(selected)}})
        if collect_only:
            summaries.append({'pool': (directory / 'collected-pool.json').relative_to(root).as_posix(),
                              'worlds': len(worlds), 'selection': 'not evaluated'})
            load_pool(root, summaries[-1]['pool'], commands.protocol)
            continue
        selected, receipt = dreaming(commands, worlds, selected, directory / 'dream')
        state = {'schema_version': 1, 'kind': 'dream_pool', 'protocol': commands.protocol,
                 'worlds': entries[:], 'policy': {'path': selected.relative_to(root).as_posix(),
                                                'sha256': sha(selected)}}
        write(directory / 'pool.json', state)
        summaries.append({'pool': (directory / 'pool.json').relative_to(root).as_posix(),
                          'worlds': len(worlds), 'selected_version': receipt['selected_version'],
                          'score': receipt['feedback'][receipt['selected_version']]['score']})
        # Recheck the immutable pool before deploying the winner into another rollout.
        load_pool(root, summaries[-1]['pool'], commands.protocol)
    result = {'status': 'collected' if collect_only else 'evaluated', 'iterations': summaries,
              'pool': summaries[-1]['pool'], 'completion': 'not evaluated; Goal and E2E own product acceptance'}
    write(output / 'result.json', result)
    return result


def replay_candidates(root, config, pool, candidates, out):
    """The current Codex is the developer; compare its accumulated revisions.

    No model or discovery command is launched. Candidates are copied before
    evaluation, and the incumbent participates in the same frozen pool.
    """
    commands = Commands(root, config)
    root = commands.root
    prior, worlds, incumbent = load_pool(root, pool, commands.protocol)
    sources = [incumbent] + [local_file(root, name) for name in candidates]
    directory = local_file(root, out, must_exist=False)
    directory.mkdir(parents=True, exist_ok=False)
    policies = []
    for index, source in enumerate(sources):
        path = directory / f'v{index}.py'
        shutil.copyfile(source, path)
        policies.append(ExecutablePolicy(commands, path, directory / f'v{index}-replay'))
    selected, receipt = dream.improve(worlds, policies[0], lambda current, feedback, i: policies[i],
                                      versions=len(policies), workers=config['workers'],
                                      rounds=config['replay_rounds'], penalty=config['parallelism_penalty'])
    commands.verify()
    shutil.copyfile(selected.source, directory / 'selected.py')
    receipt['policy_sha256'] = sha(directory / 'selected.py')
    receipt['candidate_sha256'] = [p.source_sha256 for p in policies]
    receipt['settings'] = {k: config[k] for k in ('workers', 'replay_rounds', 'parallelism_penalty')}
    write(directory / 'evaluation.json', receipt)
    updated = {**prior, 'policy': {'path': (directory / 'selected.py').relative_to(root).as_posix(),
                                 'sha256': receipt['policy_sha256']}}
    write(directory / 'pool.json', updated)
    load_pool(root, (directory / 'pool.json').relative_to(root).as_posix(), commands.protocol)
    result = {'status': 'evaluated', 'pool': (directory / 'pool.json').relative_to(root).as_posix(),
              'selected_version': receipt['selected_version'],
              'score': receipt['feedback'][receipt['selected_version']]['score'],
              'completion': 'not evaluated; Goal and E2E own product acceptance'}
    write(directory / 'result.json', result)
    return result
