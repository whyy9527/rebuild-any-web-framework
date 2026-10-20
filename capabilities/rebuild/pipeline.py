"""Compatibility batch controller; native Goal workflow is the default path.

A pipeline owns only batch/phase progression. It does not generate observations
or edits: the current Codex follows next_action, then executes step to check the
stage. Harness owns attempts/budgets only in that explicitly selected legacy
mode. Batch completion is never full-product Goal completion. Real model
continuation requires separate host evidence.
"""
import json
from pathlib import Path
import time
import uuid

from capabilities.exploration.harness import Harness
from capabilities.exploration.storage import digest, save
from capabilities.rebuild.contracts import coverage, freeze, load, local_file, verify
from runtime.runner import input_manifest

ACTIONS = {
    'explore': 'Observe the explicit reference scope. Record evidence and unknown behaviors; create the shared contract and adapters.',
    'specify': 'Validate executable actions, common fixture and preconditions. Keep unknowns separate and label product decisions.',
    'reference': 'Run reference verification. Repair incorrect discovery/specification from actual evidence, not to fit candidate code.',
    'freeze': 'Freeze the reference-confirmed batch. Do not change acceptance during implementation.',
    'implement': 'Implement candidate; read actual differences and repair product code. Keep frozen acceptance intact.',
    'discover': 'Explore error, boundary, exit, recovery and state links beyond initial scenarios. Record a discovery audit and next revision.',
    'review': 'Recompute coverage against current source and inputs. Report remaining unknowns and independent UI/visual/model evaluation limits.',
    'complete': 'The configured pipeline batch is complete; independent product/UI/model evaluations remain separate.',
}
CATEGORIES = {'normal', 'error', 'boundary', 'exit', 'recovery', 'state_link'}


class Pipeline:
    def __init__(self, workspace):
        self.root = Path(workspace).resolve()
        self.directory = self.root / '.codex/rebuild'
        self.directory.mkdir(parents=True, exist_ok=True)
        self.lock_owner = Harness(self.directory)

    def path(self, run_id):
        return self.lock_owner.path(run_id)

    def read(self, run_id):
        return json.loads(self.path(run_id).read_text())

    def start(self, specification, targets, max_steps=50, max_seconds=3600):
        if type(max_steps) is not int or not 1 <= max_steps <= 1000 or type(max_seconds) is not int or not 1 <= max_seconds <= 86400:
            raise ValueError('explicit finite pipeline guardrails required')
        for name in (specification, targets):
            if Path(name).is_absolute() or '..' in Path(name).parts or not name:
                raise ValueError('relative contract paths required')
        state = {'schema_version': 1, 'id': uuid.uuid4().hex, 'stage': 'explore', 'specification': specification, 'targets': targets,
                 'deadline': time.time()+max_seconds, 'max_steps': max_steps, 'steps': 0, 'events': [],
                 'batch': None, 'parent': None, 'reference_receipt': None, 'candidate_receipt': None,
                 'discovery_completed': False, 'discovered_ids': [], 'last_error': None}
        with self.lock_owner.lock():
            save(self.path(state['id']), state)
        return state

    def persist_receipt(self, state, label, value):
        path = self.root / 'artifacts/rebuild' / state['id'] / (str(state['steps']) + '-' + label + '.json')
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists():
            raise ValueError('receipt path already exists')
        save(path, value)
        return path.relative_to(self.root).as_posix()

    def document(self, name):
        return json.loads(local_file(self.root, name).read_text())

    def status(self, run_id):
        state = self.read(run_id)
        result = {**state, 'next_action': ACTIONS.get(state['stage'], 'Stop; the pipeline exhausted its guardrail.')}
        if state['stage'] == 'complete':
            contract = load(self.root, state['specification'], state['targets'])
            result['coverage'] = coverage(contract, self.document(state['candidate_receipt']))
            if input_manifest(self.root,state['discovery_paths']) != state['discovery_inputs']:
                raise ValueError('discovery evidence changed after completion')
        return result

    def step(self, run_id, audit_path=None, timeout=30):
        with self.lock_owner.lock():
            state = self.read(run_id)
            if state['stage'] in {'complete', 'budget_exhausted'}:
                return self.status(run_id)
            if state['steps'] >= state['max_steps'] or time.time() >= state['deadline']:
                state['stage'] = 'budget_exhausted'
                save(self.path(run_id), state)
                return state
            state['steps'] += 1
            stage = state['stage']
            event = {'step': state['steps'], 'stage': stage, 'at': time.time()}
            try:
                contract = load(self.root, state['specification'], state['targets'])
                remaining = min(timeout, max(0.001, state['deadline']-time.time()))
                if stage == 'explore':
                    if not any(b['discovery'] == 'observed' for b in contract['spec']['behaviors']):
                        raise ValueError('exploration requires actual reference evidence, not decisions only')
                    state['inventory_digest'] = contract['spec_digest']
                    state['stage'] = 'specify'
                elif stage == 'specify':
                    if contract['spec_digest'] != state['inventory_digest']:
                        state['stage'] = 'explore'
                        raise ValueError('inventory changed; recheck exploration evidence without resetting budget')
                    state['stage'] = 'reference'
                elif stage == 'reference':
                    result = verify(self.root, contract, 'reference', remaining, deadline=state['deadline'])
                    state['reference_receipt'] = self.persist_receipt(state, 'reference', result)
                    event['receipt'] = state['reference_receipt']
                    if result['status'] != 'pass':
                        raise ValueError('reference verification failed; inspect ' + state['reference_receipt'])
                    state['stage'] = 'freeze'
                elif stage == 'freeze':
                    reference = self.document(state['reference_receipt'])
                    parent = self.document(state['parent']) if state['parent'] else None
                    batch = freeze(contract, reference, parent)
                    state['batch'] = self.persist_receipt(state, 'batch', batch)
                    event['receipt'] = state['batch']
                    state['stage'] = 'implement'
                elif stage == 'implement':
                    result = verify(self.root, contract, 'candidate', remaining, self.document(state['batch']), deadline=state['deadline'])
                    state['candidate_receipt'] = self.persist_receipt(state, 'candidate', result)
                    event['receipt'] = state['candidate_receipt']
                    if result['status'] != 'pass':
                        raise ValueError('candidate verification failed; inspect ' + state['candidate_receipt'])
                    state['stage'] = 'review' if state['discovery_completed'] else 'discover'
                elif stage == 'discover':
                    if not audit_path:
                        raise ValueError('independent discovery audit is required')
                    audit = self.document(audit_path)
                    batch = self.document(state['batch'])
                    if audit.get('parent_batch_digest') != digest(batch):
                        raise ValueError('discovery audit must bind to the prior frozen batch')
                    checks = audit.get('checks', {})
                    if set(checks) != CATEGORIES:
                        raise ValueError('discovery must inspect normal/error/boundary/exit/recovery/state_link')
                    for evidence in checks.values():
                        local_file(self.root, evidence)
                    discovery_paths = sorted(set([audit_path, *checks.values()]))
                    discovered = [b['id'] for b in contract['spec']['behaviors']
                                  if b['discovery'] == 'observed' and b['id'] not in batch['scenario_digests']]
                    if not discovered or contract['spec'].get('parent_digest') != digest(batch):
                        raise ValueError('record at least one newly observed behavior in a parent-linked revision')
                    state.update(parent=state['batch'], reference_receipt=None, candidate_receipt=None,
                                 discovery_completed=True, discovered_ids=discovered,
                                 discovery_paths=discovery_paths,discovery_inputs=input_manifest(self.root,discovery_paths),
                                 discovery_audit_digest=digest(audit), inventory_digest=contract['spec_digest'], stage='reference')
                elif stage == 'review':
                    if input_manifest(self.root,state['discovery_paths']) != state['discovery_inputs']:
                        raise ValueError('discovery evidence changed since exploration')
                    result = coverage(contract, self.document(state['candidate_receipt']))
                    if result['unknown_total'] or any(b['status'] != 'pass' for b in result['rows']):
                        raise ValueError('bounded inventory still contains unknown or nonpassing behaviors')
                    if not state['discovery_completed'] or not state['discovered_ids']:
                        raise ValueError('initial acceptance is insufficient; discovery cycle is required')
                    state['stage'] = 'complete'
                event.update(status='pass', next_stage=state['stage'], spec_digest=contract['spec_digest'])
                state['last_error'] = None
            except (ValueError, OSError, KeyError, TypeError) as error:
                state['last_error'] = str(error).replace(str(self.root), '<workspace>')
                event.update(status='fail', error=state['last_error'])
            state['events'].append(event)
            save(self.path(run_id), state)
            return {**state, 'next_action': ACTIONS.get(state['stage'], 'Stop.')}
