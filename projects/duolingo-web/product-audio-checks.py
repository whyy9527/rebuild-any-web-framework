"""Record actual UI-triggered system output of an isolated owned Swift client.

Requires macOS Screen Recording/Accessibility access already granted to this
runtime. No microphone, other applications, or user progress are captured.
Run after building LingoSeed: python3 projects/duolingo-web/product-audio-checks.py artifacts/product-v3/audio-02
"""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time

root = Path.cwd().resolve()
out = Path(sys.argv[1]).resolve()
out.mkdir(parents=True, exist_ok=True)
progress = out / 'progress.json'
if progress.exists():
    raise SystemExit('Choose a fresh output directory; existing progress is preserved')
recorder = out / 'capture-owned-audio'
subprocess.run(['swiftc', '-parse-as-library', 'projects/duolingo-web/capture-owned-audio.swift', '-o', str(recorder)], check=True)
binary = root / 'projects/education-swift/.build/debug/LingoSeed'
log = (out / 'app.log').open('wb')
child = subprocess.Popen([str(binary), '--fixture', str(root / 'projects/duolingo-web/fixture-v2.json'), '--progress', str(progress)], stdout=log, stderr=log, start_new_session=True)
(out / 'process.json').write_text(json.dumps({'pid': child.pid, 'progress': str(progress)}))
results = {}
scenarios = [
    ('pronunciation', ['start-lesson', 'option-morning', 'pronounce'], False),
    ('correct', ['check'], False),
    ('incorrect', ['continue', 'option-bye', 'check'], False),
    ('muted-matching', ['sound-toggle', 'continue', 'pair-left-morning', 'pair-right-morning', 'pair-left-thanks', 'pair-right-thanks', 'pair-left-bye', 'pair-right-bye'], True),
    ('restored-completion', ['sound-toggle', 'continue', 'option-thanks', 'check', 'continue'], False),
    ('matching-correct', ['return-path', 'start-lesson', 'option-morning', 'check', 'continue', 'option-thanks', 'check', 'continue', 'pair-left-morning', 'pair-right-morning', 'pair-left-thanks', 'pair-right-thanks', 'pair-left-bye', 'pair-right-bye'], False),
    ('word-pronunciation', ['continue', 'return-path', 'start-lesson-1', 'option-hello', 'check', 'continue', 'pronounce'], False),
]
try:
    time.sleep(1)
    for name, actions, silent in scenarios:
        action_file = out / (name + '-actions.json')
        action_file.write_text(json.dumps(actions))
        audio = out / (name + '.wav')
        run = subprocess.run([str(recorder), str(child.pid), str(audio), '7', str(action_file)], capture_output=True, text=True, timeout=30)
        (out / (name + '.log')).write_text(run.stdout + run.stderr)
        if run.returncode:
            raise RuntimeError(name + ': capture or owned UI actions failed')
        receipt = json.loads(audio.with_suffix('.wav.json').read_text())
        if receipt.get('failure') or not receipt['samples'] or len(receipt['ui_actions']) != len(actions):
            raise RuntimeError(name + ': incomplete recording or UI actions')
        # Nonzero output proves this is more than a player-call log. The muted
        # run must contain actual actions and sampled silence throughout.
        if silent:
            if receipt['peak'] != 0 or receipt['rms'] != 0:
                raise RuntimeError('Muted application emitted system-output audio')
        elif receipt['peak'] < 0.005 or receipt['rms'] < 0.0001:
            raise RuntimeError(name + ': expected system-output audio is absent')
        receipt['sha256'] = hashlib.sha256(audio.read_bytes()).hexdigest()
        receipt['bytes'] = audio.stat().st_size
        receipt['status'] = 'pass'
        results[name] = receipt
        print('PASS', name, 'peak', round(receipt['peak'], 5), flush=True)
    status = 'pass'
except Exception as error:
    status = 'fail'
    results['failure'] = str(error)
finally:
    child.terminate()
    try:
        child.wait(timeout=3)
    except subprocess.TimeoutExpired:
        child.kill(); child.wait()
    log.close()
    receipt = {'kind': 'native_ui_audio_loopback_suite', 'status': status, 'scenarios': results,
               'binary_sha256': hashlib.sha256(binary.read_bytes()).hexdigest(),
               'source_sha256': {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in Path('projects/education-swift/Sources').rglob('*.swift')},
               'scope': 'Only owned application system output, microphone disabled; actual AX actions timed inside each recording',
               'limitations': ['Verifies digital system-output signal, not physical speaker volume or human preference', 'Original synthesized sounds and system English voice, not Duolingo recordings']}
    (out / 'result.json').write_text(json.dumps(receipt, indent=2) + '\n')
if status != 'pass':
    raise SystemExit(results['failure'])
print('PASS seven actual UI-triggered output recordings including word instruction and sampled mute silence')
