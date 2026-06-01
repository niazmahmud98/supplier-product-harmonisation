# Canonical Product Schema
# This document defines the unified data model for the Supplier Product Harmonisation System.
# All supplier data is mapped into this structure regardless of source.

---

## Entities & Relationships

Product (1) → Variant (many)
Variant (1) → SupplierOffer (many)
SupplierOffer (1) → PricingTier (many)
SupplierOffer (1) → Stock (1)

---

## 1. Product
Stores core product information. Abstract item - not supplier specific.

| Field       | Type   | Required | Description              |
|-------------|--------|----------|--------------------------|
| id          | UUID   | Yes      | Unique product ID        |
| name        | String | Yes      | Normalised product name  |
| description | String | No       | Product description      |
| category    | String | Yes      | Harmonised category      |
| material    | String | No       | Normalised material      |
| brand       | String | No       | Brand name               |

---

## 2. Variant
Color/size options of a product.

| Field      | Type   | Required | Description         |
|------------|--------|----------|---------------------|
| id         | UUID   | Yes      | Unique variant ID   |
| product_id | UUID   | Yes      | Links to Product    |
| color      | String | No       | Normalised color    |
| size       | String | No       | Size label          |
| dimensions | JSON   | No       | length/width/height |

---

## 3. SupplierOffer
Supplier specific data for a variant.

| Field        | Type   | Required | Description            |
|--------------|--------|----------|------------------------|
| id           | UUID   | Yes      | Unique offer ID        |
| variant_id   | UUID   | Yes      | Links to Variant       |
| supplier     | String | Yes      | Supplier name          |
| supplier_sku | String | Yes      | Supplier product code  |
| currency     | String | Yes      | Always EUR             |
| stock        | Int    | Yes      | Available stock        |

---

## 4. PricingTier
MOQ-based pricing for each supplier offer.

| Field          | Type  | Required | Description          |
|----------------|-------|----------|----------------------|
| id             | UUID  | Yes      | Unique tier ID       |
| offer_id       | UUID  | Yes      | Links to SupplierOffer|
| from_quantity  | Int   | Yes      | Minimum order qty    |
| to_quantity    | Int   | No       | Maximum order qty    |
| price          | Float | Yes      | Price per unit       |

---

## Assumptions
- All prices are in EUR
- All dimensions are in cm
- Missing fields default to null
- Category is always normalised via CATEGORY_MAP
- Color is always normalised via COLOR_MAP