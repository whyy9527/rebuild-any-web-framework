"""Add source-derived profile/navigation facts without relaxing v56 frontend checks."""
import argparse
import json
from pathlib import Path

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[1]
EVIDENCE = BASE / 'evidence/english-profile-frontier-v1'


def build():
    contract = json.loads((BASE / 'frontend-english-v56.json').read_text())
    prior = contract['requirements'][:]
    reference = json.loads((EVIDENCE / 'reference.json').read_text())
    for stem in ['profile', 'dismissed', 'achievements']:
        source_path = EVIDENCE / 'source' / (stem + '.json')
        source = json.loads(source_path.read_text())
        key = 'profile-frontier-' + stem
        facts = {'guest_profile_present': '2026 年 10 月加入' in source['snapshot'],
                 'guest_introduction_present': any(a['name'] == '下次再说' for a in source['actions']),
                 'guest_error_present': 'heading "Error 404"' in source['snapshot']}
        reference['states'][key]['interactions'] = facts
        for name, value in facts.items():
            contract['requirements'].append(dict(id=key + '-' + name, state=key,
                kind='interaction_boolean', field=name, expected=value,
                evidence=[str(source_path.relative_to(ROOT))]))
    contract.update(revision='english-v57', parent_revision='english-v56', changes=[
        'Actual independent profile/introduction/error visibility, guarding the stale top-level renderer failure'])
    assert contract['requirements'][:len(prior)] == prior
    return contract, reference


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out-dir', required=True)
    output = Path(parser.parse_args().out_dir)
    output.mkdir(parents=True, exist_ok=False)
    for name, value in zip(['contract.json', 'reference.json'], build()):
        (output / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')
