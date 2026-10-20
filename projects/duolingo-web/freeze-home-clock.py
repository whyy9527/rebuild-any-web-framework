"""Rebuild v48 and the shared clock scenario from frozen original observations."""
import argparse
import hashlib
import json
from pathlib import Path

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[1]
EVIDENCE = BASE / 'evidence/english-home-clock-v1'


def build():
    contract = json.loads((BASE / 'frontend-english-v47.json').read_text())
    previous = contract['requirements'][:]
    reference = json.loads((BASE / 'evidence/english-home-motion-v1/reference.json').read_text())
    source = json.loads((EVIDENCE / 'source-clock.json').read_text())
    assert source['viewport'] == {'width': 1200, 'height': 732}
    assert source['deadline']['value'] == '2026-10-11T10:00:00Z'
    scenario = {'deadline_epoch_milliseconds': 1791712800000, 'states': []}
    for name, row in zip(['hours', 'minutes', 'seconds'], source['receipts'], strict=True):
        key = 'home-clock-' + name
        image = row['path']
        assert (ROOT / image).is_file() and row['stable_clock_capture']
        assert hashlib.sha256((EVIDENCE / (key + '.svg')).read_bytes()).hexdigest() == row['svg_sha256']
        clock = row['countdown']
        scenario['states'].append({'id': key, 'epoch_milliseconds': clock['history'][-1]['now'], 'expected_text': clock['value']})
        reference['states'][key] = {
            'accessible_text': [clock['value']], 'elements': {'home-league-countdown': {'rect': clock['rect']}},
            'capture': {'path': image, 'content_rect_points': [0, 0, 1200, 732], 'window_points': [1200, 732], 'backing_scale': 1}}
        for kind, extra in [
            ('accessible_text', {'text': clock['value']}),
            ('element_geometry', {'element': 'home-league-countdown', 'rect': clock['rect'], 'tolerance_points': 0}),
            ('image_pixels', {'reference_image': image, 'pixels': [1200, 732]})]:
            contract['requirements'].append({'id': key + '-' + kind, 'state': key, 'kind': kind,
                'evidence': [str((EVIDENCE / 'source-clock.json').relative_to(ROOT)), image], **extra})
    assert contract['requirements'][:len(previous)] == previous
    contract.update(revision='english-v48', parent_revision='english-v47', changes=[
        'Actual hours/minutes/seconds countdown at recorded DOM mutation epochs; no prior requirement relaxed.'])
    return contract, reference, scenario


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out-dir', required=True)
    output = Path(parser.parse_args().out_dir)
    output.mkdir(parents=True, exist_ok=False)
    for filename, value in zip(['contract.json', 'reference.json', 'scenario.json'], build(), strict=True):
        (output / filename).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')
