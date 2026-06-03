import json
import os
from .text_normalization import normalize_text

# Memory cache to load the JSON file only once (Optimization)
_CATEGORY_MAP_CACHE = None
_DEFAULT_FALLBACK = "Uncategorized"

def _load_category_mappings():
    """
    Internal helper to load the categories.json file dynamically.
    Uses caching to prevent redundant disk I/O operations.
    """
    global _CATEGORY_MAP_CACHE, _DEFAULT_FALLBACK
    
    if _CATEGORY_MAP_CACHE is not None:
        return _CATEGORY_MAP_CACHE

    # Locate the mappings/categories.json file relative to this file
    base_dir = os.path.dirname(os.path.dirname(__file__))
    mapping_path = os.path.join(base_dir, "mappings", "categories.json")

    if not os.path.exists(mapping_path):
        # Safe fallback if file is missing in production environment
        return {}

    try:
        with open(mapping_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            _CATEGORY_MAP_CACHE = data.get("canonical_taxonomy", {})
            _DEFAULT_FALLBACK = data.get("default_fallback", "Uncategorized")
    except Exception:
        _CATEGORY_MAP_CACHE = {}
    
    return _CATEGORY_MAP_CACHE


def harmonize_category(raw_category: str) -> str:
    """
    Harmonises any raw or localized supplier category into our 
    unified canonical taxonomy based on mappings/categories.json.
    """
    if not raw_category:
        return _DEFAULT_FALLBACK

    # Clean and lowercase the incoming category for flawless matching
    clean_cat = normalize_text(raw_category).lower()

    # Load the taxonomy matrix
    taxonomy = _load_category_mappings()

    # Dynamic Lookup: Scan the arrays to find where this category belongs
    for master_category, supplier_variants in taxonomy.items():
        if clean_cat in supplier_variants:
            return master_category  # Match found! Return the beautiful Standard title

    # Handle unknown categories (Work Item 6.1 Task 3 Requirement)
    return _DEFAULT_FALLBACK