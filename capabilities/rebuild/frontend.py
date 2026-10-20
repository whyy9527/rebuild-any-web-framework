"""Compare observed frontend requirements, independently of semantic E2E.

Drivers collect facts; they do not supply pass flags. Image requirements read
actual captures and compare normalized pixels independently of text checks.
Neither text nor image checks certify audio or unvisited states.
"""
import argparse
import json
import math
from pathlib import Path

from capabilities.exploration.storage import digest
from capabilities.rebuild.contracts import local_file


def compare(root, contract, observed):
    root = Path(root).resolve()
    rows = []
    for requirement in contract['requirements']:
        row = {'id': requirement['id'], 'state': requirement['state']}
        evidence = requirement.get('evidence', [])
        if not evidence:
            raise ValueError('reference evidence required')
        for name in evidence:
            local_file(root, name)
        state = observed.get('states', {}).get(requirement['state'])
        if state is not None and 'browser_capture' in requirement and requirement['kind'] != 'pending':
            from .browser import comparison_gate, observed_state, read_receipt
            gate = comparison_gate(root, requirement, state)
            if gate is None:
                reference_path = requirement['browser_capture']['reference']
                reference_state = observed_state(root, read_receipt(root, reference_path), reference_path)
                reference_requirement = {key: value for key, value in requirement.items() if key != 'browser_capture'}
                reference_result = compare(root, {'requirements': [reference_requirement]},
                                           {'states': {requirement['state']: reference_state}})
                if reference_result['status'] != 'pass':
                    gate = {'status': 'unavailable', 'reason': 'Reference browser evidence does not satisfy the shared assertion',
                            'reference_result': reference_result['rows'][0]}
            if gate:
                row.update(gate)
                rows.append(row)
                continue
        if requirement['kind'] == 'pending':
            row.update(status='not_run', reason=requirement['description'])
        elif state is None:
            row.update(status='not_run', reason='Driver has not visited this reference state')
        elif requirement['kind'] == 'image_pixels':
            from .images import compare_capture
            row.update(compare_capture(root, requirement, state))
        elif requirement['kind'] == 'accessible_text':
            expected = requirement['text']
            actual = state.get('accessible_text')
            if not isinstance(actual, list):
                row.update(status='unavailable', reason='Driver did not collect accessible text')
            else:
                found = expected.casefold() in {str(text).strip().casefold() for text in actual}
                row.update(status='pass' if found else 'fail', expected=expected)
        elif requirement['kind'] == 'capture_dimensions':
            expected = requirement['pixels']
            actual = state.get('capture_pixels')
            row.update(status='unavailable' if actual is None else 'pass' if actual == expected else 'fail',
                       expected=expected, actual=actual,
                       reason='Comparable capture dimensions only; does not prove visual equivalence')
        elif requirement['kind'] == 'interaction_boolean':
            actual = state.get('interactions', {}).get(requirement['field'])
            row.update(status='unavailable' if type(actual) is not bool else 'pass' if actual == requirement['expected'] else 'fail',
                       expected=requirement['expected'], actual=actual)
        elif requirement['kind'] == 'element_role':
            actual = state.get('elements', {}).get(requirement['element'], {}).get('role')
            # Compare a common semantic role across DOM and macOS AX drivers.
            actual = {'AXRadioButton': 'radio', 'AXButton': 'button', 'AXCheckBox': 'checkbox', 'AXLink': 'link', 'AXMenuItem': 'menuitem', 'AXTextField': 'textbox'}.get(actual, actual)
            row.update(status='unavailable' if actual is None else 'pass' if actual == requirement['role'] else 'fail',
                       expected=requirement['role'], actual=actual)
        elif requirement['kind'] == 'element_value':
            expected = requirement['value']
            if not isinstance(expected, str):
                raise ValueError('Element value contract must be a string')
            actual = state.get('elements', {}).get(requirement['element'], {}).get('value')
            row.update(status='unavailable' if not isinstance(actual, str) else 'pass' if actual == expected else 'fail',
                       expected=expected, actual=actual)
        elif requirement['kind'] == 'element_boolean':
            field = requirement['field']
            if field not in ('enabled', 'checked') or type(requirement['expected']) is not bool:
                raise ValueError('Unsupported element boolean contract')
            actual = state.get('elements', {}).get(requirement['element'], {}).get(field)
            row.update(status='unavailable' if type(actual) is not bool else 'pass' if actual == requirement['expected'] else 'fail',
                       expected=requirement['expected'], actual=actual)
        elif requirement['kind'] == 'pixel_color':
            point, expected = requirement['point'], requirement['rgb']
            valid_point = isinstance(point, list) and len(point) == 2 and all(type(v) is int and v >= 0 for v in point)
            valid_rgb = lambda rgb: isinstance(rgb, list) and len(rgb) == 3 and all(type(v) is int and 0 <= v <= 255 for v in rgb)
            if not valid_point or not valid_rgb(expected):
                raise ValueError('Invalid pixel color contract')
            actual = state.get('pixel_samples', {}).get(','.join(map(str, point)))
            row.update(status='unavailable' if not valid_rgb(actual) or state.get('pixel_color_space') != 'sRGB' else 'pass' if actual == expected else 'fail',
                       expected=expected, actual=actual,
                       reason='Exact screenshot pixel only; does not prove whole-image equivalence')
        elif requirement['kind'] == 'element_geometry':
            expected = requirement['rect']
            tolerance = requirement['tolerance_points']
            if not isinstance(expected, list) or len(expected) != 4 or not all(type(v) in (int, float) and math.isfinite(v) for v in expected) or type(tolerance) not in (int, float) or not math.isfinite(tolerance) or tolerance < 0:
                raise ValueError('Invalid geometry contract')
            actual = state.get('elements', {}).get(requirement['element'], {}).get('rect')
            valid = isinstance(actual, list) and len(actual) == 4 and all(type(v) in (int, float) and math.isfinite(v) for v in actual)
            if 'relative_to_state' in requirement:
                origin_state = observed.get('states', {}).get(requirement['relative_to_state'])
                if origin_state is None:
                    row.update(status='not_run', reason='Driver has not visited the relative geometry origin state')
                    rows.append(row)
                    continue
                origin = origin_state.get('elements', {}).get(requirement['element'], {}).get('rect')
                origin_valid = isinstance(origin, list) and len(origin) == 4 and all(type(v) in (int, float) and math.isfinite(v) for v in origin)
                valid = valid and origin_valid
                actual = [a - b for a, b in zip(actual, origin)] if valid else None
                row['relative_to_state'] = requirement['relative_to_state']
            delta = [abs(a - b) for a, b in zip(actual, expected)] if valid else None
            row.update(status='unavailable' if not valid else 'pass' if max(delta) <= tolerance else 'fail',
                       expected=expected, actual=actual, delta_points=delta,
                       reason='Control geometry in content points only; other visual properties remain separate')
        else:
            raise ValueError('Unsupported frontend requirement: ' + requirement['kind'])
        rows.append(row)
    if not rows or len({row['id'] for row in rows}) != len(rows):
        raise ValueError('Nonempty unique frontend requirements required')
    return {'kind': 'frontend_requirements', 'contract_digest': digest(contract),
            'observation_digest': digest(observed), 'rows': rows,
            'status': 'pass' if all(row['status'] == 'pass' for row in rows) else 'fail'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--workspace', default='.')
    parser.add_argument('--contract', required=True)
    parser.add_argument('--observed', required=True)
    parser.add_argument('--out', required=True)
    args = parser.parse_args()
    root = Path(args.workspace).resolve()
    contract = json.loads(local_file(root, args.contract).read_text())
    observed = json.loads(local_file(root, args.observed).read_text())
    result = compare(root, contract, observed)
    output = root / args.out
    with output.open('x') as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
    print(json.dumps({'status': result['status'], 'counts': {
        status: sum(row['status'] == status for row in result['rows'])
        for status in ['pass', 'fail', 'not_run', 'unavailable']}}, ensure_ascii=False))
    return 0 if result['status'] == 'pass' else 1


if __name__ == '__main__':
    raise SystemExit(main())
