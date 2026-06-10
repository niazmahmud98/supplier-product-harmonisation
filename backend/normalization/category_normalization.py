import json
import os

# Force reload every time — no caching
_DEFAULT_FALLBACK = "Uncategorized"

def _load_category_mappings():
    base_dir = os.path.dirname(os.path.dirname(__file__))
    mapping_path = os.path.join(base_dir, "mappings", "categories.json")

    if not os.path.exists(mapping_path):
        return {}

    try:
        with open(mapping_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("canonical_taxonomy", {})
    except Exception:
        return {}


def harmonize_category(raw_category: str, product_name: str = "") -> str:
    taxonomy = _load_category_mappings()

    # Step 1: raw category exact match
    if raw_category:
        clean_cat = raw_category.lower().strip()
        for master_category, keywords in taxonomy.items():
            if clean_cat in [k.lower() for k in keywords]:
                return master_category
            for keyword in keywords:
                if keyword.lower() in clean_cat:
                    return master_category

    # Step 2: product name keyword match — simple lowercase, no normalize
    if product_name:
        clean_name = product_name.lower().strip()
        for master_category, keywords in taxonomy.items():
            for keyword in keywords:
                if keyword.lower() in clean_name:
                    return master_category

    return _DEFAULT_FALLBACK