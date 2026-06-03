# Phase 4: Data Exploration & Quality Report
**Project:** Multi-Supplier Product & Price Harmonisation Engine  
**Author:** Backend Integration Engineer  
**Status:** Completed  

---

## 1. Executive Summary
This report profiles the raw data ingested during Phase 3 from three major promotional product suppliers: **European Sourcing**, **XD Connects**, and **PF Concept**. The goal was to identify semantic inconsistencies, structural fragmentation, and data quality flaws before pushing the data into the unified database.

The analysis proves that while data completeness is exceptionally high (0% missing critical values in monitored samples), severe fragmentation exists in **category taxonomies, localization languages, and hierarchical structures**.

---

## 2. Supplier Data Profile Comparison (Supplier Comparison Table)

| Quality Metric | European Sourcing (Controlled Sample) | XD Connects (Full Ingestion) | PF Concept (Price Feed Only) |
| :--- | :--- | :--- | :--- |
| **Analyzed Records** | 520 Products (1,040 Variant Items) | Full Catalog List | 2,057 Dynamic Model Items |
| **Completeness %** | 100% | 100% | 100% |
| **Duplicate Identifiers**| 936 (Expected due to variant mapping) | 0 | 0 |
| **Unique Categories** | 97 Categories | 15 Categories | N/A (Price Matrix Only) |
| **Unique Colors** | 5 Colors (Standard English) | 73 Colors (Mixed German/EN) | N/A |
| **Invalid/Zero Prices** | 0 | 0 | 0 |
| **Primary Currency** | EUR | EUR | EUR |

---

## 3. Core Inconsistencies & Quality Discoveries

### A. Category Fragmentation & Inconsistencies
* **European Sourcing:** Features highly atomic and loose tags (97 unique categories for 520 products). It mixes uppercase and lowercase names (e.g., `Backpack` vs `backpack`, `Ballpoint pen` vs `ballpoint pen`), which requires string normalization.
* **XD Connects:** Features a tightly controlled set of 15 categories, but they are fully localized in **German** (e.g., `Regenschirme` for Umbrellas, `Schreibgeräte` for Writing Instruments).
* **Harmonisation Challenge:** Phase 5 must map European Sourcing's loose tags and XD Connects' German terms into a unified, clean English canonical category tree.

### B. Color & Material Inconsistencies
* **European Sourcing:** Colors are extracted safely from nested attributes (`black`, `grey`, `navy blue`) and follow clean, lowercased English values.
* **XD Connects:** Colors are highly fragmented (73 unique colors) and suffer from severe multilingual mix-ups (e.g., `blau`, `braun`, `Hellgrau` in German alongside `Iceberg green`, `Sage blue` in English).
* **Harmonisation Challenge:** Colors must be sanitized, translated, and mapped to standard baseline colors during transformation.

### C. Structural & Nesting Complexities
* **European Sourcing:** Missing direct fields at the root layer. `name` and `description` are deeply nested within child `variants` objects, rather than the parent product envelope.
* **PF Concept:** Schema is highly complex. Target catalog prices do not exist in standard rows; they are deeply buried inside a multi-tier structure: `PFCPriceFeed -> priceInfo -> models -> items -> objectPrices -> scales`.
* **XD Connects:** Ingested directly as a flat list format rather than a wrapped dictionary payload object.

---

## 4. Invalid Data & Fraud Detection
* **Zero & Negative Prices:** Checked across all scale-pricing matrices across all three suppliers. **0 invalid instances detected.** All multi-tiered matrix pricing nodes contain mathematically sound values (`> 0.00`).
* **Missing Core Values:** All monitored records contain valid baseline identifiers, titles, and inventory schemas.

---

## 5. Next Steps for Phase 5 (Transformation Pipeline)
Based on these profiling metrics, the transformation script must enforce:
1. **Multilingual Translation Module:** Translate German colors and categories from XD Connects to English baseline terms.
2. **Text Normalization:** Apply lowercasing and trim whitespace to wipe out duplicate categories like `Backpack` and `backpack`.
3. **Identifier Extraction:** Flatten nested European Sourcing structures and multi-tiered PF Concept scaling tables into standard database models.