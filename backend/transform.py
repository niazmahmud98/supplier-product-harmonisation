import json
import os
import sys

sys.path.append(os.path.dirname(__file__))

from transformers import (
    EuropeanSourcingTransformer,
    XDConnectsTransformer,
    PFConceptTransformer
)

from normalization import (
    harmonize_category,
    normalize_material,
    normalize_color
)


def build_pf_product_lookup(products_path: str) -> dict:
    lookup = {}

    if not os.path.exists(products_path):
        print("WARNING: PF Concept products.json not found — skipping lookup.")
        return lookup

    try:
        with open(products_path, "r", encoding="utf-8") as f:
            raw = json.load(f)

        models = raw.get("pfcProductfeed", {}).get("productfeed", {}).get("models", [])

        for model_wrapper in models:
            model = model_wrapper.get("model", {})
            if not isinstance(model, dict):
                continue

            # Name is at model level
            name = model.get("description", "")
            ext_desc = model.get("extDesc", "") 

            for items_wrapper in model.get("items", []):
                item = items_wrapper.get("item", {})
                if not isinstance(item, dict):
                    continue

                item_code = str(item.get("itemCode", "")).strip().lower()
                if not item_code or len(item_code) < 6:
                    continue

                # Use first 6 digits as model code to match price/stock feed
                model_code = item_code[:6]

                category = item.get("categoryData", {}).get("groupDesc", "Uncategorized")
                brand = item.get("brand", "Generic") or "Generic"
                material = item.get("material", "") or ""

                # Color from colors.color list
                color = "multicolor"
                color_list = item.get("colors", {}).get("color", [])
                if isinstance(color_list, list) and color_list:
                    color = color_list[0].get("baseColor", "multicolor") or "multicolor"
                elif isinstance(color_list, dict):
                    color = color_list.get("baseColor", "multicolor") or "multicolor"

                lookup[model_code] = {
                    "name": name,
                    "description": ext_desc,
                    "brand": brand,
                    "material": material,
                    "category": category,
                    "color": color
                }

    except Exception as e:
        print(f"ERROR building PF Concept lookup: {e}")

    print(f"PF Concept product lookup built: {len(lookup)} items")
    return lookup

def run_harmonisation_pipeline():
    print("DYNAMIC MULTI-FILE PIPELINE EXECUTING: HARMONISATION ENGINE")

    base_dir = os.path.dirname(__file__)

    # Build PF Concept product lookup from product feed
    pf_products_path = os.path.join(base_dir, "data", "raw", "pf_concept", "products.json")
    pf_lookup = build_pf_product_lookup(pf_products_path)

    supplier_configs = [
        {
            "name": "XD Connects",
            "transformer": XDConnectsTransformer(),
            "folder_path": os.path.join(base_dir, "data", "raw", "xd_connects"),
            "allowed_files": ["products.json"]
        },
        {
            "name": "European Sourcing",
            "transformer": EuropeanSourcingTransformer(),
            "folder_path": os.path.join(base_dir, "data", "raw", "european_sourcing"),
            "allowed_files": ["products.json"]
        },
        {
            "name": "PF Concept",
            "transformer": PFConceptTransformer(),
            "folder_path": os.path.join(base_dir, "data", "raw", "pf_concept"),
            "allowed_files": ["prices.json", "stock.json"]
        }
    ]

    unified_catalog = []

    for config in supplier_configs:
        name = config["name"]
        transformer = config["transformer"]
        folder_path = config["folder_path"]
        allowed_files = config.get("allowed_files")

        print(f"Scanning Folder for Supplier: {name}")

        if not os.path.exists(folder_path):
            print(f"Skipping {name}: Folder not found at {folder_path}")
            continue

        json_files = [f for f in os.listdir(folder_path) if f.endswith(".json")]

        if not json_files:
            print(f"No JSON files found inside {folder_path}")
            continue

        print(f"Found {len(json_files)} JSON files to process for {name}: {json_files}")

        for file_name in json_files:

            if allowed_files is not None and file_name not in allowed_files:
                print(f"Skipping {file_name} (not needed for {name})")
                continue

            raw_file_path = os.path.join(folder_path, file_name)
            print(f"Processing File: {file_name}...")

            try:
                with open(raw_file_path, "r", encoding="utf-8") as f:
                    raw_payload = json.load(f)

                # Step A: Run supplier-specific transformation
                standardized_batch = transformer.transform(raw_payload)

                # Step B: Apply harmonisation rules
                for item in standardized_batch:

                    # PF Concept — enrich with product lookup data
                    if name == "PF Concept":
                        sku_key = str(item.get("sku", "")).strip().lower()
                        if sku_key in pf_lookup:
                            product_info = pf_lookup[sku_key]
                            # Only override if name is generic placeholder
                            if item.get("name", "").startswith("Product "):
                                item["name"] = product_info["name"]
                            item["brand"] = product_info["brand"]
                            item["category"] = product_info["category"]
                            item["color"] = product_info["color"]
                            item["description"] = product_info["description"]
                            item["material"] = product_info["material"] 
                            if not item.get("material"):
                                item["material"] = product_info["material"]

                    if item.get("category") == "Uncategorized":
                        item["category"] = harmonize_category(item.get("category", ""), item.get("name", ""))
                    if name not in ["PF Concept", "XD Connects"]:
                           item["material"] = normalize_material(item.get("description", "") or item.get("name", ""))


                    # Normalize color for each variant
                    for variant in item.get("variants", []):
                        raw_color = variant.get("color", "")
                        if raw_color:
                            variant["color"] = normalize_color(raw_color)

                    # Normalize PF Concept item-level color
                    if name == "PF Concept" and item.get("color"):
                        item["color"] = normalize_color(item["color"])

                print(f"Harmonized {len(standardized_batch)} items from {file_name}.")
                unified_catalog.extend(standardized_batch)

            except Exception as e:
                print(f"Error processing {file_name}: {str(e)}")

    output_dir = os.path.join(base_dir, "data", "harmonized")
    os.makedirs(output_dir, exist_ok=True)

    master_file_path = os.path.join(output_dir, "unified_products.json")

    print(f"Saving final harmonized dataset...")

    with open(master_file_path, "w", encoding="utf-8") as out_f:
        json.dump(unified_catalog, out_f, indent=2, ensure_ascii=False)

    print(f"PIPELINE INTEGRATION COMPLETE SUCCESSFUL!")
    print(f"Total Master Harmonized Products Integrated: {len(unified_catalog)}")
    print(f"Master Catalog Saved at: {master_file_path}")

if __name__ == "__main__":
    run_harmonisation_pipeline()