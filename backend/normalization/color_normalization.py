import json
import os
from .text_normalization import normalize_text

# Load color mapping from mappings/colors.json
_base_dir = os.path.dirname(os.path.dirname(__file__))
_colors_path = os.path.join(_base_dir, "mappings", "colors.json")

with open(_colors_path, "r", encoding="utf-8") as f:
    _color_data = json.load(f)

COLOR_MAPPING = _color_data["canonical_colors"]
DEFAULT_FALLBACK = _color_data["default_fallback"]

def normalize_color(raw_color: str) -> str:
    """
    Harmonises inconsistent supplier color names (English + German)
    into a clean, unified canonical color name.
    """
    if not raw_color:
        return DEFAULT_FALLBACK

    clean_color = normalize_text(raw_color).lower().strip()

    for canonical, variants in COLOR_MAPPING.items():
        if clean_color in variants:
            return canonical

    return DEFAULT_FALLBACK