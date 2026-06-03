import re

def convert_to_cm(value: float, from_unit: str) -> float:
    """Converts length/dimension units to standard cm"""
    if not value:
        return 0.0
    
    unit = from_unit.strip().lower()
    if unit in ["mm", "millimeter"]:
        return round(value / 10.0, 2)
    elif unit in ["inch", "inches", "in", '"']:
        return round(value * 2.54, 2)
    elif unit in ["m", "meter"]:
        return round(value * 100.0, 2)
    
    return round(value, 2)  # Default assume cm

def normalize_volume(volume_str: str) -> str:
    """Standardizes volume representations ('0.5L' or '500 ml' to '500ml')"""
    if not volume_str:
        return ""
    
    clean_str = volume_str.strip().lower().replace(" ", "")
    # Check for Liters to ML conversion (0.5l -> 500ml)
    match_l = re.match(r"([0-9.]+)(l|liter|liters)", clean_str)
    if match_l:
        val = float(match_l.group(1))
        if val < 5.0:  # Likely in Liters, convert to ml
            return f"{int(val * 1000)}ml"
        return f"{int(val)}ml"
        
    return clean_str