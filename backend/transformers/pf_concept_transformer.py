import sys
import os

# Ensuring backend root is in python path safely
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from transformers.base_transformer import BaseTransformer
from normalization import normalize_text, standardize_price, normalize_currency_code


class PFConceptTransformer(BaseTransformer):
    """
    Transformer subclass for PF Concept.
    Handles extraction of prices from highly complex multi-tier price matrices
    (PFCPriceFeed -> priceInfo -> models -> items -> objectPrices -> scales).
    """

    def __init__(self):
        # Initialise base class with the unique supplier key
        super().__init__(supplier_key="pf_concept")

    def transform(self, raw_data: list) -> list:
        """
        Transforms raw PF Concept deep-nested price matrices into standardized formats.
        Accepts the parsed dictionary/list payload and flattens it out.
        """
        canonical_products = []
        if not raw_data:
            return []

        # PF Concept pricing feed structure is typically wrapped inside an object
        # Let's extract the actual models array dynamically based on structural hierarchy
        models_list = []
        if isinstance(raw_data, dict):
            price_feed = raw_data.get("PFCPriceFeed", {})
            price_info = price_feed.get("priceInfo", [{}])
            if price_info and isinstance(price_info, list):
                models_container = price_info[0].get("models", [])
                if models_container and "model" in models_container[0]:
                    models_list = models_container[0]["model"]
                else:
                    models_list = models_container
        elif isinstance(raw_data, list):
            models_list = raw_data

        # Reading keys from our field mapping layer loaded by parent class
        name_key = self.field_mappings.get("name", "modelName")
        sku_key = self.field_mappings.get("sku", "id")

        for model in models_list:
            if not isinstance(model, dict):
                continue

            # Extract basic identifiers at the model level
            raw_name = model.get(name_key, "")
            raw_sku = model.get(sku_key, "")

            # If model name or SKU is blank, fallback to item level identifiers
            clean_name = normalize_text(raw_name) if raw_name else ""
            clean_sku = str(raw_sku).strip().upper() if raw_sku else ""

            # Standard currency accumulator
            currency_iso = "EUR"

            # Traverse down the multi-tier product data structure
            items = model.get("items", [{}])
            for item in items:
                if not isinstance(item, dict):
                    continue

                # If model root level SKU was missing, use item number as SKU
                if not clean_sku and item.get("itemNo"):
                    clean_sku = str(item.get("itemNo")).strip().upper()

                object_prices = item.get("objectPrices", [])
                for obj_price in object_prices:
                    if not isinstance(obj_price, dict):
                        continue

                    standardized_prices = []
                    scales = obj_price.get("scales", [])
                    
                    for scale in scales:
                        if not isinstance(scale, dict):
                            continue

                        # Extract currency code from scale node
                        raw_currency = scale.get("currency", "EUR")
                        currency_iso = normalize_currency_code(raw_currency)

                        # Parse pricing bounds
                        raw_qty = scale.get("quantityFrom", 1)
                        raw_price = scale.get("nettPrice", 0.0)

                        standardized_prices.append({
                            "minimum_quantity": int(raw_qty),
                            "price": standardize_price(raw_price)
                        })

                    # If we found valid prices, assemble the canonical record
                    if standardized_prices:
                        # Sort pricing matrix by minimum_quantity
                        standardized_prices = sorted(standardized_prices, key=lambda x: x["minimum_quantity"])

                        # Assemble into unified standard canonical structure
                        canonical_item = {
                            "supplier": "PF Concept",
                            "sku": clean_sku,
                            "name": clean_name if clean_name else f"Product {clean_sku}",
                            "description": normalize_text(model.get("description", "No description available.")),
                            "brand": normalize_text(model.get("brand", "Generic")).title(),
                            "category": normalize_text(model.get("category", "Uncategorized")).title(),
                            "color": normalize_text(item.get("color", "multicolor")).lower(),
                            "currency": currency_iso,
                            "pricing_matrix": standardized_prices
                        }

                        canonical_products.append(canonical_item)

        return canonical_products