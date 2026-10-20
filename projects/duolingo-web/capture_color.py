"""Compatibility import for case scripts; shared image normalization has one owner."""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from capabilities.rebuild.images import profile_facts, srgb_image
