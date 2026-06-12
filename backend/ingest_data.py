import os
import json
import uuid
from models import SessionLocal, Product, Variant, SupplierOffer, PricingTier, Base, engine

def load_json_file(file_path):
    if not os.path.exists(file_path):
        return []
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, dict):
                # Handle PF Concept nested structures
                if "PFCPriceFeed" in data:
                    return data["PFCPriceFeed"]
                if "PFCStockFeed" in data:
                    return data["PFCStockFeed"]
                return [data]
            return data if isinstance(data, list) else []
    except Exception as e:
        return []

def run_ingestion():
    print("🚀 CRITICAL SYSTEM OVERHAUL: FORCE INGESTING ALL 3 SUPPLIERS...")

    # Drop and re-create tables for fresh ingestion
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    base_dir = os.path.dirname(os.path.abspath(__file__))

    master_products_path = os.path.join(base_dir, "data", "harmonized", "unified_products.json")
    master_products = load_json_file(master_products_path)

    if not master_products:
        print("❌ Error: unified_products.json not found!")
        db.close()
        return

    print(f"📋 Total stream records loaded from JSON: {len(master_products)}")

    # Pre-cache XD Connects — key: ItemCode
    xd_stock = {str(item.get("ItemCode")).strip().lower(): item for item in load_json_file(os.path.join(base_dir, "data", "raw", "xd_connects", "stock.json")) if isinstance(item, dict) and item.get("ItemCode")}
    xd_prices = {str(item.get("ItemCode")).strip().lower(): item for item in load_json_file(os.path.join(base_dir, "data", "raw", "xd_connects", "prices.json")) if isinstance(item, dict) and item.get("ItemCode")}

    # Pre-cache European Sourcing — key: sku (stock has no SKU, skip)
    eu_stock = {}
    eu_prices = {str(item.get("sku")).strip().lower(): item for item in load_json_file(os.path.join(base_dir, "data", "raw", "european_sourcing", "pricing.json")) if isinstance(item, dict) and item.get("sku")}

    # Pre-cache PF Concept — key: itemcode
    pf_stock = {str(item.get("itemCode")).strip().lower(): item for item in load_json_file(os.path.join(base_dir, "data", "raw", "pf_concept", "stock.json")) if isinstance(item, dict) and item.get("itemCode")}
    pf_prices = {str(item.get("itemcode")).strip().lower(): item for item in load_json_file(os.path.join(base_dir, "data", "raw", "pf_concept", "prices.json")) if isinstance(item, dict) and item.get("itemcode")}

    products_added = 0
    variants_added = 0
    offers_added = 0

    for idx, mp in enumerate(master_products):
        raw_supplier = mp.get("supplier", "").strip()
        if "xd" in raw_supplier.lower() or "xindao" in raw_supplier.lower():
            supplier_name = "XD Connects"
        elif "pf" in raw_supplier.lower() or "concept" in raw_supplier.lower():
            supplier_name = "PF Concept"
        else:
            supplier_name = "European Sourcing"

        sku = str(mp.get("sku", "")).strip()
        sku_key = sku.lower()
        if not sku:
            continue

        try:
            # Layer 1: Product Master Injection
            product_name = mp.get("name", "Unnamed Product").strip()
            product = db.query(Product).filter(Product.name == product_name).first()

            if not product:
                product = Product(
                    id=str(uuid.uuid4()),
                    name=product_name,
                    description=mp.get("description", ""),
                    category=mp.get("category", "Uncategorized"),
                    material=mp.get("material", "Unknown"),
                    brand=mp.get("brand", None)
                )
                db.add(product)
                db.flush()
                products_added += 1

            # Layer 2: Variant Specification
            color_val = mp.get("color", "multicolor")
            size_val = mp.get("size", "Standard")
            dimensions_data = str(mp.get("dimensions")) if mp.get("dimensions") else None

            variant = db.query(Variant).filter(
                Variant.product_id == product.id,
                Variant.color == color_val,
                Variant.size == size_val
            ).first()

            if not variant:
                variant = Variant(
                    id=str(uuid.uuid4()),
                    product_id=product.id,
                    color=color_val,
                    size=size_val,
                    dimensions=dimensions_data
                )
                db.add(variant)
                db.flush()
                variants_added += 1

            # Layer 3: Safe Inventory Fallback Evaluation
            qty = 0
            if supplier_name == "XD Connects" and sku_key in xd_stock:
                qty = xd_stock[sku_key].get("CurrentStock", 0)
            elif supplier_name == "PF Concept" and sku_key in pf_stock:
                qty = pf_stock[sku_key].get("stockDirect", 0)
            # European Sourcing: no SKU-based stock available

            # Layer 4: Force Supplier Offer Context mapping
            offer = db.query(SupplierOffer).filter(
                SupplierOffer.supplier == supplier_name,
                SupplierOffer.supplier_sku == sku
            ).first()

            if not offer:
                offer = SupplierOffer(
                    id=str(uuid.uuid4()),
                    variant_id=variant.id,
                    supplier=supplier_name,
                    supplier_sku=sku,
                    currency=mp.get("currency", "EUR") or "EUR",
                    stock=int(qty or 0)
                )
                db.add(offer)
                db.flush()
                offers_added += 1

            # Layer 5: Safe Pricing Fallback Evaluation
            price_val = mp.get("price") or 0.0
            if not price_val:
                if supplier_name == "XD Connects" and sku_key in xd_prices:
                    price_val = xd_prices[sku_key].get("ItemPriceNet_Qty1") or 0.0
                elif supplier_name == "European Sourcing" and sku_key in eu_prices:
                    price_val = eu_prices[sku_key].get("value") or eu_prices[sku_key].get("price", 0.0)
                elif supplier_name == "PF Concept" and sku_key in pf_prices:
                    try:
                        price_val = pf_prices[sku_key]["scales"][0]["scale"][0]["nettPrice"]
                    except (KeyError, IndexError):
                        price_val = 0.0

            tier_entry = db.query(PricingTier).filter(
                PricingTier.offer_id == offer.id,
                PricingTier.from_quantity == 1
            ).first()

            if not tier_entry:
                db.add(PricingTier(
                    id=str(uuid.uuid4()),
                    offer_id=offer.id,
                    from_quantity=1,
                    to_quantity=None,
                    price=float(price_val or 0.0)
                ))

            # Commit periodically to keep memory flat
            if idx % 500 == 0 and idx > 0:
                db.commit()

        except Exception as single_error:
            print(f"Error on record {idx}: {single_error} | supplier: {mp.get('supplier')} | sku: {mp.get('sku')}")
            db.rollback()
            continue

    db.commit()
    print("\n🎉 SUCCESS: ALL CHANNELS INTERCEPTED SUCCESSFULLY!")
    print(f"   Total Master Products: {products_added}")
    print(f"   Total Supplier Offers Registered: {offers_added}")
    db.close()

if __name__ == "__main__":
    run_ingestion()