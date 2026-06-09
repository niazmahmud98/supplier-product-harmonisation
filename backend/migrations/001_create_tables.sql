-- Updated Database Migration Script with Distinct Prefixes

-- Core product table
CREATE TABLE "HarmonizedProducts" (
    id UUID PRIMARY KEY,
    name VARCHAR NOT NULL,
    description TEXT,
    category VARCHAR NOT NULL,
    material VARCHAR,
    brand VARCHAR
);

-- Color/size variants of a product
CREATE TABLE "HarmonizedVariants" (
    id UUID PRIMARY KEY,
    product_id UUID NOT NULL REFERENCES "HarmonizedProducts"(id) ON DELETE CASCADE,
    color VARCHAR,
    size VARCHAR,
    dimensions JSONB
);

-- Supplier specific data for each variant
CREATE TABLE "HarmonizedSupplierOffers" (
    id UUID PRIMARY KEY,
    variant_id UUID NOT NULL REFERENCES "HarmonizedVariants"(id) ON DELETE CASCADE,
    supplier VARCHAR NOT NULL,
    supplier_sku VARCHAR NOT NULL,
    currency VARCHAR NOT NULL DEFAULT 'EUR',
    stock INTEGER NOT NULL DEFAULT 0
);

-- MOQ based pricing
CREATE TABLE "HarmonizedPricingTiers" (
    id UUID PRIMARY KEY,
    offer_id UUID NOT NULL REFERENCES "HarmonizedSupplierOffers"(id) ON DELETE CASCADE,
    from_quantity INTEGER NOT NULL,
    to_quantity INTEGER,
    price NUMERIC(10, 2) NOT NULL
);