"""Build the current Swift product before driving real native UI. No assertions."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys

root = Path.cwd().resolve()
request_text = sys.stdin.read()
request = json.loads(request_text)
operation = request.get('operation')
response = {'operation': operation}
if operation == 'stop':
    response['resources'] = []  # The native driver closes every child before returning.
else:
    project = Path('projects/education-swift')
    try:
        build = subprocess.run(['swift', 'build', '--package-path', str(project), '--product', 'LingoSeed'],
                               capture_output=True, text=True, timeout=120)
        if build.returncode:
            response.update(status='unavailable', reason='Current Swift product build failed',
                            build_log=(build.stdout + build.stderr)[-8000:].replace(str(root), '<workspace>').replace('/Library/Developer/CommandLineTools', '<toolchain>'))
        else:
            run = subprocess.run(['swift', 'projects/duolingo-web/native-adapter-v3.swift'], input=request_text,
                                 capture_output=True, text=True, timeout=240)
            lines = [line[len('APP_REBUILD_RESULT '):] for line in run.stdout.splitlines() if line.startswith('APP_REBUILD_RESULT ')]
            if run.returncode or len(lines) != 1:
                response.update(status='invalid', reason='Native driver did not emit exactly one result')
            else:
                response = json.loads(lines[0])
                sources = [project / 'Package.swift', *sorted(project.glob('Sources/**/*.swift'))]
                response['build'] = {'binary_sha256': hashlib.sha256((project / '.build/debug/LingoSeed').read_bytes()).hexdigest(),
                                     'source_sha256': {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in sources}}
    except subprocess.TimeoutExpired:
        response.update(status='unavailable', reason='Build/native driver command exceeded its explicit deadline')
    except (OSError, ValueError):
        response.update(status='invalid', reason='Build/native driver IO or protocol error')
print('APP_REBUILD_RESULT ' + json.dumps(response, ensure_ascii=False))
