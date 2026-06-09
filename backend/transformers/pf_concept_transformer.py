import sys
import os

# Ensuring backend root is in python path safely
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from transformers.base_transformer import BaseTransformer
from normalization import normalize_text, standardize_price, normalize_currency_code


class PFConceptTransformer(BaseTransformer):
    """
    Transformer subclass for PF Concept.
    Handles two feed types:
      - PFCPriceFeed -> priceInfo -> models -> model[] -> items[] -> item[] -> scales[]
      - PFCStockFeed -> stockFeed -> models -> model[] -> items[] -> item[] -> stockDirect
    """

    def __init__(self):
        super().__init__(supplier_key="pf_concept")

    def _extract_models(self, raw_data: dict) -> tuple:
        """
        Detects feed type (price or stock) and extracts the models list.
        Returns (models_list, feed_type) where feed_type is 'price' or 'stock'.
        """
        if "PFCPriceFeed" in raw_data:
            feed = raw_data["PFCPriceFeed"]
            info = feed.get("priceInfo", [])
            feed_type = "price"
        elif "PFCStockFeed" in raw_data:
            feed = raw_data["PFCStockFeed"]
            info = feed.get("stockFeed", [])
            feed_type = "stock"
        else:
            return [], "unknown"

        if not info or not isinstance(info, list):
            return [], feed_type

        models_container = info[0].get("models", [])
        if not models_container or not isinstance(models_container, list):
            return [], feed_type

        # models is a wrapper list — actual model array is inside first element
        if "model" in models_container[0]:
            return models_container[0]["model"], feed_type

        return models_container, feed_type

    def transform(self, raw_data) -> list:
        canonical_products = []
        if not raw_data:
            return []

        # Handle list input (fallback)
        if isinstance(raw_data, list):
            models_list = raw_data
            feed_type = "price"
        elif isinstance(raw_data, dict):
            models_list, feed_type = self._extract_models(raw_data)
        else:
            return []

        # Field mapping keys from parent class
        sku_key = self.field_mappings.get("sku", "modelcode")

        for model in models_list:
            if not isinstance(model, dict):
                continue

            # Model-level fields — stock feed uses 'modelCode', price feed uses 'modelcode'
            raw_sku = model.get(sku_key) or model.get("modelCode") or model.get("modelcode", "")
            clean_sku = str(raw_sku).strip().upper() if raw_sku else ""
            clean_desc = normalize_text(model.get("description", "No description available."))

            # items[] is a wrapper list, actual products are inside 'item' key
            for items_container in model.get("items", []):
                if not isinstance(items_container, dict):
                    continue

                for item in items_container.get("item", []):
                    if not isinstance(item, dict):
                        continue

                    # Item-level SKU fallback
                    item_sku = clean_sku or str(item.get("itemCode") or item.get("itemcode", "")).strip().upper()

                    if feed_type == "price":
                        # Extract currency and scales from item
                        raw_currency = item.get("currency", "EUR")
                        currency_iso = normalize_currency_code(raw_currency)

                        standardized_prices = []
                        for scale in item.get("scales", []):
                            if not isinstance(scale, dict):
                                continue
                            standardized_prices.append({
                                "minimum_quantity": int(scale.get("quantityFrom", 1)),
                                "price": standardize_price(scale.get("nettPrice", 0.0))
                            })

                        if not standardized_prices:
                            continue

                        standardized_prices = sorted(standardized_prices, key=lambda x: x["minimum_quantity"])

                        canonical_products.append({
                            "supplier": "PF Concept",
                            "sku": item_sku,
                            "name": f"Product {item_sku}",
                            "description": clean_desc,
                            "brand": normalize_text(model.get("brand", "Generic")).title(),
                            # "category": normalize_text(model.get("category", "Uncategorized")).title(),
                            "category": str(item.get("groupDesc", "Uncategorized")),
                            "color": normalize_text(item.get("color", "multicolor")).lower(),
                            "currency": currency_iso,
                            "pricing_matrix": standardized_prices
                        })

                    elif feed_type == "stock":
                        # Stock feed has no pricing — build stock-only record
                        stock_direct = item.get("stockDirect", 0)
                        stock_next_po = item.get("stockNextPo", 0)

                        canonical_products.append({
                            "supplier": "PF Concept",
                            "sku": item_sku,
                            "name": f"Product {item_sku}",
                            "description": clean_desc,
                            "brand": "Generic",
                            # "category": "Uncategorized",
                            "category": str(item.get("groupDesc", "Uncategorized")),
                            "color": "multicolor",
                            "currency": "EUR",
                            "pricing_matrix": [],
                            "stock_direct": stock_direct,
                            "stock_next_po": stock_next_po,
                            "stock_location": item.get("stockLocation", "")
                        })

        return canonical_products