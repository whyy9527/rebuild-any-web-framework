"""Normalize owned window decorations/Retina sampling and measure raw differences.

No image alignment, masking or content cropping is inferred. Native content
geometry comes from the application's actual NSWindow. Metrics are diagnostics,
not a visual pass verdict; matching dimensions alone cannot establish fidelity.
"""
import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image, ImageChops, ImageStat


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--reference', required=True)
    parser.add_argument('--window', required=True)
    parser.add_argument('--metadata', required=True)
    parser.add_argument('--out', required=True)
    args = parser.parse_args()
    output = Path(args.out)
    output.mkdir(parents=True, exist_ok=False)
    metadata = json.loads(Path(args.metadata).read_text())
    window = Image.open(args.window).convert('RGB')
    width, height = metadata['window_points']
    x, y, content_width, content_height = metadata['content_rect_points']
    scale = window.width / width
    if abs(window.height / height - scale) > 0.001 or abs(scale - metadata['backing_scale']) > 0.001:
        raise ValueError('Capture does not match recorded window geometry/backing scale')
    crop = [round(v * scale) for v in [x, y, x + content_width, y + content_height]]
    candidate = window.crop(crop).resize((round(content_width), round(content_height)), Image.Resampling.LANCZOS)
    candidate.save(output / 'candidate-content.png')
    reference = Image.open(args.reference).convert('RGB')
    result = {'kind': 'visual_difference_measurement', 'status': 'diagnostic_only',
              'reference_pixels': list(reference.size), 'candidate_pixels': list(candidate.size),
              'normalization': {'window_crop_pixels': crop, 'sample_scale': scale, 'resampling': 'LANCZOS',
                                'basis': 'Actual NSWindow contentLayoutRect; no product pixels excluded'},
              'limitations': ['No product pass verdict', 'Caller must establish same course/progress/preferences and animation state']}
    for label, filename in [('reference', args.reference), ('window', args.window), ('metadata', args.metadata)]:
        result[label + '_sha256'] = hashlib.sha256(Path(filename).read_bytes()).hexdigest()
    if reference.size == candidate.size:
        difference = ImageChops.difference(reference, candidate)
        difference.save(output / 'difference.png')
        result['mean_absolute_rgb'] = ImageStat.Stat(difference).mean
        result['rms_rgb'] = ImageStat.Stat(difference).rms
    else:
        result['reason'] = 'Content dimensions differ; images were not resized to conceal the mismatch'
    (output / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result))


if __name__ == '__main__':
    main()
