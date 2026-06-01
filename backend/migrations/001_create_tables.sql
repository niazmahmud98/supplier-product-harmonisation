-- Database Migration Script for PostgreSQL
-- Creates all tables for the Supplier Product Harmonisation System

-- Core product table - supplier independent
CREATE TABLE products (
    id UUID PRIMARY KEY,
    name VARCHAR NOT NULL,
    description TEXT,
    category VARCHAR NOT NULL,  -- harmonised category
    material VARCHAR,
    brand VARCHAR
);

-- Color/size variants of a product
CREATE TABLE variants (
    id UUID PRIMARY KEY,
    product_id UUID NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    color VARCHAR,              -- normalised color
    size VARCHAR,
    dimensions JSONB            -- length/width/height in cm
);

-- Supplier specific data for each variant
CREATE TABLE supplier_offers (
    id UUID PRIMARY KEY,
    variant_id UUID NOT NULL REFERENCES variants(id) ON DELETE CASCADE,
    supplier VARCHAR NOT NULL,
    supplier_sku VARCHAR NOT NULL,
    currency VARCHAR NOT NULL DEFAULT 'EUR',
    stock INTEGER NOT NULL DEFAULT 0
);

-- MOQ based pricing - more you buy, cheaper the price
CREATE TABLE pricing_tiers (
    id UUID PRIMARY KEY,
    offer_id UUID NOT NULL REFERENCES supplier_offers(id) ON DELETE CASCADE,
    from_quantity INTEGER NOT NULL,
    to_quantity INTEGER,        -- null means no upper limit
    price NUMERIC(10, 2) NOT NULL
);