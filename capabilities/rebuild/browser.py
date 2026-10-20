"""Validate browser evidence before the existing frontend assertions run.

Receipts describe trusted local observations, not remote attestation. Stability
means the sampled document did not change; it is not atomic media capture.
"""
import hashlib
import json
import math
from pathlib import Path
import struct

from .contracts import local_file


ARTIFACTS = {'dom', 'screenshot', 'accessibility', 'text'}
PREPARATION = ('environment', 'scroll', 'focus', 'hover')


def valid_sample(sample):
    if not isinstance(sample, dict) or any(k not in sample for k in (*PREPARATION, 'document', 'revision', 'elements', 'url')):
        return False
    environment = sample['environment']
    fields = {'viewport', 'device_scale', 'locale', 'timezone', 'color_scheme', 'reduced_motion', 'service_worker_controlled'}
    if not isinstance(environment, dict) or not fields <= environment.keys():
        return False
    finite = lambda value: type(value) in (int, float) and math.isfinite(value)
    pair = lambda value: isinstance(value, list) and len(value) == 2 and all(finite(v) for v in value)
    return (pair(environment['viewport']) and all(v > 0 for v in environment['viewport'])
            and finite(environment['device_scale']) and environment['device_scale'] > 0
            and all(isinstance(environment[k], str) and environment[k] for k in ('locale', 'timezone'))
            and environment['color_scheme'] in ('light', 'dark')
            and all(type(environment[k]) is bool for k in ('reduced_motion', 'service_worker_controlled'))
            and pair(sample['scroll']) and isinstance(sample['document'], str) and bool(sample['document'])
            and type(sample['revision']) is int and sample['revision'] >= 0
            and isinstance(sample['elements'], dict) and isinstance(sample['hover'], list)
            and (sample['focus'] is None or isinstance(sample['focus'], dict))
            and isinstance(sample['url'], str) and bool(sample['url']))


def read_receipt(root, name):
    value = json.loads(local_file(root, name).read_text())
    if not isinstance(value, dict) or type(value.get('schema_version')) is not int or value['schema_version'] != 1 or value.get('kind') != 'browser_step':
        raise ValueError('browser_step schema_version 1 required')
    return value


def observed_state(root, receipt, name):
    """Project measured receipt facts into the existing frontend state shape."""
    state = {'browser_evidence': name, 'elements': receipt.get('after', {}).get('elements', {})}
    text = receipt['artifacts'].get('text', {})
    if text.get('state') == 'captured':
        state['accessible_text'] = local_file(root, text['path']).read_text().splitlines()
    image = receipt['artifacts'].get('screenshot', {})
    if image.get('state') == 'captured' and 'after' in receipt:
        environment = receipt['after']['environment']
        width, height = environment['viewport']
        state['capture'] = {'path': image['path'], 'content_rect_points': [0, 0, width, height],
                            'backing_scale': environment['device_scale'], 'window_points': [width, height],
                            'state_consistent': receipt.get('before') == receipt['after']}
        raw = local_file(root, image['path']).read_bytes()
        if raw[:8] == b'\x89PNG\r\n\x1a\n' and len(raw) >= 24:
            state['capture_pixels'] = list(struct.unpack('>II', raw[16:24]))
    return state


def evidence_problems(root, receipt, required):
    problems = []
    if not isinstance(receipt, dict) or not isinstance(receipt.get('ready'), dict) or not isinstance(receipt.get('artifacts'), dict):
        return ['browser receipt structure is invalid']
    if receipt.get('action_status') != 'executed':
        problems.append('browser action was not executed')
    if receipt.get('ready', {}).get('status') != 'observed':
        problems.append('browser readiness was not observed')
    if receipt.get('cleanup') != 'released':
        problems.append('browser resources were not released')
    if receipt.get('probe_cleanup') != 'released':
        problems.append('browser probe cleanup was not confirmed')
    before, after = receipt.get('before'), receipt.get('after')
    if not valid_sample(before) or not valid_sample(after):
        problems.append('browser state samples are missing')
    elif before != after:
        problems.append('browser state changed during capture')
    artifacts = receipt.get('artifacts', {})
    requested = receipt.get('requested')
    if not isinstance(requested, list) or not requested or any(not isinstance(k, str) for k in requested) or not set(requested) <= ARTIFACTS:
        return problems + ['browser capture selection is missing or invalid']
    for kind in sorted(set(required) | set(requested)):
        artifact = artifacts.get(kind, {})
        if not isinstance(artifact, dict):
            problems.append(kind + ': invalid artifact')
            continue
        if artifact.get('state') != 'captured':
            problems.append(kind + ': ' + str(artifact.get('state', 'missing')))
            continue
        try:
            raw = local_file(root, artifact.get('path')).read_bytes()
            if type(artifact.get('bytes')) is not int or len(raw) != artifact['bytes']:
                problems.append(kind + ': byte count changed')
            if hashlib.sha256(raw).hexdigest() != artifact.get('sha256'):
                problems.append(kind + ': digest changed')
        except (ValueError, OSError, TypeError):
            problems.append(kind + ': artifact file unavailable')
    return problems


def comparison_gate(root, requirement, state):
    """A declared browser reference makes candidate evidence mandatory."""
    root = Path(root).resolve()
    reference = requirement['browser_capture']
    if not isinstance(reference, dict) or set(reference) != {'reference', 'required'}:
        raise ValueError('browser_capture requires reference and required artifacts')
    required = reference['required']
    if not isinstance(required, list) or not required or any(not isinstance(k, str) for k in required) or not set(required) <= ARTIFACTS:
        raise ValueError('nonempty supported browser artifacts required')
    required = set(required)
    if requirement['kind'] in ('image_pixels', 'capture_dimensions'):
        required.add('screenshot')
    if requirement['kind'] == 'accessible_text':
        required.add('text')
    try:
        original = read_receipt(root, reference['reference'])
        candidate = read_receipt(root, state.get('browser_evidence'))
        problems = ['reference: ' + p for p in evidence_problems(root, original, required)]
        problems += ['candidate: ' + p for p in evidence_problems(root, candidate, required)]
        if original.get('id') != requirement['state'] or candidate.get('id') != requirement['state']:
            problems.append('browser step identity does not match requirement state')
        if 'relative_to_state' in requirement:
            problems.append('relative geometry requires a separately verified origin; browser gate does not support it')
        if not problems:
            for key in PREPARATION:
                if original['after'][key] != candidate['after'][key]:
                    problems.append('browser preparation differs: ' + key)
            # Existing frontend fields must come from this receipt's actual files.
            if 'text' in required:
                text = local_file(root, candidate['artifacts']['text']['path']).read_text()
                if state.get('accessible_text') != text.splitlines():
                    problems.append('candidate text does not match browser evidence')
            if requirement['kind'].startswith('element_'):
                element = requirement.get('element')
                if state.get('elements', {}).get(element) != candidate['after']['elements'].get(element):
                    problems.append('candidate element does not match browser evidence')
            if requirement['kind'] == 'image_pixels':
                capture = state.get('capture', {})
                if not isinstance(capture, dict):
                    capture = {}
                environment = candidate['after']['environment']
                width, height = environment['viewport']
                measured = {'path': candidate['artifacts']['screenshot']['path'],
                            'content_rect_points': [0, 0, width, height],
                            'backing_scale': environment['device_scale'], 'window_points': [width, height]}
                if any(capture.get(k) != v for k, v in measured.items()):
                    problems.append('candidate image does not match browser evidence')
                if requirement['reference_image'] != original['artifacts']['screenshot']['path']:
                    problems.append('reference image does not match browser evidence')
                original_environment = original['after']['environment']
                w, h = original_environment['viewport']
                original_capture = {'path': original['artifacts']['screenshot']['path'],
                                    'content_rect_points': [0, 0, w, h],
                                    'backing_scale': original_environment['device_scale'], 'window_points': [w, h]}
                declared_capture = requirement.get('reference_capture')
                if declared_capture is not None and (not isinstance(declared_capture, dict) or any(declared_capture.get(k) != v for k, v in original_capture.items())):
                    problems.append('reference image geometry does not match browser evidence')
            if requirement['kind'] == 'capture_dimensions':
                raw = local_file(root, candidate['artifacts']['screenshot']['path']).read_bytes()
                if raw[:8] != b'\x89PNG\r\n\x1a\n' or len(raw) < 24:
                    problems.append('candidate screenshot is not a PNG')
                elif state.get('capture_pixels') != list(struct.unpack('>II', raw[16:24])):
                    problems.append('candidate dimensions do not match browser evidence')
    except (ValueError, OSError, KeyError, TypeError) as error:
        problems = ['browser evidence unavailable: ' + str(error).replace(str(root), '<workspace>')]
    return {'status': 'unavailable', 'reason': '; '.join(problems)} if problems else None
