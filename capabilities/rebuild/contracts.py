"""One assertion owner; adapters receive actions, never expected answers.

Local trusted adapters execute real browser/native actions. Their protocol is not
attestation: a test double exercises this module, but cannot prove UI behavior.
"""
import json
import math
from pathlib import Path
import re
import time
import tempfile

from capabilities.exploration.storage import digest
from runtime.runner import evaluate, input_manifest, manifest

MARKER = 'APP_REBUILD_RESULT '
LAYERS = {'browser_ui', 'native_ui', 'core', 'test_double'}
KINDS = {'original_online', 'local_reference', 'candidate'}


def local_file(root, name, *, must_exist=True):
    require_text(name, 'contract path')
    path = Path(name)
    if path.is_absolute() or '..' in path.parts or not (root / path).resolve().is_relative_to(root):
        raise ValueError('contract files must be inside the explicit workspace')
    if must_exist and not (root / path).is_file():
        raise ValueError('missing contract input: ' + name)
    return root / path


def require_text(value, field):
    if not isinstance(value, str) or not value.strip():
        raise ValueError('nonempty ' + field + ' required')


def load(root, specification, targets):
    root = Path(root).resolve()
    spec = json.loads(local_file(root, specification).read_text())
    config = json.loads(local_file(root, targets).read_text())
    if spec.get('schema_version') != 1 or config.get('schema_version') != 1:
        raise ValueError('schema_version 1 required')
    require_text(spec.get('revision'), 'revision')
    source = spec.get('source', {})
    for field in ('kind', 'version', 'date', 'scope', 'reset_limitations'):
        require_text(source.get(field), 'source.' + field)
    if source['kind'] not in KINDS - {'candidate'}:
        raise ValueError('source must distinguish online original from local reference')
    fixture = json.loads(local_file(root, spec.get('fixture', '')).read_text())
    if not isinstance(fixture.get('initial_state'), dict) or not fixture['initial_state']:
        raise ValueError('fixture.initial_state must declare an observable reset state')
    paths = [specification, targets, spec['fixture']]
    seen = set()
    if not isinstance(spec.get('behaviors'), list) or not spec['behaviors']:
        raise ValueError('nonempty behavior inventory required')
    for behavior in spec['behaviors']:
        identifier = behavior.get('id')
        if not isinstance(identifier, str) or not re.fullmatch(r'[a-zA-Z0-9_-]+', identifier) or identifier in seen:
            raise ValueError('unique stable behavior id required')
        seen.add(identifier)
        require_text(behavior.get('description'), 'behavior description')
        discovery = behavior.get('discovery')
        if discovery not in ('unknown', 'observed', 'decision'):
            raise ValueError('discovery must be unknown, observed or decision')
        if discovery == 'observed':
            if not behavior.get('evidence'):
                raise ValueError('observed behavior requires evidence files')
            for evidence in behavior['evidence']:
                local_file(root, evidence)
                paths.append(evidence)
        if discovery == 'decision':
            require_text(behavior.get('rationale'), 'product decision rationale')
        if discovery == 'unknown':
            if behavior.get('steps'):
                raise ValueError('unknown behavior cannot contain asserted steps')
            continue
        if not isinstance(behavior.get('precondition'), dict):
            raise ValueError('explicit precondition required')
        if not isinstance(behavior.get('steps'), list) or not behavior['steps']:
            raise ValueError('known behavior requires executable steps')
        for step in behavior['steps']:
            if not isinstance(step.get('action'), dict) or not step['action']:
                raise ValueError('nonempty action required')
            if not isinstance(step.get('expect'), dict) or not step['expect']:
                raise ValueError('nonempty expected observation required')
    if not isinstance(config.get('targets'), dict) or set(config['targets']) != {'reference', 'candidate'}:
        raise ValueError('explicit reference and candidate targets required')
    for name, target in config['targets'].items():
        if target.get('kind') not in KINDS or target.get('layer') not in LAYERS:
            raise ValueError('explicit target kind and verification layer required')
        if (name == 'reference' and target['kind'] != source['kind']) or (name == 'candidate' and target['kind'] != 'candidate'):
            raise ValueError('target kind must match declared source and role')
        argv = target.get('command')
        if not isinstance(argv, list) or not argv or any(not isinstance(v, str) or not v for v in argv):
            raise ValueError('explicit adapter argv required')
        declared = target.get('acceptance_paths')
        if not isinstance(declared, list) or not declared:
            raise ValueError('declare adapter and acceptance dependencies')
        paths.extend(declared)
    inputs = input_manifest(root, sorted(set(paths)))
    if any(value is None for value in inputs.values()):
        raise ValueError('declared acceptance inputs must exist')
    return {'workspace': root, 'spec': spec, 'targets': config, 'fixture': fixture, 'inputs': inputs,
            'source_digest': digest(manifest(root)),
            'paths': sorted(set(paths)), 'spec_digest': digest(spec), 'targets_digest': digest(config)}


def differences(expected, actual, prefix='state'):
    """Dict subsets allow extra UI fields; lists and primitive types are exact."""
    if type(expected) is not type(actual):
        return [prefix + ': type differs']
    if isinstance(expected, dict):
        result = []
        for key, value in expected.items():
            result.extend([prefix + '.' + key + ': missing'] if key not in actual else differences(value, actual[key], prefix + '.' + key))
        return result
    if isinstance(expected, list):
        if len(expected) != len(actual):
            return [prefix + ': length differs']
        return [issue for i, value in enumerate(expected) for issue in differences(value, actual[i], prefix + '[' + str(i) + ']')]
    return [] if expected == actual else [prefix + ': expected ' + repr(expected) + ', got ' + repr(actual)]


def call(root, target, request, timeout):
    with tempfile.TemporaryDirectory(prefix='rebuild-bytecode-') as cache:
        receipt = evaluate(root, target['command'], timeout=timeout,
                           input_text=json.dumps(request, ensure_ascii=False),
                           environment={'PYTHONDONTWRITEBYTECODE': '1', 'PYTHONPYCACHEPREFIX': cache})
    receipt.pop('source_files', None)
    if receipt['status'] != 'pass':
        return receipt, None
    lines = [line[len(MARKER):] for line in receipt['output'].splitlines() if line.startswith(MARKER)]
    try:
        if len(lines) != 1 or receipt['output_truncated']:
            raise ValueError('exactly one complete protocol result required')
        response = json.loads(lines[0])
        if not isinstance(response, dict) or response.get('operation') != request['operation']:
            raise ValueError('adapter operation mismatch')
        if 'status' in response:
            if response['status'] not in {'unavailable', 'fail', 'invalid'}:
                raise ValueError('adapters report errors, never self-certify success')
            require_text(response.get('reason'), 'adapter failure reason')
            receipt.update(status=response['status'], reason=response['reason'])
            return receipt, None
    except (ValueError, TypeError) as error:
        receipt.update(status='invalid', protocol_error=str(error))
        return receipt, None
    return receipt, response


def verify(root, contract, target_name, timeout=30, frozen=None, deadline=None):
    root = Path(root).resolve()
    if not math.isfinite(timeout) or timeout <= 0 or (deadline is not None and not math.isfinite(deadline)):
        raise ValueError('finite positive adapter timeout and finite deadline required')
    if input_manifest(root, contract['paths']) != contract['inputs']:
        raise ValueError('contract inputs changed after loading')
    if target_name not in contract['targets']['targets']:
        raise ValueError('unknown target')
    if frozen is not None:
        if frozen.get('kind') != 'frozen_batch' or not re.fullmatch('[a-f0-9]{64}', frozen.get('reference_receipt_digest', '')):
            raise ValueError('reference-confirmed frozen batch required')
        for key in ('spec_digest', 'targets_digest', 'inputs'):
            if frozen.get(key) != contract[key]:
                raise ValueError('frozen contract changed: ' + key)
    if target_name == 'candidate' and frozen is None:
        raise ValueError('candidate verification requires a reference-confirmed frozen batch')
    target = contract['targets']['targets'][target_name]
    report = {'schema_version': 1, 'kind': 'behavior_verification', 'target': target_name,
              'target_kind': target['kind'], 'layer': target['layer'], 'revision': contract['spec']['revision'],
              'spec_digest': contract['spec_digest'], 'targets_digest': contract['targets_digest'],
              'source_digest': digest(manifest(root)),
              'inputs': contract['inputs'], 'behaviors': [], 'lifecycle': [], 'created_at': time.time()}
    def execute(request, cleanup=False):
        remaining = timeout if deadline is None else min(timeout, deadline-time.time())
        if cleanup:
            remaining = min(timeout, 5)  # Explicit bounded cleanup allowance, even after task deadline.
        if remaining <= 0:
            return {'status': 'timeout', 'output': 'Not executed: batch deadline exhausted', 'wall_seconds': 0}, None
        return call(root, target, request, remaining)
    def operation(name, **fields):
        result, response = execute({'operation': name, 'fixture': contract['fixture'], **fields}, cleanup=name == 'stop')
        report['lifecycle'].append({'operation': name, 'receipt': result})
        return result, response
    try:
        start, _ = operation('start')
        for behavior in contract['spec']['behaviors']:
            item = {'id': behavior['id'], 'discovery': behavior['discovery'], 'status': 'unknown'}
            report['behaviors'].append(item)
            if behavior['discovery'] == 'unknown':
                continue
            if start['status'] != 'pass':
                item.update(status='unavailable', reason='target startup failed')
                continue
            reset, response = operation('reset')
            problems = differences(contract['fixture']['initial_state'], response.get('state')) if response else []
            if reset['status'] != 'pass' or problems:
                item.update(status='unavailable', reason='reset failed', differences=problems)
                continue
            request = {'operation': 'scenario', 'fixture': contract['fixture'], 'scenario_id': behavior['id'],
                       'precondition': behavior['precondition'], 'actions': [s['action'] for s in behavior['steps']]}
            result, response = execute(request)
            item.update(status=result['status'], receipt=result)
            if response is None:
                continue
            precondition_errors = differences(behavior['precondition'], response.get('precondition_state'), 'precondition')
            if precondition_errors:
                item.update(status='invalid', reason='scenario precondition was not established', differences=precondition_errors)
                continue
            observations = response.get('observations')
            if response.get('scenario_id') != behavior['id'] or not isinstance(observations, list) or len(observations) != len(behavior['steps']):
                item.update(status='invalid', reason='scenario identity or executed step count mismatch')
                continue
            problems = []
            for index, (step, observation) in enumerate(zip(behavior['steps'], observations)):
                if not isinstance(observation, dict) or type(observation.get('step')) is not int or observation['step'] != index:
                    problems.append('observation step mismatch: ' + str(index))
                else:
                    problems.extend(differences(step['expect'], observation.get('state'), 'step[' + str(index) + ']'))
            item.update(status='fail' if problems else 'pass', differences=problems, observations=observations)
        reset, response = operation('reset')
        if response and differences(contract['fixture']['initial_state'], response.get('state')):
            reset.update(status='fail', reason='final reset did not restore fixture')
    finally:
        operation('stop')
    # Detect changing tests, adapters, evidence, config or fixtures during a run.
    try:
        intact = input_manifest(root, contract['paths']) == contract['inputs'] and digest(manifest(root)) == report['source_digest']
    except ValueError:
        intact = False
    if not intact:
        report['integrity'] = 'changed'
    else:
        report['integrity'] = 'verified'
    known = [item for item in report['behaviors'] if item['discovery'] != 'unknown']
    report['status'] = ('pass' if known and all(b['status'] == 'pass' for b in known)
                        and all(e['receipt']['status'] == 'pass' for e in report['lifecycle'])
                        and report['integrity'] == 'verified' else 'fail')
    report['counts'] = {status: sum(item['status'] == status for item in report['behaviors'])
                        for status in ('unknown', 'pass', 'fail', 'invalid', 'unavailable', 'timeout')}
    return report


def freeze(contract, reference, parent=None):
    if reference.get('kind') != 'behavior_verification' or reference.get('target') != 'reference' or reference.get('status') != 'pass':
        raise ValueError('a passing real reference receipt is required before freezing')
    for key in ('spec_digest', 'targets_digest', 'inputs'):
        if reference.get(key) != contract[key]:
            raise ValueError('reference confirmation is stale: ' + key)
    scenarios = {b['id']: digest({'precondition': b['precondition'], 'steps': b['steps']})
                 for b in contract['spec']['behaviors'] if b['discovery'] != 'unknown'}
    if not scenarios or reference.get('integrity') != 'verified' or reference.get('target_kind') != contract['spec']['source']['kind']:
        raise ValueError('reference must confirm at least one scenario with intact inputs')
    if reference.get('source_digest') != digest(manifest(contract['workspace'])):
        raise ValueError('reference source changed since confirmation')
    verified = {b['id']: b['status'] for b in reference.get('behaviors', [])}
    if any(verified.get(identifier) != 'pass' for identifier in scenarios):
        raise ValueError('reference has not confirmed every executable behavior')
    parent_digest = contract['spec'].get('parent_digest')
    if parent_digest is not None or parent is not None:
        if parent is None or parent.get('kind') != 'frozen_batch' or digest(parent) != parent_digest:
            raise ValueError('new batch must identify its actual frozen parent')
        if any(scenarios.get(identifier) != value for identifier, value in parent['scenario_digests'].items()):
            raise ValueError('incremental batch cannot remove or weaken prior scenarios')
    return {'schema_version': 1, 'kind': 'frozen_batch', 'revision': contract['spec']['revision'],
            'spec_digest': contract['spec_digest'], 'targets_digest': contract['targets_digest'],
            'inputs': contract['inputs'], 'reference_receipt_digest': digest(reference),
            'reference_kind': reference['target_kind'], 'reference_layer': reference['layer'],
            'parent_digest': parent_digest, 'scenario_digests': scenarios, 'created_at': time.time()}


def coverage(contract, receipt=None):
    if receipt is not None and any(receipt.get(key) != contract[key] for key in ('spec_digest', 'targets_digest', 'inputs')):
        raise ValueError('cannot use stale receipts for current coverage')
    if receipt is not None and receipt.get('source_digest') != digest(manifest(contract['workspace'])):
        raise ValueError('cannot use stale artifact results for current coverage')
    results = {item['id']: item for item in receipt['behaviors']} if receipt else {}
    rows = [{'id': b['id'], 'discovery': b['discovery'],
             'status': results.get(b['id'], {}).get('status', 'unknown' if b['discovery'] == 'unknown' else 'not_run')}
            for b in contract['spec']['behaviors']]
    return {'revision': contract['spec']['revision'], 'spec_digest': contract['spec_digest'],
            'rows': rows, 'known_total': sum(b['discovery'] != 'unknown' for b in rows),
            'unknown_total': sum(b['discovery'] == 'unknown' for b in rows),
            'receipt_digest': digest(receipt) if receipt else None}
