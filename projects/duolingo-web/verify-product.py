"""One product verdict: frozen business E2E AND observed frontend requirements.

Run from repository root. A failed frontend check cannot be hidden by semantic
success. This initial contract is deliberately incomplete and reports that fact.
"""
import argparse
import json
from pathlib import Path
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from capabilities.rebuild.frontend import compare
from capabilities.exploration.storage import digest
from runtime.runner import manifest, input_manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', required=True)
    args = parser.parse_args()
    root = Path.cwd()
    output = root / args.out
    output.mkdir(parents=True, exist_ok=False)
    source = digest(manifest(root))
    resources = digest(input_manifest(root, ['projects/education-swift/Sources/LingoSeed/Resources/Reference']))
    contract_paths = {'frontend': 'projects/duolingo-web/frontend-v4.json',
                      'course': 'projects/duolingo-web/frontend-course-v6.json',
                      'preferences': 'projects/duolingo-web/frontend-preferences-v4.1.json',
                      'guidebook': 'projects/duolingo-web/frontend-guidebook-v6.1.json'}
    contracts = {name: json.loads((root / path).read_text()) for name, path in contract_paths.items()}
    fixture_path = 'projects/duolingo-web/fixture-reference-v6.json'
    inputs = {fixture_path, *contract_paths.values()}
    inputs.update(json.loads((root / fixture_path).read_text())['provenance']['evidence'])
    reference_preferences_path = 'projects/duolingo-web/evidence/exploration-v4/preferences-reference-ack-04.json'
    inputs.add(reference_preferences_path)
    for contract in contracts.values():
        inputs.update(path for row in contract['requirements'] for path in row['evidence'])
    inputs = sorted(inputs)
    reference_inputs = digest(input_manifest(root, inputs))
    business = subprocess.run([sys.executable, '-m', 'workflows.rebuild.cli', 'verify',
        '--workspace', '.', '--spec', 'projects/duolingo-web/spec-v2.json',
        '--targets', 'projects/duolingo-web/targets-v2.json', '--target', 'candidate',
        '--frozen', 'projects/duolingo-web/evidence/batch-v2.json', '--timeout', '360',
        '--max-seconds', '1800', '--out', (output / 'business.json').relative_to(root).as_posix()],
        capture_output=True, text=True, timeout=1850)
    (output / 'business.log').write_text(business.stdout + business.stderr)
    probe = subprocess.run(['swift', 'projects/duolingo-web/observe-frontend.swift', str(output / 'frontend'),
                            'projects/duolingo-web/fixture-reference-v6.json', '--walk-course'],
        capture_output=True, text=True, timeout=90)
    (output / 'frontend.log').write_text(probe.stdout + probe.stderr)
    checks = {}
    for name, contract in contracts.items():
        checks[name] = compare(root, contract, json.loads((output / 'frontend/observed.json').read_text())) if probe.returncode == 0 else {
            'status': 'unavailable', 'reason': 'Actual native frontend probe failed'}
        (output / (name + '.json')).write_text(json.dumps(checks[name], ensure_ascii=False, indent=2) + '\n')
    checks['reference_preferences'] = compare(root, contracts['preferences'], json.loads((root / reference_preferences_path).read_text()))
    (output / 'reference_preferences.json').write_text(json.dumps(checks['reference_preferences'], ensure_ascii=False, indent=2) + '\n')
    unchanged = source == digest(manifest(root))
    resources_unchanged = resources == digest(input_manifest(root, ['projects/education-swift/Sources/LingoSeed/Resources/Reference']))
    inputs_unchanged = reference_inputs == digest(input_manifest(root, inputs))
    result = {'kind': 'combined_product_acceptance', 'source_digest': source,
        'source_unchanged': unchanged, 'resource_digest': resources, 'resources_unchanged': resources_unchanged,
        'reference_inputs_digest': reference_inputs, 'reference_inputs_unchanged': inputs_unchanged,
        'reference_inputs': inputs,
        'business_exit_code': business.returncode, 'course_copy_status': checks['course']['status'],
        'frontend_status': checks['frontend']['status'], 'preferences_status': checks['preferences']['status'],
        'reference_preferences_status': checks['reference_preferences']['status'],
        'status': 'pass' if unchanged and resources_unchanged and inputs_unchanged and business.returncode == 0 and all(check['status'] == 'pass' for check in checks.values()) else 'fail',
        'limitations': ['Frontend inventory expands with exploration',
                        'Reference preferences replay is an actual dated observation, not a fresh online run',
                        'Current pending visual/audio requirements prevent product completion']}
    (output / 'result.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result['status'] == 'pass' else 1


if __name__ == '__main__':
    raise SystemExit(main())
