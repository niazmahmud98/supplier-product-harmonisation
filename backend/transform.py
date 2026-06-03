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

# Importing our Phase 6 Harmonisation and Deduplication Engine Utilities
from normalization import (
    harmonize_category,
    normalize_material,
    find_duplicate_candidates
)

def run_harmonisation_pipeline():
    print("DYNAMIC MULTI-FILE PIPELINE EXECUTING: HARMONISATION ENGINE")

    base_dir = os.path.dirname(__file__)
    
    # Configuration matrix pointing directly to the folders instead of single files
    supplier_configs = [
        {
            "name": "XD Connects",
            "transformer": XDConnectsTransformer(),
            "folder_path": os.path.join(base_dir, "data", "raw", "xd_connects")
        },
        {
            "name": "European Sourcing",
            "transformer": EuropeanSourcingTransformer(),
            "folder_path": os.path.join(base_dir, "data", "raw", "european_sourcing")
        },
        {
            "name": "PF Concept",
            "transformer": PFConceptTransformer(),
            "folder_path": os.path.join(base_dir, "data", "raw", "pf_concept")
        }
    ]

    unified_catalog = []

    # 1. DYNAMIC LOOP: Scan folders and process ALL JSON files found inside
    for config in supplier_configs:
        name = config["name"]
        transformer = config["transformer"]
        folder_path = config["folder_path"]

        print(f"Scanning Folder for Supplier: {name}")
        
        # Guard Check: If the supplier folder doesn't exist, skip safely
        if not os.path.exists(folder_path):
            print(f"Skipping {name}: Folder not found at {folder_path}")
            continue

        # Get all JSON files inside this specific supplier folder dynamically
        json_files = [f for f in os.listdir(folder_path) if f.endswith(".json")]
        
        if not json_files:
            print(f"No JSON files found inside {folder_path}")
            continue

        print(f"Found {len(json_files)} JSON files to process for {name}: {json_files}")

        # Loop through each individual JSON file found inside this folder
        for file_name in json_files:
            raw_file_path = os.path.join(folder_path, file_name)
            print(f"Processing File: {file_name}...")

            try:
                # Load the raw payload from this specific file
                with open(raw_file_path, "r", encoding="utf-8") as f:
                    raw_payload = json.load(f)
                
                # Step A: Run OOP base transformation
                standardized_batch = transformer.transform(raw_payload)
                
                # Step B: Apply Harmonisation rules on-the-fly
                for item in standardized_batch:
                    item["category"] = harmonize_category(item.get("category", ""))
                    item["material"] = normalize_material(item.get("description", "") or item.get("name", ""))
                
                print(f"Harmonized {len(standardized_batch)} items from {file_name}.")
                
                # Merge this file's data into our master catalog
                unified_catalog.extend(standardized_batch)

            except Exception as e:
                print(f"Error during processing file {file_name}: {str(e)}")

    # 2. SECOND PASS: Execute Work Item 6.4 Product Deduplication (Bonus Task)
    print("Running Cross-Supplier Product Deduplication Matrix...")
    duplicate_report = find_duplicate_candidates(unified_catalog, threshold=0.75)
    print(f"Found {len(duplicate_report)} cross-supplier duplicate product clusters!")

    # 3. THIRD PASS: Save Output Datasets into data/harmonized/
    output_dir = os.path.join(base_dir, "data", "harmonized")
    os.makedirs(output_dir, exist_ok=True)
    
    master_file_path = os.path.join(output_dir, "unified_products.json")
    duplicate_file_path = os.path.join(output_dir, "duplicate_candidates.json")

    print(f" Saving final harmonized datasets...")
    
    # Save the Master Unified Catalog JSON
    with open(master_file_path, "w", encoding="utf-8") as out_f:
        json.dump(unified_catalog, out_f, indent=2, ensure_ascii=False)

    # Save the Duplicate Log Table JSON
    with open(duplicate_file_path, "w", encoding="utf-8") as dup_f:
        json.dump(duplicate_report, dup_f, indent=2, ensure_ascii=False)

    print(f"PIPELINE INTEGRATION COMPLETE SUCCESSFUL!")
    print(f"Total Master Harmonized Products Integrated: {len(unified_catalog)}")
    print(f"Master Catalog Saved at: {master_file_path}")
    print(f"Duplicate Clusters Table Saved at: {duplicate_file_path}")

if __name__ == "__main__":
    run_harmonisation_pipeline()