"""Strict capture comparison; Pillow is needed only for image requirements."""
import hashlib
from io import BytesIO
import math
from pathlib import Path
from .contracts import local_file


def srgb_image(image):
    from PIL import ImageCms
    profile = image.info.get('icc_profile')
    if profile:
        source = ImageCms.ImageCmsProfile(BytesIO(profile))
        return ImageCms.profileToProfile(image, source, ImageCms.createProfile('sRGB'), outputMode='RGB')
    return image.convert('RGB')


def profile_facts(image):
    from PIL import ImageCms
    profile = image.info.get('icc_profile')
    return {'input_profile': ImageCms.getProfileDescription(ImageCms.ImageCmsProfile(BytesIO(profile))).strip() if profile else 'untagged browser CSS capture; assumed sRGB',
            'input_profile_sha256': hashlib.sha256(profile).hexdigest() if profile else None,
            'comparison_space': 'sRGB'}


def compatible_geometry(capture, pixels):
    rect, scale, window = (capture.get(k) for k in ('content_rect_points', 'backing_scale', 'window_points'))
    finite = lambda v: type(v) in (int, float) and math.isfinite(v)
    return (isinstance(rect, list) and len(rect) == 4 and all(finite(v) for v in rect)
            and rect[0] >= 0 and rect[1] >= 0 and rect[2:] == pixels
            and finite(scale) and scale > 0 and isinstance(window, list) and len(window) == 2
            and all(finite(v) and v > 0 for v in window)
            and rect[0] + rect[2] <= window[0] and rect[1] + rect[3] <= window[1])


def compare_capture(root, requirement, state):
    root = Path(root).resolve()
    try:
        from PIL import Image, ImageChops, ImageStat, ImageCms
    except ImportError:
        return {'status': 'unavailable', 'reason': 'Pillow is required for image_pixels comparison'}
    reference_path = local_file(root, requirement['reference_image'])
    pixels = requirement['pixels']
    if not isinstance(pixels, list) or len(pixels) != 2 or any(type(v) is not int or v <= 0 for v in pixels):
        raise ValueError('Invalid reference image dimensions')
    capture = state.get('capture')
    if not isinstance(capture, dict) or not isinstance(capture.get('path'), str):
        return {'status': 'unavailable', 'reason': 'Driver did not collect a capture file'}
    if capture.get('state_consistent') is False:
        return {'status': 'unavailable', 'reason': 'Candidate semantic state changed around capture'}
    candidate_path = local_file(root, capture['path'], must_exist=False)
    rect, scale, window = (capture.get(k) for k in ('content_rect_points', 'backing_scale', 'window_points'))
    if not compatible_geometry(capture, pixels):
        return {'status': 'unavailable', 'reason': 'Missing or incompatible measured capture geometry'}
    source_capture = requirement.get('reference_capture')
    if source_capture is not None and (not isinstance(source_capture, dict) or not compatible_geometry(source_capture, pixels)):
        raise ValueError('Invalid measured reference capture geometry')
    if isinstance(source_capture, dict) and source_capture.get('state_consistent') is False:
        raise ValueError('Reference semantic state changed around capture')
    try:
        with Image.open(reference_path) as im:
            if source_capture is None and im.size != tuple(pixels):
                raise ValueError('Reference image does not match frozen viewport')
            reference_profile = profile_facts(im)
            reference = srgb_image(im)
            if source_capture is not None:
                source_scale = source_capture['backing_scale']
                if im.size != tuple(round(v * source_scale) for v in source_capture['window_points']):
                    raise ValueError('Reference image does not match measured window and scale')
                x, y, w, h = source_capture['content_rect_points']
                reference = reference.crop(tuple(round(v * source_scale) for v in (x, y, x+w, y+h))).resize(tuple(pixels), Image.Resampling.LANCZOS)
        with Image.open(candidate_path) as im:
            if im.size != tuple(round(v * scale) for v in window):
                return {'status': 'unavailable', 'reason': 'Capture size does not match measured window and scale'}
            candidate_profile = profile_facts(im)
            x, y, w, h = rect
            candidate = srgb_image(im).crop(tuple(round(v * scale) for v in (x, y, x+w, y+h)))
            candidate = candidate.resize(tuple(pixels), Image.Resampling.LANCZOS)
    except (OSError, ImageCms.PyCMSError) as error:
        return {'status': 'unavailable', 'reason': 'Capture decoding/color conversion failed: ' + type(error).__name__}
    difference = ImageChops.difference(reference, candidate)
    return {'status': 'pass' if all(hi == 0 for lo, hi in difference.getextrema()) else 'fail',
            'reference_sha256': hashlib.sha256(reference_path.read_bytes()).hexdigest(),
            'capture_sha256': hashlib.sha256(candidate_path.read_bytes()).hexdigest(),
            'mean_absolute_rgb_difference': ImageStat.Stat(difference).mean,
            'profiles': {'reference': reference_profile, 'candidate': candidate_profile},
            'normalization': 'ICC to sRGB; measured content crop and backing-scale downsample on each declared capture; no masks, alignment search or tolerance',
            'reason': 'Actual same-state image pixels only; sound, animation timing and unvisited states remain separate'}
