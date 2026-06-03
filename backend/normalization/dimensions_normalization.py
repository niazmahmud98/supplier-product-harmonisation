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

def normalize_dimensions(raw_dimensions: str) -> dict:
    """
    Standardises various supplier dimension formats into a unified dictionary structure.
    Integrates with convert_to_cm to ensure unified metric output in cm.

    """
    default_structure = {"length": None, "width": None, "height": None, "unit": "cm"}
    
    if not raw_dimensions or not isinstance(raw_dimensions, str):
        return default_structure

    # Detect unit on-the-fly (Default to cm, or detect mm/inches/m)
    clean_text = raw_dimensions.lower().strip()
    detected_unit = "cm"
    if "mm" in clean_text:
        detected_unit = "mm"
    elif "inch" in clean_text or "in" in clean_text or '"' in clean_text:
        detected_unit = "inch"
    elif "m" in clean_text and "mm" not in clean_text:
        detected_unit = "m"

    # Extract numbers using Regular Expression (Regex)
    numbers = [float(n) for n in re.findall(r"[-+]?\d*\.\d+|\d+", clean_text)]

    if not numbers:
        return default_structure

    # Map numbers and convert them to standard 'cm' using convert_to_cm function
    try:
        if len(numbers) >= 3:
            return {
                "length": convert_to_cm(numbers[0], detected_unit),
                "width": convert_to_cm(numbers[1], detected_unit),
                "height": convert_to_cm(numbers[2], detected_unit),
                "unit": "cm"
            }
        elif len(numbers) == 2:
            return {
                "length": convert_to_cm(numbers[0], detected_unit),
                "width": convert_to_cm(numbers[1], detected_unit),
                "height": None,
                "unit": "cm"
            }
        elif len(numbers) == 1:
            return {
                "length": convert_to_cm(numbers[0], detected_unit),
                "width": None,
                "height": None,
                "unit": "cm"
            }
    except Exception:
        return default_structure

    return default_structure