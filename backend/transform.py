import json
import os
import sys

# Ensuring the backend root directory is in the python path to load our custom modules safely
sys.path.append(os.path.dirname(__file__))

# Importing the object-oriented transformers we built previously
from transformers import (
    EuropeanSourcingTransformer,
    XDConnectsTransformer,
    PFConceptTransformer
)

# Importing our Phase 6 Harmonisation Engine Utilities
from normalization import (
    harmonize_category,
    normalize_material
)

def run_harmonisation_pipeline():
    print("DYNAMIC MULTI-FILE PIPELINE EXECUTING: HARMONISATION ENGINE")

    base_dir = os.path.dirname(__file__)

    # Configuration matrix — allowed_files=None means process all files in folder
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
            "allowed_files": ["products.json"]  # pricing/stock are index-based, cannot be linked reliably
        },
        {
            "name": "PF Concept",
            "transformer": PFConceptTransformer(),
            "folder_path": os.path.join(base_dir, "data", "raw", "pf_concept"),
            "allowed_files": None
        }
    ]

    unified_catalog = []

    # DYNAMIC LOOP: Scan folders and process JSON files
    for config in supplier_configs:
        name = config["name"]
        transformer = config["transformer"]
        folder_path = config["folder_path"]
        allowed_files = config.get("allowed_files")

        print(f"Scanning Folder for Supplier: {name}")

        # Guard: skip if folder missing
        if not os.path.exists(folder_path):
            print(f"Skipping {name}: Folder not found at {folder_path}")
            continue

        json_files = [f for f in os.listdir(folder_path) if f.endswith(".json")]

        if not json_files:
            print(f"No JSON files found inside {folder_path}")
            continue

        print(f"Found {len(json_files)} JSON files to process for {name}: {json_files}")

        for file_name in json_files:

            # Skip files not in the allowed list (if a filter is set)
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
                    item["category"] = harmonize_category(item.get("category", ""))
                    item["material"] = normalize_material(item.get("description", "") or item.get("name", ""))

                print(f"Harmonized {len(standardized_batch)} items from {file_name}.")

                unified_catalog.extend(standardized_batch)

            except Exception as e:
                print(f"Error processing {file_name}: {str(e)}")

    # Save final output
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