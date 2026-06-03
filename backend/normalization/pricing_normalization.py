def normalize_currency_code(currency: str) -> str:
    """Standardizes loose currency representations to ISO 4217 codes"""
    if not currency:
        return "EUR"  # Project default baseline
    
    cur = currency.strip().upper()
    if cur in ["€", "EUR", "EURO"]:
        return "EUR"
    if cur in ["$", "USD", "DOLLAR"]:
        return "USD"
    if cur in ["£", "GBP", "POUND"]:
        return "GBP"
    
    return cur

def standardize_price(price_val) -> float:
    """Ensures prices are strictly floats, rounded to 2 decimal places"""
    if price_val is None:
        return 0.00
        
    try:
        # Handle string prices with commas ( "12,50" -> 12.50)
        if isinstance(price_val, str):
            price_val = price_val.replace(",", ".").strip()
        
        float_price = float(price_val)
        
        # Validation: No negative prices allowed
        if float_price < 0:
            return 0.00
            
        return round(float_price, 2)
    except (ValueError, TypeError):
        return 0.00