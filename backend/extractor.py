import os
import time
import json
import requests
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Supplier API Credentials & Endpoints
EU_TOKEN = os.getenv("EUROPEAN_SOURCING_TOKEN")
EU_URL = os.getenv("EUROPEAN_SOURCING_URL")

XD_PRODUCTS = os.getenv("XD_CONNECTS_PRODUCTS_URL")
XD_PRICES = os.getenv("XD_CONNECTS_PRICES_URL")
XD_STOCK = os.getenv("XD_CONNECTS_STOCK_URL")

PF_PRODUCTS = os.getenv("PF_CONCEPT_PRODUCTS_URL")
PF_PRICE = os.getenv("PF_CONCEPT_PRICE_URL")
PF_STOCK = os.getenv("PF_CONCEPT_STOCK_URL")


class BaseExtractor:

    def fetch(self, url, method="GET", headers=None, body=None):
        """Fetches data from a specific API endpoint with built-in retry logic."""
        for i in range(3):
            try:
                if method == "GET":
                    response = requests.get(url, headers=headers)
                else:
                    response = requests.post(url, headers=headers, json=body)

                if response.status_code == 200:
                    return response.json()

                print(f"Error {response.status_code}, retry {i+1}/3...")
                time.sleep(2)

            except Exception as e:
                print(f"Network error: {e}, retry {i+1}/3...")
                time.sleep(2)
        return None

    def save(self, data, path):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def log(self, msg):
        print(f"[EXTRACTOR] {msg}")

    def fetch_all(self):
        raise NotImplementedError("Each supplier extractor must implement fetch_all method.")


class EuropeanSourcingExtractor(BaseExtractor):

    def fetch_all(self):
        # Guard: check credentials before proceeding
        if not EU_TOKEN or not EU_URL:
            self.log("ERROR: European Sourcing credentials not set in .env")
            return

        headers = {
            "x-auth-token": EU_TOKEN,
            "Content-Type": "application/json"
        }

        products_list = []
        variants_list = []
        stock_list = []
        pricing_list = []

        page = 0
        max_pages = 10

        self.log("Starting European Sourcing extraction...")

        while page < max_pages:
            body = {
                "lang": "en",
                "size": 50,
                "from": page * 50
            }

            data = self.fetch(
                f"{EU_URL}/search",
                method="POST",
                headers=headers,
                body=body
            )

            if not data:
                break

            products = data.get("products", [])
            if not products:
                break

            for p in products:
                products_list.append(p)

                for v in p.get("variants", []):
                    variants_list.append(v)

                    if "stock" in v:
                        stock_list.append(v["stock"])

                    if "variant_prices" in v:
                        pricing_list.append(v["variant_prices"])

            page += 1
            self.log(f"Page {page} processed -> Total products collected: {len(products_list)}")

        self.save(products_list, "data/raw/european_sourcing/products.json")
        self.save(variants_list, "data/raw/european_sourcing/variants.json")
        self.save(stock_list, "data/raw/european_sourcing/stock.json")
        self.save(pricing_list, "data/raw/european_sourcing/pricing.json")

        self.log("European Sourcing extraction completed and cached successfully.")


class XDConnectsExtractor(BaseExtractor):

    def fetch_all(self):
        # Guard: check credentials before proceeding
        if not XD_PRODUCTS or not XD_PRICES or not XD_STOCK:
            self.log("ERROR: XD Connects URLs not set in .env")
            return

        self.log("Starting XD Connects extraction...")

        products = self.fetch(XD_PRODUCTS)
        prices = self.fetch(XD_PRICES)
        stock = self.fetch(XD_STOCK)

        if products:
            self.save(products, "data/raw/xd_connects/products.json")
        if prices:
            self.save(prices, "data/raw/xd_connects/prices.json")
        if stock:
            self.save(stock, "data/raw/xd_connects/stock.json")

        self.log("XD Connects extraction completed and cached successfully.")


class PFConceptExtractor(BaseExtractor):

    def fetch_all(self):
        # Guard: check credentials before proceeding
        if not PF_PRICE or not PF_STOCK:
            self.log("ERROR: PF Concept URLs not set in .env")
            return

        self.log("Starting PF Concept extraction...")

        # Fetch product feed — provides name, category, color, material, brand
        if PF_PRODUCTS:
            products = self.fetch(PF_PRODUCTS)
            if products:
                self.save(products, "data/raw/pf_concept/products.json")
                self.log("PF Concept product feed saved.")
        else:
            self.log("WARNING: PF_CONCEPT_PRODUCTS_URL not set — skipping product feed.")

        prices = self.fetch(PF_PRICE)
        stock = self.fetch(PF_STOCK)

        if prices:
            self.save(prices, "data/raw/pf_concept/prices.json")
        if stock:
            self.save(stock, "data/raw/pf_concept/stock.json")

        self.log("PF Concept extraction completed and cached successfully.")


if __name__ == "__main__":
    eu_extractor = EuropeanSourcingExtractor()
    xd_extractor = XDConnectsExtractor()
    pf_extractor = PFConceptExtractor()

    eu_extractor.fetch_all()
    xd_extractor.fetch_all()
    pf_extractor.fetch_all()

    print("\n[SUCCESS] All supplier data successfully extracted and cached locally!")