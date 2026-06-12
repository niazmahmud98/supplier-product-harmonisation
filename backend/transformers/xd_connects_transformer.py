import sys
import os

# Ensuring the backend root is in the python path to load normalization packages safely
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from transformers.base_transformer import BaseTransformer
from normalization import normalize_text, standardize_price, normalize_material


class XDConnectsTransformer(BaseTransformer):
    """
    Transformer subclass for XD Connects.
    Handles German-to-English translation of colors/categories on-the-fly,
    and maps the flat JSON list to our unified canonical structure.
    """

    # Static dictionaries for quick, offline localization translation
    GERMAN_TO_ENGLISH_CATEGORIES = {
        "regenschirme": "umbrellas",
        "schreibgeräte": "writing instruments",
        "taschen & reise": "bags & travel",
        "telefon- & tablet-accessoires": "phone & tablet accessories",
        "werkzeuge & taschenlampen": "tools & flashlights",
        "caps & mützen": "caps & hats",
        "lanyards & schlüsselanhänger": "lanyards & keychains",
        "audio": "audio",
        "drinkware": "drinkware",
        "home & living": "home & living",
        "outdoor": "outdoor",
        "portfolios & notebooks": "portfolios & notebooks",
        "sport & fitness": "sport & fitness",
        "textile": "textiles",
        "car & safety": "car & safety",
    }

    GERMAN_TO_ENGLISH_COLORS = {
        "hellgrau": "light grey",
        "königsblau": "royal blue",
        "minze": "mint",
        "moosgrün": "moss green",
        "olivgrün": "olive green",
        "silbergrau": "silver grey",
        "stahl": "steel",
        "anthrazit": "anthracite",
        "beige": "beige",
        "blau": "blue",
        "braun": "brown",
        "burgunderrot": "burgundy red",
        "gelb": "yellow",
        "grün": "green",
        "orange": "orange",
        "rot": "red",
        "schwarz": "black",
        "weiß": "white",
        "weiss": "white",
    }

    def __init__(self):
        # Initialise base class with the unique supplier key
        super().__init__(supplier_key="xd_connects")

    def _translate_category(self, raw_cat: str) -> str:
        """Translates localized German categories to standard English"""
        norm_cat = normalize_text(raw_cat)
        return self.GERMAN_TO_ENGLISH_CATEGORIES.get(norm_cat, norm_cat)

    def _translate_color(self, raw_color: str) -> str:
        """Translates localized German colors to standard English"""
        norm_color = normalize_text(raw_color)
        return self.GERMAN_TO_ENGLISH_COLORS.get(norm_color, norm_color)

    def transform(self, raw_data: list) -> list:
        """
        Transforms raw XD Connects products into unified canonical format.
        """
        canonical_products = []
        if not raw_data or not isinstance(raw_data, list):
            return []

        # Reading keys directly from the JSON field mapping layer loaded by parent class
        name_key = self.field_mappings.get("name")
        desc_key = self.field_mappings.get("description")
        sku_key = self.field_mappings.get("sku")
        brand_key = self.field_mappings.get("brand")
        color_key = self.field_mappings.get("color")
        cat_key = self.field_mappings.get("category")

        for item in raw_data:
            if not isinstance(item, dict):
                continue

            # Extracting and cleaning core fields using our normalization utilities
            raw_name = item.get(name_key, "")
            raw_desc = item.get(desc_key, "")
            raw_sku = item.get(sku_key, "")
            raw_brand = item.get(brand_key, "Generic")

            # Handling translation layers
            raw_cat = item.get(cat_key, "Uncategorized")
            raw_color = item.get(color_key, "Multicolor")

            clean_name = normalize_text(raw_name)
            clean_desc = normalize_text(raw_desc)
            clean_sku = (
                str(raw_sku).strip().upper()
            )  # Standardising SKU to uppercase string
            clean_brand = normalize_text(raw_brand).title()

            translated_cat = self._translate_category(raw_cat).title()
            translated_color = self._translate_color(raw_color).lower()

            # Parsing nested pricing structure (ScalePrices table matrix)
            standardized_prices = []
            for scale in item.get("ScalePrices", []):
                raw_qty = scale.get("Quantity", 1)
                raw_price = scale.get("Price", 0.0)

                standardized_prices.append(
                    {
                        "minimum_quantity": int(raw_qty),
                        "price": standardize_price(raw_price),
                    }
                )

            # Assembling into the final enterprise Canonical schema structure
            canonical_item = {
                "supplier": "XD Connects",
                "sku": clean_sku,
                "name": clean_name,
                "description": clean_desc,
                "brand": clean_brand,
                "category": translated_cat,
                "color": translated_color,
                "currency": "EUR",  # XD Connects baseline default currency code
                "pricing_matrix": standardized_prices,
                "material": normalize_material(item.get("Material", "").split(",")[0]) or "Unknown",
            }

            canonical_products.append(canonical_item)

        return canonical_products