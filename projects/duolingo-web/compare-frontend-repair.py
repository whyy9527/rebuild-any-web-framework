"""Bind a fresh fourth-lesson observation and compare the unchanged strict v80 mold."""
import argparse
import json
from pathlib import Path
import subprocess
import sys

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--observed', required=True)
p.add_argument('--out-dir', required=True)
a = p.parse_args()
out = Path(a.out_dir)
out.mkdir(parents=True, exist_ok=False)
d = json.loads(Path(a.observed).read_text())
assert d['kind'] == 'owned_native_ax_observation' and d['candidate_binary_sha256']
d['states'] = {'unit12-l4-' + k: v for k, v in d['states'].items()}
if 'unit12-l4-home-after' in d['states']:
    d['states']['unit12-l4-home-after-fixed'] = d['states']['unit12-l4-home-after']
source = out / 'prefixed.json'
source.write_text(json.dumps(d, ensure_ascii=False, indent=2) + '\n')
subprocess.run([sys.executable, 'projects/duolingo-web/bind-frontend-aliases.py',
    '--observed', str(source), '--aliases', 'projects/duolingo-web/evidence/english-frontend-repair-v80/aliases.json',
    '--out', str(out / 'bound.json')], check=True)
result = subprocess.run([sys.executable, '-m', 'capabilities.rebuild.frontend',
    '--contract', 'projects/duolingo-web/frontend-english-v80.json', '--observed', str(out / 'bound.json'),
    '--out', str(out / 'frontend.json')])
raise SystemExit(result.returncode)
