from .text_normalization import normalize_text

def normalize_material(raw_material: str) -> str:
    """
    Harmonises and normalises inconsistent supplier material names 
    into a clean, unified canonical taxonomy format.
 
    """
    if not raw_material:
        return "Unknown"

    # Clean and lowercase the input text for bulletproof token matching
    clean_mat = normalize_text(raw_material).lower()

    #  Stainless Steel Mapping Logic
    if "stainless" in clean_mat or "steel" in clean_mat or "stahl" in clean_mat:
        return "Stainless Steel"

    # Recycled PET (rPET) Mapping Logic
    if "rpet" in clean_mat or "recycled pet" in clean_mat or "recycled polyethylene" in clean_mat:
        return "Recycled PET"

    # Bamboo Mapping Logic
    if "bamboo" in clean_mat or "bambus" in clean_mat:
        return "Bamboo"

    # Cotton Blends Mapping Logic
    if "cotton" in clean_mat or "baumwolle" in clean_mat:
        # Check if it's a blend or mix of materials
        if any(token in clean_mat for token in ["blend", "mix", "%", "poly", "canvas"]):
            return "Cotton Blend"
        return "Cotton"

    # Fallback for other standard common promotional items materials
    if "plastic" in clean_mat or "kunststoff" in clean_mat:
        return "Plastic"
    if "glass" in clean_mat or "glas" in clean_mat:
        return "Glass"
    if "aluminum" in clean_mat or "aluminium" in clean_mat:
        return "Aluminum"
    if "wood" in clean_mat or "holz" in clean_mat:
        return "Wood"
    if "pet" in clean_mat and ("recycelt" in clean_mat or "recycled" in clean_mat):
        return "Recycled PET"

    # General fallback if no match is found, keeping it clean with title case
    return "Unknown"