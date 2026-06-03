# Data Exploration & Profiling
# Analyses raw supplier data for quality issues
# Covers: missing values, duplicates, category/color inconsistencies, invalid prices

import json
import os


# HELPER: Load JSON file
def load_json(path):
    """Load a JSON file and return data"""
    if not os.path.exists(path):
        print(f"File not found: {path}")
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

# Missing Values Check
def check_missing(products, supplier_name):
    """Check missing values and report using canonical field names"""
    print(f"\n--- Missing Values: {supplier_name} ---")
    total = len(products)
    if total == 0:
        print("  No products found to analyze.")
        return

    # Count missing for each canonical field manually based on nested structure
    missing_counts = {"name": 0, "description": 0, "category": 0, "material": 0, "brand": 0, "color": 0}

    for p in products:
        if supplier_name == "XD Connects":
            if not p.get("ItemName"): missing_counts["name"] += 1
            if not p.get("LongDescription"): missing_counts["description"] += 1
            if not p.get("MainCategory"): missing_counts["category"] += 1
            if not p.get("Material"): missing_counts["material"] += 1
            if not p.get("Brand"): missing_counts["brand"] += 1
            if not p.get("Color"): missing_counts["color"] += 1
        
        elif supplier_name == "European Sourcing":
            # FIXED: Name & Description exist inside the nested variants list, not at product root
            variants = p.get("variants", [])
            first_variant = variants[0] if variants else {}

            name_val = first_variant.get("name")
            desc_val = first_variant.get("description")
            
            # If they are dictionaries with multi-language data, extract the content
            if isinstance(name_val, dict): name_val = name_val.get("en") or list(name_val.values())[0]
            if isinstance(desc_val, dict): desc_val = desc_val.get("en") or list(desc_val.values())[0]

            if not name_val: missing_counts["name"] += 1
            if not desc_val: missing_counts["description"] += 1
            if not p.get("brand"): missing_counts["brand"] += 1
            
            # Category list check
            if not p.get("categories") or len(p.get("categories", [])) == 0:
                missing_counts["category"] += 1
                
            # Nested color and material inside variants attributes
            has_color = False
            has_material = False
            for v in variants:
                for attr in v.get("attributes", []):
                    attr_group = attr.get("attribute_group", {}).get("slug", "")
                    if attr_group == "colors": has_color = True
                    if attr_group == "materials": has_material = True
            
            if not has_color: missing_counts["color"] += 1
            if not has_material: missing_counts["material"] += 1

    # Report results
    for canonical, missing in missing_counts.items():
        percent = round((missing / total) * 100, 1) if total > 0 else 0
        print(f"  {canonical}: {missing} missing ({percent}%)")


# Duplicate SKU Check
def check_duplicates(products, supplier_name):
    """Check for duplicate SKUs or Internal References"""
    print(f"\n-- Duplicate SKUs: {supplier_name} --")
    skus = []
    
    for p in products:
        if supplier_name == "XD Connects":
            if p.get("ItemNo"): skus.append(p["ItemNo"])
        elif supplier_name == "European Sourcing":
            if p.get("id"): skus.append(p["id"])
            
        # Check variant level identifiers
        for v in p.get("variants", []):
            if v.get("supplier_reference"):
                skus.append(v["supplier_reference"])
            elif v.get("id"):
                skus.append(v["id"])

    total_skus = len(skus)
    duplicate_count = total_skus - len(set(skus))
    print(f"  Total SKU/Ref Records: {total_skus}")
    print(f"  Duplicate Count: {duplicate_count}")


# Category Analysis
def check_categories(products, supplier_name):
    """Show all unique categories"""
    print(f"\n-- Categories: {supplier_name} --")
    categories = set()
    
    for p in products:
        if supplier_name == "European Sourcing":
            for cat in p.get("categories", []):
                categories.add(cat.get("name", "unknown"))
        elif supplier_name == "XD Connects":
            if p.get("MainCategory"):
                categories.add(p["MainCategory"])

    print(f"  Total unique categories: {len(categories)}")
    # Print first 15 to keep output clean but structured
    for cat in sorted(list(categories))[:15]:
        print(f"    - {cat}")
    if len(categories) > 15:
        print(f"    ... and {len(categories) - 15} more categories.")


# Color Analysis
def check_colors(products, supplier_name):
    """Show all unique colors"""
    print(f"\n-- Colors: {supplier_name} --")
    colors = set()
    
    for p in products:
        if supplier_name == "European Sourcing":
            for v in p.get("variants", []):
                for attr in v.get("attributes", []):
                    if attr.get("attribute_group", {}).get("slug") == "colors":
                        colors.add(attr.get("value", "unknown"))
        elif supplier_name == "XD Connects":
            if p.get("Color"):
                colors.add(p["Color"])

    print(f"  Total unique colors: {len(colors)}")
    for color in sorted(list(colors))[:15]:
        print(f"    - {color}")


# Invalid Price Check
def check_prices(products, supplier_name):
    """Check for invalid prices"""
    print(f"\n-- Invalid Prices: {supplier_name} --")
    zero_prices = 0
    negative_prices = 0

    for p in products:
        if supplier_name == "European Sourcing":
            for v in p.get("variants", []):
                for price in v.get("variant_prices", []):
                    value = price.get("value", 0)
                    if value == 0: zero_prices += 1
                    if value < 0: negative_prices += 1
        elif supplier_name == "XD Connects":
            # Check if ScalePrices exist in XD Connects schema
            for scale in p.get("ScalePrices", []):
                value = scale.get("Price", 0)
                if value == 0: zero_prices += 1
                if value < 0: negative_prices += 1

    print(f"  Zero prices:     {zero_prices}")
    print(f"  Negative prices: {negative_prices}")


# Run all checks
def run_eda():
    print("Data Exploration & Profiling Pipeline")
  

    # European Sourcing Analysis
    es_products = load_json("data/raw/european_sourcing/products.json")
    if es_products:
        check_missing(es_products, "European Sourcing")
        check_duplicates(es_products, "European Sourcing")
        check_categories(es_products, "European Sourcing")
        check_colors(es_products, "European Sourcing")
        check_prices(es_products, "European Sourcing")

    print("\n" + "="*50)

    # XD Connects Analysis
    xd_data = load_json("data/raw/xd_connects/products.json")
    if xd_data:
        # If it's already a list, use it directly, otherwise try to get "products" key
        if isinstance(xd_data, list):
            xd_products = xd_data
        else:
            xd_products = xd_data.get("products", [])
            
        check_missing(xd_products, "XD Connects")
        check_duplicates(xd_products, "XD Connects")
        check_categories(xd_products, "XD Connects")
        check_colors(xd_products, "XD Connects")
        check_prices(xd_products, "XD Connects")

    print("\n" + "="*50)

    #PF Concept Analysis
    pf_data = load_json("data/raw/pf_concept/prices.json")
    if pf_data:
        print("\n--- PF Concept Price Data ---")
        # Extract deep level list mapping
        pf_models = pf_data.get("PFCPriceFeed", {}).get("priceInfo", [{}])[0].get("models", [])
        
        # Unpacking actual models array data inside inner dict
        actual_models = []
        if pf_models and "model" in pf_models[0]:
            actual_models = pf_models[0]["model"]
        elif isinstance(pf_models, list):
            actual_models = pf_models

        print(f"  Total dynamic models/products found: {len(actual_models)}")

        # Check currencies and values from scales matrix
        zero_prices = 0
        currencies = set()
        
        for m in actual_models:
            for item in m.get("items", []):
                for op in item.get("objectPrices", []):
                    for scale in op.get("scales", []):
                        currencies.add(scale.get("currency", "EUR"))
                        price_val = scale.get("nettPrice", 0)
                        if price_val == 0:
                            zero_prices += 1

        print(f"  Currencies found: {currencies if currencies else 'EUR'}")
        print(f"  Zero prices detected in matrix: {zero_prices}")

    print("EDA Complete!")


if __name__ == "__main__":
    run_eda()