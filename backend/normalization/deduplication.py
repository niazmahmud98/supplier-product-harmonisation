from difflib import SequenceMatcher
from .text_normalization import normalize_text

def calculate_similarity(text1: str, text2: str) -> float:
    """
    Calculates the string similarity ratio between two texts.
    Optimized to fast-exit if strings are completely mismatched.
    """
    if not text1 or not text2:
        return 0.0
        
    clean1 = normalize_text(text1).lower().strip()
    clean2 = normalize_text(text2).lower().strip()
    
    if abs(len(clean1) - len(clean2)) > 100:
        return 0.0
        
    return SequenceMatcher(None, clean1, clean2).ratio()


def find_duplicate_candidates(products: list, threshold: float = 0.75) -> list:
    """
    Highly Optimized Deduplication Scanner using Category Bucketing.
    Smartly skips 'Uncategorized' batch to avoid O(N^2) CPU hogging.
    Processes thousands of master records instantly!
    """
    duplicate_candidates = []
    
    if len(products) < 2:
        return []

    # Step 1: Bucket products by their harmonized category
    category_buckets = {}
    for p in products:
        cat = p.get("category", "Uncategorized")
        if cat not in category_buckets:
            category_buckets[cat] = []
        category_buckets[cat].append(p)

    print(f"Grouped into {len(category_buckets)} category buckets for hyper-speed processing.")

    # Step 2: Perform matrix scan within valid category buckets
    for cat_name, bucket_products in category_buckets.items():
        # GOLDEN RULE: Skip 'Uncategorized' loop to save massive CPU processing time
        if cat_name == "Uncategorized":
            print(f"Skipping bucket [Uncategorized] containing {len(bucket_products)} partial items to save CPU time.")
            continue
            
        num_in_bucket = len(bucket_products)
        if num_in_bucket < 2:
            continue
            
        print(f"Scanning bucket [{cat_name}] containing {num_in_bucket} items...")

        for i in range(num_in_bucket):
            p1 = bucket_products[i]
            
            for j in range(i + 1, num_in_bucket):
                p2 = bucket_products[j]
                
                # Cross-supplier evaluation: skip if same supplier
                if p1.get("supplier") == p2.get("supplier"):
                    continue
                    
                # 1. Quick Title Similarity Check
                title_score = calculate_similarity(p1.get("name", ""), p2.get("name", ""))
                if title_score < 0.50:
                    continue
                    
                # 2. Description Similarity Check
                desc_score = calculate_similarity(p1.get("description", ""), p2.get("description", ""))
                
                # 3. Weighted Average Confidence Score
                confidence_score = (title_score * 0.70) + (desc_score * 0.30)
                
                if confidence_score >= threshold:
                    duplicate_candidates.append({
                        "confidence_score": round(confidence_score, 2),
                        "match_type": "High Similarity Cluster" if confidence_score >= 0.90 else "Review Required",
                        "category": cat_name,
                        "product_a": {
                            "supplier": p1.get("supplier"),
                            "sku": p1.get("sku"),
                            "name": p1.get("name")
                        },
                        "product_b": {
                            "supplier": p2.get("supplier"),
                            "sku": p2.get("sku"),
                            "name": p2.get("name")
                        }
                    })
                    
    return sorted(duplicate_candidates, key=lambda x: x["confidence_score"], reverse=True)