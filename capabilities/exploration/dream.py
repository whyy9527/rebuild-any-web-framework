"""Dream-RSI section 3: shared online/replay decisions and policy improvement.

Clean-room implementation of arXiv:2609.14858v2. This module neither calls a
model nor owns a Goal. A score belongs to the fixed case evaluator.
"""
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
import math

from capabilities.exploration.storage import digest


RHO = (0, 0.25, 0.5, 0.75, 1)


class PolicyError(ValueError):
    pass


def positive_int(value, name):
    if type(value) is not int or value < 1:
        raise ValueError(name + ' must be a positive integer')
    return value


def finite(value, name):
    if type(value) not in (int, float) or not math.isfinite(value):
        raise ValueError(name + ' must be a finite number')
    return value


def validate_tree(tree):
    if type(tree.get('schema_version')) is not int or tree['schema_version'] != 1 or tree.get('kind') != 'dream_tree':
        raise ValueError('dream_tree schema_version 1 required')
    if not isinstance(tree.get('protocol'), str) or not tree['protocol']:
        raise ValueError('fixed evaluator/discovery protocol identity required')
    nodes = tree.get('nodes')
    if not isinstance(nodes, list) or not nodes:
        raise ValueError('rooted discovery tree required')
    seen, children = {}, {}
    for seq, node in enumerate(nodes):
        identifier = node.get('id')
        if not isinstance(identifier, str) or not identifier or identifier in seen:
            raise ValueError('unique node ids required')
        if type(node.get('seq')) is not int or node['seq'] != seq:
            raise ValueError('explicit contiguous creation order required; never infer or sort it')
        finite(node.get('score'), 'score')
        if not isinstance(node.get('observation'), dict) or not isinstance(node.get('generation_history'), list):
            raise ValueError('node observation and generation history required')
        parent = node.get('parent')
        if seq == 0:
            if parent is not None or node['score'] != 0 or node['generation_history']:
                raise ValueError('root must have no parent and score zero')
        elif parent not in seen:
            raise ValueError('parent must precede its child')
        else:
            history = node['generation_history']
            if len(history) != len(seen[parent]['generation_history']) + 1 or history[:-1] != seen[parent]['generation_history']:
                raise ValueError('child must inherit its parent generation history')
            children.setdefault(parent, []).append(identifier)
            if parent != nodes[0]['id'] and len(children[parent]) > 1:
                raise ValueError('section 3 permits root branching and one continuation per non-root')
        seen[identifier] = node
    return tree


def public_node(node):
    return deepcopy({key: node[key] for key in
                     ('id', 'parent', 'seq', 'score', 'observation', 'generation_history')})


def view(nodes, workers, round_number):
    parents = {node['parent'] for node in nodes[1:]}
    eligible = [nodes[0]['id']] + [n['id'] for n in nodes[1:] if n['id'] not in parents]
    return {'nodes': [public_node(n) for n in nodes], 'eligible': eligible,
            'max_parallelism': workers, 'round': round_number}


def decide(policy, nodes, rho, workers, round_number):
    observation = view(nodes, workers, round_number)
    try:
        batch = policy(deepcopy(observation), rho)
    except Exception as error:
        raise PolicyError('policy execution failed: ' + str(error)) from error
    if (not isinstance(batch, list) or any(not isinstance(v, str) for v in batch)
            or len(batch) != len(set(batch)) or len(batch) > workers
            or any(v not in observation['eligible'] for v in batch)):
        raise PolicyError('select distinct root/visible leaves, at most max_parallelism')
    return batch


def replay(tree, policy, *, rho, workers, rounds):
    """Reveal recorded children only; the policy never receives the hidden tree."""
    tree = deepcopy(validate_tree(tree))
    positive_int(workers, 'workers'); positive_int(rounds, 'rounds')
    finite(rho, 'rho')
    if not 0 <= rho <= 1:
        raise ValueError('rho must be in [0,1]')
    by_id = {n['id']: n for n in tree['nodes']}
    children = {}
    for node in tree['nodes'][1:]:
        children.setdefault(node['parent'], []).append(node['id'])
    observed, revealed, trace = [tree['nodes'][0]], {tree['nodes'][0]['id']}, []
    reason = 'round_limit'
    for k in range(rounds):
        if len(revealed) == len(by_id):
            reason = 'world_exhausted'
            break
        batch = decide(policy, observed, rho, workers, k)
        if not batch:
            reason = 'policy_stop'
            break
        additions = []
        for parent in batch:
            child = next((v for v in children.get(parent, []) if v not in revealed), None)
            if child is not None:
                additions.append(child)
                revealed.add(child)
                observed.append(by_id[child])
        trace.append({'parents': batch, 'revealed': additions,
                      'observations': [public_node(by_id[v]) for v in additions]})
    if len(revealed) == len(by_id):
        reason = 'world_exhausted'
    return {'rho': rho, 'calls': len(observed) - 1, 'rounds': len(trace),
            'best_score': max((n['score'] for n in observed[1:]), default=0), 'trace': trace, 'stop': reason}


def score_world(tree, policy, *, workers, rounds, penalty, rhos=RHO):
    """Equation (1), including the zero-call sweep terms in the penalty mean."""
    validate_tree(tree)
    finite(penalty, 'parallelism penalty')
    if penalty < 0 or not rhos:
        raise ValueError('nonnegative penalty and nonempty rho sweep required')
    budget = len(tree['nodes']) - 1
    optimum = max(n['score'] for n in tree['nodes'])
    if budget <= 0 or optimum <= 0:
        raise ValueError('equation (1) requires B > 0 and S > 0; retain this world without inventing a score')
    runs = [replay(tree, policy, rho=rho, workers=workers, rounds=rounds) for rho in rhos]
    points = set((r['calls'], max(0, min(1, r['best_score'] / optimum))) for r in runs)
    pareto = sorted((n, a) for n, a in points if not any(
        m <= n and b >= a and (m < n or b > a) for m, b in points))
    previous, area = 0, 0
    for calls, attainment in pareto:
        area += (attainment - previous) * (budget - calls) / budget
        previous = attainment
    parallel = sum(r['rounds'] / r['calls'] if r['calls'] else 0 for r in runs) / len(runs)
    return {'score': area - penalty * parallel, 'hypervolume': area,
            'parallelism_penalty': parallel, 'pareto': [list(p) for p in pareto],
            'runs': runs, 'world_digest': digest(tree)}


def evaluate_pool(trees, policy, **options):
    if not trees or len({t['protocol'] for t in trees}) != 1:
        raise ValueError('nonempty simulator pool with one fixed protocol required')
    worlds = [score_world(tree, policy, **options) for tree in trees]
    return {'score': sum(w['score'] for w in worlds) / len(worlds), 'worlds': worlds}


def improve(trees, incumbent, revise, *, versions, **options):
    """Each revision consumes actual earlier replay feedback; retain the incumbent."""
    positive_int(versions, 'versions')
    trees = deepcopy(trees)
    # Validate the worlds independently of candidate failures.
    for tree in trees:
        validate_tree(tree)
    candidates, feedback, current = [incumbent], [], incumbent
    for index in range(versions):
        if index:
            current = revise(current, deepcopy(feedback), index)
            candidates.append(current)
        try:
            result = evaluate_pool(trees, current, **options)
            feedback.append({'version': index, 'status': 'evaluated', **result})
        except PolicyError as error:
            if index == 0:
                raise
            feedback.append({'version': index, 'status': 'invalid', 'score': None, 'error': str(error)})
    best = max((i for i, f in enumerate(feedback) if f['status'] == 'evaluated'),
               key=lambda i: feedback[i]['score'])
    return candidates[best], {'selected_version': best, 'feedback': feedback,
                              'pool_digest': digest(trees)}


def rollout(root, policy, generate, *, protocol, history, workers, rounds, rho=1):
    """Generate/evaluate real children concurrently from separate parent snapshots."""
    positive_int(workers, 'workers'); positive_int(rounds, 'rounds')
    finite(rho, 'rho')
    if not 0 <= rho <= 1:
        raise ValueError('rho must be in [0,1]')
    tree = {'schema_version': 1, 'kind': 'dream_tree', 'protocol': protocol,
            'nodes': [deepcopy(root)], 'rounds': []}
    validate_tree(tree)
    for k in range(rounds):
        nodes = tree['nodes']
        batch = decide(policy, nodes, rho, workers, k)
        if not batch:
            tree['stop'] = 'policy_stop'
            break
        parents = {n['id']: n for n in nodes}
        prefix = view(nodes, workers, k)
        seq = len(nodes)
        def attempt(item):
            slot, parent = item
            return generate(deepcopy(parents[parent]), deepcopy(prefix), deepcopy(history), seq + slot)
        # map retains the chosen batch order regardless of completion timing.
        with ThreadPoolExecutor(max_workers=workers) as executor:
            outcomes = list(executor.map(attempt, enumerate(batch)))
        additions = []
        for offset, (parent, outcome) in enumerate(zip(batch, outcomes)):
            child = {**outcome, 'id': f'n{seq + offset}', 'seq': seq + offset, 'parent': parent}
            nodes.append(child)
            additions.append(child['id'])
        validate_tree(tree)
        tree['rounds'].append({'parents': batch, 'revealed': additions})
    else:
        tree['stop'] = 'round_limit'
    return tree
