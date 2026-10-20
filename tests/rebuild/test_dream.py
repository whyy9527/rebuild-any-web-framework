from copy import deepcopy
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import threading
import unittest

from capabilities.exploration import dream
from capabilities.exploration.storage import digest
from runtime.dream import Commands, cycle, load_pool, read, replay_candidates, sha
from workflows.rebuild.project import method_report, project_status


REPO = Path(__file__).resolve().parents[2]


def tree(scores=(.25, .5, 1, .75)):
    nodes = [{'id': 'r', 'parent': None, 'seq': 0, 'score': 0,
              'observation': {}, 'generation_history': [], 'snapshot': 'hidden-root'}]
    # Two branches with depth two, interleaved by actual creation order.
    for seq, (parent, score) in enumerate(zip(('r', 'n1', 'r', 'n3'), scores), 1):
        ancestor = next(n for n in nodes if n['id'] == parent)
        nodes.append({'id': f'n{seq}', 'parent': parent, 'seq': seq, 'score': score,
                      'observation': {'value': score}, 'snapshot': 'hidden-snapshot',
                      'generation_history': ancestor['generation_history'] + [seq]})
    return {'schema_version': 1, 'kind': 'dream_tree', 'protocol': 'fixed', 'nodes': nodes}


def serial(view, rho):
    return [view['eligible'][-1]]


class DreamAlgorithmTests(unittest.TestCase):
    def test_multilevel_replay_and_root_creation_order(self):
        world = tree()
        actions = [['r'], ['r', 'n1'], ['n3'], []]
        result = dream.replay(world, lambda v, r: actions[v['round']], rho=1, workers=2, rounds=5)
        self.assertEqual([s['revealed'] for s in result['trace']], [['n1'], ['n3', 'n2'], ['n4']])
        self.assertEqual((result['calls'], result['rounds'], result['stop']), (4, 3, 'world_exhausted'))

    def test_unrevealed_future_cannot_change_earlier_input(self):
        seen = []
        def policy(view, rho):
            seen.append(deepcopy(view))
            self.assertFalse(any('snapshot' in n for n in view['nodes']))
            view['nodes'][0]['observation']['tamper'] = True
            return ['r'] if view['round'] == 0 else []
        original = tree()
        changed = deepcopy(original)
        changed['nodes'][2]['score'] = 900
        changed['nodes'][2]['observation'] = {'future': 'different'}
        before = deepcopy(original)
        dream.replay(original, policy, rho=1, workers=2, rounds=4)
        first = seen[:]; seen.clear()
        dream.replay(changed, policy, rho=1, workers=2, rounds=4)
        self.assertEqual(first, seen)
        self.assertEqual(original, before)

    def test_no_continuation_still_costs_a_round(self):
        result = dream.replay(tree(), serial, rho=1, workers=2, rounds=5)
        self.assertEqual((result['calls'], result['rounds']), (2, 5))
        self.assertEqual(result['trace'][-1]['revealed'], [])
        self.assertEqual(result['stop'], 'round_limit')

    def test_invalid_actions_and_tree_are_rejected(self):
        for action in (['r', 'r'], ['hidden'], ['r', 'n1', 'n2'], 'r'):
            with self.subTest(action=action), self.assertRaises(dream.PolicyError):
                dream.replay(tree(), lambda v, r: action, rho=1, workers=2, rounds=4)
        with self.assertRaises(dream.PolicyError):
            dream.replay(tree(), lambda v, r: ['r'] if v['round'] == 0 else
                         ['n1'] if v['round'] < 3 else [], rho=1, workers=2, rounds=4)
        for change in ('seq', 'history', 'branch'):
            world = tree()
            if change == 'seq':
                world['nodes'][3]['seq'] = 2
            elif change == 'history':
                world['nodes'][2]['generation_history'] = ['invented']
            else:
                world['nodes'][3]['parent'] = 'n1'
            with self.subTest(change=change), self.assertRaises(ValueError):
                dream.validate_tree(world)

    def test_equation_one_against_hand_calculation(self):
        # rho paths: zero calls, 1/.25, 2/.5, 3/1, 4/1.
        # Last point dominated. HV=.25*3/4+.25*2/4+.5*1/4=.4375.
        def policy(view, rho):
            if view['round'] >= round(4 * rho):
                return []
            return [['r'], ['n1'], ['r'], ['n3']][view['round']]
        result = dream.score_world(tree(), policy, workers=2, rounds=6, penalty=.1)
        self.assertAlmostEqual(result['hypervolume'], .4375)
        self.assertAlmostEqual(result['parallelism_penalty'], .8)
        self.assertAlmostEqual(result['score'], .3575)
        self.assertEqual(result['pareto'], [[0, 0], [1, .25], [2, .5], [3, 1]])

    def test_all_worlds_feedback_selection_and_incumbent_retention(self):
        worlds = [tree(), tree((1, .1, .1, .1))]
        def branch(view, rho):
            return ['r'] if view['round'] < 2 else []
        options = dict(workers=2, rounds=4, penalty=.05)
        expected = sum(dream.score_world(w, branch, **options)['score'] for w in worlds) / 2
        self.assertAlmostEqual(dream.evaluate_pool(worlds, branch, **options)['score'], expected)
        calls = []
        def revise(current, feedback, index):
            calls.append(deepcopy(feedback))
            if index == 1:
                return lambda v, r: ['invalid']
            self.assertEqual(feedback[-1]['status'], 'invalid')
            return branch
        chosen, result = dream.improve(worlds, branch, revise, versions=3, **options)
        self.assertIs(chosen, branch)
        self.assertEqual(result['selected_version'], 0)
        self.assertEqual([len(f) for f in calls], [1, 2])
        self.assertEqual(len(calls[0][0]['worlds']), 2)
        self.assertEqual(result['pool_digest'], digest(worlds))

    def test_invalid_worlds_do_not_get_favorable_scores(self):
        for world in (tree((0, 0, 0, 0)), {**tree(), 'nodes': tree()['nodes'][:1]}):
            with self.assertRaises(ValueError):
                dream.score_world(world, serial, workers=1, rounds=3, penalty=0)
        with self.assertRaises(ValueError):
            dream.evaluate_pool([tree(), {**tree(), 'protocol': 'changed'}], serial,
                                workers=1, rounds=3, penalty=0)

    def test_latest_world_winner_cannot_override_full_pool(self):
        worlds = [tree((1, .1, .1, .1)), tree()]
        first = lambda v, r: ['r'] if v['round'] == 0 else []
        deeper = lambda v, r: [v['eligible'][-1]] if v['round'] < 2 else []
        options = dict(workers=2, rounds=4, penalty=.05)
        self.assertGreater(dream.score_world(worlds[-1], deeper, **options)['score'],
                           dream.score_world(worlds[-1], first, **options)['score'])
        chosen, result = dream.improve(worlds, first, lambda current, feedback, i: deeper,
                                       versions=2, **options)
        self.assertIs(chosen, first)
        self.assertEqual(result['selected_version'], 0)

    def test_preserved_main_session_replays_reproduce_recorded_scores(self):
        directory = REPO / 'projects/dream-rsi-check/evidence/main-session'
        summary = read(directory / 'summary.json')
        worlds = read(directory / 'worlds.json')
        policies = []
        for i in range(3):
            scope = {}
            path = directory / f'v{i}.py'
            self.assertEqual(sha(path), summary['versions'][i]['code_sha256'])
            exec(compile(path.read_text(), str(path), 'exec'), scope)
            policies.append(scope['select'])
            result = dream.score_world(worlds[0], policies[-1], workers=2, rounds=4, penalty=.05)
            self.assertAlmostEqual(result['score'], summary['versions'][i]['score'])
        result = dream.evaluate_pool(worlds, policies[2], workers=2, rounds=4, penalty=.05)
        self.assertAlmostEqual(result['score'], summary['all_world_mean'])
        self.assertEqual(worlds[1]['policy_sha256'], summary['selected_sha256'])

    def test_parallel_rollout_context_and_deterministic_commit_order(self):
        barrier = threading.Barrier(2)
        seen = []
        history = [['completed']]
        def policy(view, rho):
            return ['r'] if view['round'] == 0 else ['n1', 'r']
        def generate(parent, prefix, completed, seq):
            if seq > 1:
                barrier.wait(timeout=5)  # Fails if worker requests are serialized.
            seen.append((seq, deepcopy(parent), deepcopy(prefix), completed))
            return {'score': seq, 'observation': {'generated': seq},
                    'generation_history': parent['generation_history'] + [seq]}
        result = dream.rollout(tree()['nodes'][0], policy, generate, protocol='fixed',
                               history=history, workers=2, rounds=2)
        self.assertEqual([n['id'] for n in result['nodes']], ['r', 'n1', 'n2', 'n3'])
        self.assertEqual(result['nodes'][2]['generation_history'], [1, 2])
        self.assertTrue(all(item[3] == history for item in seen))
        self.assertEqual([len(item[2]['nodes']) for item in sorted(seen)], [1, 2, 2])


class DreamRuntimeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        shutil.copytree(REPO / 'projects/dream-rsi-check', self.root / 'projects/dream-rsi-check')
        self.config = read(self.root / 'projects/dream-rsi-check/dream.json')
        for role in ('agent', 'evaluator', 'reviser'):
            self.config[role][0] = sys.executable

    def test_cycle_redeploys_winner_then_replays_without_discovery(self):
        result = cycle(self.root, self.config, 'runs/online', iterations=2)
        pool, worlds, selected = load_pool(self.root, result['pool'])
        self.assertEqual(len(worlds), 2)
        self.assertEqual(worlds[1]['policy_sha256'], sha(self.root / 'runs/online/iteration-1/dream/selected.py'))
        self.assertEqual(read(self.root / 'runs/online/iteration-1/dream/evaluation.json')['selected_version'], 1)
        self.assertTrue(any(len(n['generation_history']) > 1 for n in worlds[1]['nodes']))
        self.assertTrue(any(len(step['parents']) == 2 for step in worlds[1]['rounds']))
        for world in worlds:
            for node in world['nodes'][1:]:
                self.assertTrue(node['observation']['evaluation']['executed'])
                self.assertEqual(node['score'], sum(node['observation']['evaluation']['checks']) / 4)
                self.assertTrue((self.root / node['snapshot'] / 'candidate.py').is_file())
        online_requests = len(list(self.root.rglob('online/attempt-*/agent/request.json')))
        replay = cycle(self.root, self.config, 'runs/offline', iterations=1, pool=result['pool'], offline=True)
        self.assertEqual(replay['iterations'][0]['worlds'], 2)
        self.assertEqual(len(list(self.root.rglob('online/attempt-*/agent/request.json'))), online_requests)
        self.assertFalse(list((self.root / 'runs/offline').rglob('agent')))
        state = project_status(self.root, {'name': 'fixture', 'inputs': {'rsi_pool': replay['pool']}})
        self.assertEqual(state['rsi']['worlds'], 2)
        resumed = cycle(self.root, self.config, 'runs/resumed', iterations=1, pool=replay['pool'])
        self.assertEqual(resumed['iterations'][0]['worlds'], 3)
        generation_request = read(self.root / 'runs/resumed/iteration-1/online/attempt-1/agent/request.json')
        self.assertEqual(len(generation_request['completed_history']), 2)
        self.assertNotIn('snapshot', generation_request['completed_history'][0][0])
        # New files in old snapshots, not only edits to manifest-listed files, are detected.
        (self.root / worlds[0]['nodes'][1]['snapshot'] / 'extra.py').write_text('changed = True')
        with self.assertRaisesRegex(ValueError, 'snapshot changed'):
            load_pool(self.root, result['pool'])

    def test_fixed_protocol_and_historical_policy_integrity(self):
        result = cycle(self.root, self.config, 'runs/check', iterations=1)
        altered = deepcopy(self.config)
        altered['score_semantics'] = 'changed scale'
        with self.assertRaisesRegex(ValueError, 'protocol changed'):
            cycle(self.root, altered, 'runs/mixed', iterations=1, pool=result['pool'])
        _, _, selected = load_pool(self.root, result['pool'])
        selected.write_text('def select(v, r): return []')
        with self.assertRaisesRegex(ValueError, 'selected policy changed'):
            load_pool(self.root, result['pool'])
        commands = Commands(self.root, self.config)
        (self.root / 'projects/dream-rsi-check/worker.py').write_text('changed = True')
        with self.assertRaises(RuntimeError):
            commands.verify()

    def test_current_codex_developer_path_needs_no_nested_model(self):
        del self.config['reviser']
        collected = cycle(self.root, self.config, 'runs/collected', iterations=1, collect_only=True)
        self.assertEqual(collected['status'], 'collected')
        baseline = replay_candidates(self.root, self.config, collected['pool'], [], 'runs/baseline')
        feedback = read(self.root / 'runs/baseline/evaluation.json')
        self.assertEqual(len(feedback['feedback'][0]['worlds']), 1)
        # Read-only project entry must distinguish collection, comparison and deployment.
        config_path = self.root / 'method-config.json'
        config_path.write_text(json.dumps(self.config))
        project = {'inputs': {'rsi_config': 'method-config.json', 'rsi_pool': baseline['pool'],
                             'rsi_evaluation': 'runs/baseline/evaluation.json',
                             'fixture': 'method-config.json', 'frontend_contract': 'method-config.json'},
                   'commands': {key: ['unused'] for key in
                                ('rsi_collect', 'rsi_replay', 'replay', 'compare')}}
        self.assertEqual([row['code'] for row in method_report(self.root, project)['gaps']],
                         ['rsi.comparison'])
        # A developer supplies a revision after reading the real baseline receipt.
        (self.root / 'revision.py').write_text('def select(view,rho):\n    return []\n')
        scored = replay_candidates(self.root, self.config, collected['pool'], ['revision.py'], 'runs/revision')
        self.assertEqual(len(read(self.root / 'runs/revision/evaluation.json')['feedback']), 2)
        project['inputs'].update(rsi_pool=scored['pool'], rsi_evaluation='runs/revision/evaluation.json')
        self.assertEqual([row['code'] for row in method_report(self.root, project)['gaps']],
                         ['rsi.deployment'])
        deployed = cycle(self.root, self.config, 'runs/deploy', iterations=1, pool=scored['pool'], collect_only=True)
        _, worlds, _ = load_pool(self.root, deployed['pool'])
        self.assertEqual(worlds[-1]['policy_sha256'], sha(self.root / 'runs/revision/selected.py'))
        project['inputs']['rsi_pool'] = deployed['pool']
        self.assertEqual(method_report(self.root, project)['status'], 'connected')
        self.assertIn('not evaluated', method_report(self.root, project)['completion'])
        receipt_path = self.root / 'runs/revision/evaluation.json'
        receipt = read(receipt_path)
        receipt['feedback'][1]['worlds'] = []
        receipt_path.write_text(json.dumps(receipt))
        self.assertNotEqual(method_report(self.root, project)['status'], 'connected')
        receipt['selected_version'] = 999
        receipt_path.write_text(json.dumps(receipt))
        with self.assertRaisesRegex(ValueError, 'selected_version'):
            method_report(self.root, project)

    def test_zero_score_preserves_collected_pool_without_claiming_success(self):
        (self.root / 'zero.py').write_text('import json\nprint(json.dumps({"score":0,"observation":{}}))\n')
        self.config['evaluator'] = [sys.executable, 'zero.py']
        with self.assertRaisesRegex(ValueError, 'S > 0'):
            cycle(self.root, self.config, 'runs/zero', iterations=1)
        _, worlds, _ = load_pool(self.root, 'runs/zero/iteration-1/collected-pool.json')
        self.assertEqual(max(n['score'] for n in worlds[0]['nodes']), 0)
        self.assertFalse((self.root / 'runs/zero/result.json').exists())

    def test_cli_and_project_workflow_consumer(self):
        result = subprocess.run([sys.executable, '-m', 'workflows.rebuild.project', 'run',
                                 '--workspace', str(REPO), '--project', 'projects/dream-rsi-check/rebuild.json',
                                 '--command', 'rsi_cycle', '--out', 'artifacts/dream-cli-check', '--dry-run'],
                                cwd=REPO, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('workflows.rebuild.dream', json.loads(result.stdout)['argv'])
        result = subprocess.run([sys.executable, '-m', 'workflows.rebuild.dream', 'cycle',
                                 '--workspace', str(self.root), '--config', 'projects/dream-rsi-check/dream.json',
                                 '--out', 'runs/cli'], cwd=REPO, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)['status'], 'evaluated')


if __name__ == '__main__':
    unittest.main()
