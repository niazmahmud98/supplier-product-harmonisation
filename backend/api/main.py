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
    category: Optional[str] = Query(None),
    supplier: Optional[str] = Query(None),
    in_stock: Optional[bool] = Query(None),
    search: Optional[str] = Query(None),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Results per page"),
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

  # Pagination
    total = len(products)
    start = (page - 1) * limit
    end = start + limit

    return {
        "total": total,
        "page": page,
        "limit": limit,
        "total_pages": -(-total // limit),  # ceiling division
        "products": products[start:end]
    }


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
@app.get("/quality/uncategorized", summary="Get uncategorized products grouped by supplier")
def get_uncategorized_by_supplier(db: Session = Depends(get_db)):
    uncategorized = db.query(Product).filter(
        Product.category.ilike("Uncategorized")
    ).options(
        joinedload(Product.variants).joinedload(Variant.offers)
    ).all()

    # Create group according to supplier
    supplier_map = {}
    for p in uncategorized:
        suppliers = set()
        for v in p.variants:
            for o in v.offers:
                if o.supplier:
                    suppliers.add(o.supplier)
        for s in suppliers:
            if s not in supplier_map:
                supplier_map[s] = []
            supplier_map[s].append(p.name)

    return [
        {"supplier": supplier, "count": len(products), "sample_products": products}
        for supplier, products in sorted(supplier_map.items())
    ]

# =========================================================================
# PHASE 10: WORK ITEM 10.1, 10.2 & 10.3 — BUSINESS INTELLIGENCE LAYER
# =========================================================================

@app.get("/analytics/suppliers", summary="Work Item 10.1: Deep Supplier BI Insights")
def get_supplier_insights(db: Session = Depends(get_db)):
    """
    Analyzes corporate vendors to evaluate supply metrics:
    - Top Stock Holders
    - Price Leadership (Cheapest Vendors)
    - Catalogue Completeness (Density of variants populated)
    """
    # 1. Total stock pool per supplier
    stock_query = db.query(SupplierOffer.supplier, func.sum(SupplierOffer.stock)).group_by(SupplierOffer.supplier).all()
    stock_insights = {row[0]: row[1] or 0 for row in stock_query}

    # 2. Average price benchmark per supplier to identify the cheapest vendor
    price_query = db.query(SupplierOffer.supplier, func.avg(PricingTier.price))\
                    .join(PricingTier, SupplierOffer.id == PricingTier.offer_id)\
                    .group_by(SupplierOffer.supplier).all()
    price_insights = {row[0]: round(row[1], 2) if row[1] else 0.0 for row in price_query}

    # 3. Completeness: Count how many unique variant offers each supplier registered
    completeness_query = db.query(SupplierOffer.supplier, func.count(SupplierOffer.id)).group_by(SupplierOffer.supplier).all()
    completeness_insights = {row[0]: row[1] for row in completeness_query}

    # Rank & Compile the Top Suppliers
    return {
        "highest_stock_suppliers": stock_insights,
        "cheapest_suppliers_avg_price": price_insights,
        "catalogue_completeness_offers": completeness_insights,
        "market_share_leader": max(completeness_insights, key=completeness_insights.get) if completeness_insights else "N/A"
    }


@app.get("/analytics/pricing", summary="Work Item 10.2: Advanced Pricing Spread & Anomalies")
def get_pricing_anomalies(db: Session = Depends(get_db)):
    """
    Runs statistical analysis over pricing structures to detect:
    - Suspicious low/high prices (Outliers)
    - Price spreads across variants
    """
    # Fetch all pricing tiers connected to their product schemas
    prices = db.query(PricingTier.price).all()
    flat_prices = [p[0] for p in prices if p[0] > 0]

    if not flat_prices:
        return {"message": "Insufficient pricing data to run statistical matrices.", "anomalies": []}

    # Calculate global statistical baseline benchmarks
    avg_price = sum(flat_prices) / len(flat_prices)
    max_price = max(flat_prices)
    min_price = min(flat_prices)

    # Flag suspicious pricing anomalies (e.g., items priced under €0.50 or over 10x the global average)
    suspicious_records = db.query(Product.name, SupplierOffer.supplier, PricingTier.price)\
                           .join(Variant, Product.id == Variant.product_id)\
                           .join(SupplierOffer, Variant.id == SupplierOffer.variant_id)\
                           .join(PricingTier, SupplierOffer.id == PricingTier.offer_id)\
                           .filter((PricingTier.price < 0.50) | (PricingTier.price > (avg_price * 5))).all()

    return {
        "global_price_metrics": {
            "average_unit_cost": f"€{round(avg_price, 2)}",
            "highest_market_price": f"€{round(max_price, 2)}",
            "lowest_market_price": f"€{round(min_price, 2)}",
            "total_price_points_evaluated": len(flat_prices)
        },
        "suspicious_price_anomalies": [
            {"product": row[0], "supplier": row[1], "flagged_price": f"€{round(row[2], 2)}", "reason": "Potential Outlier Margin / Feeder Data Error"}
            for row in suspicious_records[:15]  # Stream top 15 anomalies to prevent UI bloating
        ]
    }


@app.get("/analytics/health", summary="Work Item 10.3: Catalogue Data Health Metrics")
def get_catalogue_health_metrics(db: Session = Depends(get_db)):
    """
    Evaluates global health data structures:
    - Duplicate Density
    - Normalization Coverage
    - Attribute Completeness (Missing descriptions, colors, sizes)
    """
    total_products = db.query(Product).count()
    if total_products == 0:
        return {"catalogue_health_score": "100%", "status": "Empty Dataset"}

    # 1. Duplicate Density Profile
    duplicate_names = db.query(Product.name).group_by(Product.name).having(func.count(Product.name) > 1).all()
    duplicate_density_pct = (len(duplicate_names) / total_products) * 100

    # 2. Normalization Coverage (Items not flagged as "Uncategorized")
    uncategorized_count = db.query(Product).filter(Product.category.ilike("Uncategorized")).count()
    normalization_coverage_pct = ((total_products - uncategorized_count) / total_products) * 100

    # 3. Attribute Completeness (Scan for missing critical product information)
    missing_desc_count = db.query(Product).filter((Product.description == None) | (Product.description == "")).count()
    attribute_completeness_pct = ((total_products - missing_desc_count) / total_products) * 100

    # Compound Health Score Matrix
    overall_health = (normalization_coverage_pct + attribute_completeness_pct - duplicate_density_pct) / 2

    return {
        "composite_catalogue_health_score": f"{round(max(0, min(100, overall_health)), 2)}%",
        "metrics": {
            "duplicate_density_profile": f"{round(duplicate_density_pct, 2)}%",
            "normalization_coverage_rate": f"{round(normalization_coverage_pct, 2)}%",
            "attribute_completeness_rate": f"{round(attribute_completeness_pct, 2)}%"
        },
        "raw_counts": {
            "total_master_records": total_products,
            "flagged_unmapped_categories": uncategorized_count,
            "records_missing_descriptions": missing_desc_count
        }
    }

# =========================================================================
# WORK ITEM 9.3: DISTRIBUTION CHARTS & MISSING FIELDS
# =========================================================================

@app.get("/analytics/distributions", summary="Price, Stock & Missing Fields distributions")
def get_distributions(db: Session = Depends(get_db)):

    # 1. Missing Fields %
    total_products = db.query(Product).count()
    total_variants = db.query(Variant).count()

    missing_desc = db.query(Product).filter(
        (Product.description == None) | (Product.description == "")
    ).count()
    missing_material = db.query(Product).filter(
        (Product.material == None) | (Product.material == "") | (Product.material == "Unknown")
    ).count()
    missing_color = db.query(Variant).filter(
        (Variant.color == None) | (Variant.color == "")
    ).count()
    missing_size = db.query(Variant).filter(
        (Variant.size == None) | (Variant.size == "")
    ).count()

    missing_fields = {
        "description": f"{round((missing_desc / total_products) * 100, 1)}%" if total_products else "0%",
        "material": f"{round((missing_material / total_products) * 100, 1)}%" if total_products else "0%",
        "color": f"{round((missing_color / total_variants) * 100, 1)}%" if total_variants else "0%",
        "size": f"{round((missing_size / total_variants) * 100, 1)}%" if total_variants else "0%",
    }

    # 2. Price Distribution — group prices into ranges
    prices = db.query(PricingTier.price).filter(PricingTier.price > 0).all()
    flat_prices = [p[0] for p in prices]

    price_ranges = {"€0–5": 0, "€5–15": 0, "€15–30": 0, "€30–60": 0, "€60+": 0}
    for p in flat_prices:
        if p < 5:
            price_ranges["€0–5"] += 1
        elif p < 15:
            price_ranges["€5–15"] += 1
        elif p < 30:
            price_ranges["€15–30"] += 1
        elif p < 60:
            price_ranges["€30–60"] += 1
        else:
            price_ranges["€60+"] += 1

    # 3. Stock Distribution — group stock into ranges
    stocks = db.query(SupplierOffer.stock).all()
    flat_stocks = [s[0] for s in stocks if s[0] is not None]

    stock_ranges = {"0": 0, "1–50": 0, "51–200": 0, "201–500": 0, "500+": 0}
    for s in flat_stocks:
        if s == 0:
            stock_ranges["0"] += 1
        elif s <= 50:
            stock_ranges["1–50"] += 1
        elif s <= 200:
            stock_ranges["51–200"] += 1
        elif s <= 500:
            stock_ranges["201–500"] += 1
        else:
            stock_ranges["500+"] += 1

    return {
        "missing_fields": missing_fields,
        "price_distribution": price_ranges,
        "stock_distribution": stock_ranges
    }

@app.get("/analytics/top-products", summary="Top 10 products by stock")
def get_top_products_by_stock(db: Session = Depends(get_db)):
    results = db.query(
        Product.name,
        func.sum(SupplierOffer.stock).label("total_stock")
    ).join(Product.variants)\
     .join(Variant.offers)\
     .group_by(Product.name)\
     .order_by(func.sum(SupplierOffer.stock).desc())\
     .limit(10).all()

    return [{"name": row[0], "stock": row[1] or 0} for row in results]