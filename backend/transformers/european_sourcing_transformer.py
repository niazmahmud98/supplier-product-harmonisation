import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from transformers.base_transformer import BaseTransformer
from normalization import normalize_text, standardize_price
from normalization.category_normalization import harmonize_category


class EuropeanSourcingTransformer(BaseTransformer):
    """
    Transformer subclass for European Sourcing.
    Flattens the deeply nested variants array layout into distinct canonical records,
    and extracts colors and tiered scale pricing matrices from variant attributes.
    """

    def __init__(self):
        super().__init__(supplier_key="european_sourcing")

    def _extract_color(self, variant: dict) -> str:
        """Parses the deeply nested attributes list to pull out the color value."""
        for attr in variant.get("attributes", []):
            if attr.get("attribute_group", {}).get("slug") == "colors":
                return normalize_text(attr.get("value", "multicolor"))
        return "multicolor"

    def transform(self, raw_data: list) -> list:
        """
        Transforms raw European Sourcing multi-layered products into standard canonical format.
        Flattens 1 Product -> N Variants into N Canonical Items.
        """
        canonical_products = []
        if not raw_data or not isinstance(raw_data, list):
            return []

        brand_key = self.field_mappings.get("brand")
        cat_key = self.field_mappings.get("category")

        for product in raw_data:
            if not isinstance(product, dict):
                continue

            # Extract brand name from nested brand object
            raw_brand = product.get(brand_key) or {}
            clean_brand = normalize_text(raw_brand.get("name", "Generic")).title()

            # Extract raw category name — will be harmonized inside the variant loop
            raw_categories = product.get(cat_key, [])
            raw_cat_name = ""
            if raw_categories and isinstance(raw_categories, list):
                raw_cat_name = raw_categories[0].get("name", "")

            # Loop through each variant to flatten the nested structure
            variants = product.get("variants", [])
            for variant in variants:
                if not isinstance(variant, dict):
                    continue

                # Extract name, description and SKU from variant level
                raw_name = variant.get("name", "")
                raw_desc = variant.get("description", "")
                raw_sku = variant.get("supplier_reference") or variant.get("id", "")

                # Handle multi-language dictionary — prefer English or first available value
                if isinstance(raw_name, dict):
                    raw_name = raw_name.get("en") or list(raw_name.values())[0]
                if isinstance(raw_desc, dict):
                    raw_desc = raw_desc.get("en") or list(raw_desc.values())[0]

                clean_name = normalize_text(raw_name)
                clean_desc = normalize_text(raw_desc)
                clean_sku = str(raw_sku).strip().upper()

                # Harmonize using raw_name directly to avoid normalize_text interference
                clean_category = harmonize_category(raw_cat_name, raw_name.lower().strip())

                # Extract color from nested attributes list
                clean_color = self._extract_color(variant)

                # Parse and sort tiered pricing matrix by minimum quantity
                standardized_prices = []
                for price_node in variant.get("variant_prices", []):
                    raw_qty = price_node.get("minimum_quantity", 1)
                    raw_price = price_node.get("value", 0.0)
                    standardized_prices.append({
                        "minimum_quantity": int(raw_qty),
                        "price": standardize_price(raw_price)
                    })

                standardized_prices = sorted(standardized_prices, key=lambda x: x["minimum_quantity"])

                # Assemble into unified canonical structure
                canonical_item = {
                    "supplier": "European Sourcing",
                    "sku": clean_sku,
                    "name": clean_name,
                    "description": clean_desc,
                    "brand": clean_brand,
                    "category": clean_category,
                    "color": clean_color,
                    "currency": "EUR",
                    "pricing_matrix": standardized_prices
                }

                canonical_products.append(canonical_item)

        return canonical_products