import os
import sys
from typing import Optional
from fastapi import FastAPI, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

# -------------------------------------------------------------------------
# PATH CONFIGURATION
# -------------------------------------------------------------------------
# Explicitly append the parent directory (backend root) to sys.path.
# This prevents ModuleNotFoundError when importing database 'models'.
sys.path.append(os.path.dirname(os.path.abspath(__file__)).replace("\\api", "").replace("/api", ""))

from models import SessionLocal, Product, Variant, SupplierOffer, PricingTier

# -------------------------------------------------------------------------
# FASTAPI APPLICATION INITIALIZATION
# -------------------------------------------------------------------------
app = FastAPI(
    title="Supplier Product Harmonisation API",
    description="Phase 8 Official Catalog & Metrics API Layer exposed for Staging/Production environments.",
    version="1.0.0"
)
@app.get("/debug")
def debug():
    import sqlite3
    from models import engine
    return {"db_url": str(engine.url), "db_path": str(engine.url).replace("sqlite:///", "")}


from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows local frontend server files to call the API safely
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------------------------------------------------------
# DATABASE SESSION DEPENDENCY
# -------------------------------------------------------------------------
def get_db():
    # Yields a database session instance per request and ensures proper connection closure.
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# =========================================================================
# WORK ITEM 8.1 & 8.2: PRODUCT ENDPOINTS, SEARCH & FILTERING
# =========================================================================

@app.get("/products", summary="Get all harmonized products with advanced filters")
def get_products(
    category: Optional[str] = Query(None, description="Filter exactly by product category"),
    supplier: Optional[str] = Query(None, description="Filter products supplied by a specific supplier name"),
    in_stock: Optional[bool] = Query(None, description="True: returns only available variants, False: returns out-of-stock"),
    search: Optional[str] = Query(None, description="Case-insensitive keyword search in product name or description"),
    db: Session = Depends(get_db)
):
    # Base Query with eager loading optimized for the renamed 'Harmonized' tables setup
    query = db.query(Product).options(
        joinedload(Product.variants)
        .joinedload(Variant.offers)
        .joinedload(SupplierOffer.pricing_tiers)
    )

    # 1. Keyword Search Logic (Work Item 8.2)
    if search:
        query = query.filter(
            Product.name.ilike(f"%{search}%") | 
            Product.description.ilike(f"%{search}%")
        )

    # 2. Category Filter Logic (Work Item 8.2)
    if category:
        query = query.filter(Product.category.ilike(category))

    # 3. Supplier Filter Logic (Work Item 8.2)
    if supplier:
        query = query.join(Product.variants).join(Variant.offers).filter(
            SupplierOffer.supplier.ilike(supplier)
        )

    # Execute database fetch
    products = query.all()

    # 4. In-Stock Filtering Logic (Work Item 8.2)
    if in_stock is not None:
        filtered_products = []
        for p in products:
            keep_product = False
            for v in p.variants:
                total_stock = sum([offer.stock for offer in v.offers])
                if (in_stock and total_stock > 0) or (not in_stock and total_stock == 0):
                    keep_product = True
                    break
            if keep_product:
                filtered_products.append(p)
        return filtered_products

    return products


@app.get("/products/{product_id}", summary="Get a single product by its UUID")
def get_product_by_id(product_id: str, db: Session = Depends(get_db)):
    # Retrieves a single master product by its unique UUID token.
    product = db.query(Product).options(
        joinedload(Product.variants)
        .joinedload(Variant.offers)
        .joinedload(SupplierOffer.pricing_tiers)
    ).filter(Product.id == product_id).first()
    
    if not product:
        raise HTTPException(status_code=404, detail="Product not found in the database")
    return product


@app.get("/categories", summary="Get a unique list of all harmonized categories")
def get_categories(
    supplier: Optional[str] = Query(None, description="Filter categories by supplier"),
    db: Session = Depends(get_db)
):
    query = db.query(Product.category).distinct()
    
 
    if supplier:
        query = query.join(Product.variants).join(Variant.offers).filter(
            SupplierOffer.supplier.ilike(supplier)
        )
    
    categories = query.all()
    return [c[0] for c in categories if c[0]]


@app.get("/suppliers", summary="Get a unique list of all suppliers")
def get_suppliers(db: Session = Depends(get_db)):
    # Extracts a distinct list of all active suppliers currently owning an offer.
    suppliers = db.query(SupplierOffer.supplier).distinct().all()
    return [s[0] for s in suppliers if s[0]]


# =========================================================================
# WORK ITEM 8.3: METRICS ENDPOINTS (DATA QUALITY & ANALYTICS)
# =========================================================================

@app.get("/metrics", summary="Get global platform sync metrics")
def get_platform_metrics(db: Session = Depends(get_db)):
    # Aggregates high-level inventory metrics for the executive dashboard
    total_products = db.query(Product).count()
    total_variants = db.query(Variant).count()
    total_offers = db.query(SupplierOffer).count()
    total_stock = db.query(func.sum(SupplierOffer.stock)).scalar() or 0
    
    return {
        "total_harmonized_products": total_products,
        "total_resolved_variants": total_variants,
        "total_supplier_offers": total_offers,
        "total_global_stock_pool": total_stock
    }


@app.get("/duplicates", summary="Identify potential product naming duplicates")
def get_potential_duplicates(db: Session = Depends(get_db)):
    # Finds products sharing identical names to pinpoint data redundancy
    duplicate_names = db.query(Product.name).group_by(Product.name).having(func.count(Product.name) > 1).all()
    flat_names = [d[0] for d in duplicate_names]
    
    if not flat_names:
        return {"message": "System data clean! No naming duplicates found.", "duplicates": []}
        
    duplicated_products = db.query(Product).filter(Product.name.in_(flat_names)).all()
    return {
        "total_duplicate_groups": len(flat_names),
        "flagged_products": duplicated_products
    }


@app.get("/quality", summary="Check data harmonisation quality scoring")
def get_data_quality_score(db: Session = Depends(get_db)):
    # Measures the percentage of successfully categorized items (Uncategorized vs Clean data)
    total_count = db.query(Product).count()
    if total_count == 0:
        return {"quality_score": "100%", "uncategorized_count": 0, "total_count": 0}
        
    uncategorized_count = db.query(Product).filter(Product.category.ilike("Uncategorized")).count()
    categorized_count = total_count - uncategorized_count
    quality_percentage = (categorized_count / total_count) * 100
    
    return {
        "overall_harmonisation_quality": f"{round(quality_percentage, 2)}%",
        "total_records_evaluated": total_count,
        "successfully_categorized": categorized_count,
        "flagged_uncategorized_records": uncategorized_count
    }