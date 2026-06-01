# Defines the database tables for PostgreSQL
# Each class = one table in the database

from sqlalchemy import Column, String, Float, Integer, JSON, ForeignKey
from sqlalchemy.orm import relationship, declarative_base

# Base class - all models inherit from this
Base = declarative_base()


class Product(Base):
    # Core product info - not supplier specific
    # One product can have many variants
    __tablename__ = "products"

    id          = Column(String, primary_key=True)  # unique UUID
    name        = Column(String, nullable=False)     # normalised name
    description = Column(String, nullable=True)      # product description
    category    = Column(String, nullable=False)     # harmonised category
    material    = Column(String, nullable=True)      # normalised material
    brand       = Column(String, nullable=True)      # brand name

    variants = relationship("Variant", back_populates="product")


class Variant(Base):
    # Color/size options of a product
    # One variant can have many supplier offers
    __tablename__ = "variants"

    id         = Column(String, primary_key=True)        # unique UUID
    product_id = Column(String, ForeignKey("products.id")) # links to Product
    color      = Column(String, nullable=True)           # normalised color
    size       = Column(String, nullable=True)           # size label
    dimensions = Column(JSON, nullable=True)             # length/width/height in cm

    product         = relationship("Product", back_populates="variants")
    supplier_offers = relationship("SupplierOffer", back_populates="variant")


class SupplierOffer(Base):
    # Supplier specific data for a variant
    # One variant can be offered by multiple suppliers
    __tablename__ = "supplier_offers"

    id           = Column(String, primary_key=True)          # unique UUID
    variant_id   = Column(String, ForeignKey("variants.id")) # links to Variant
    supplier     = Column(String, nullable=False)            # supplier name
    supplier_sku = Column(String, nullable=False)            # supplier product code
    currency     = Column(String, default="EUR")             # always EUR
    stock        = Column(Integer, default=0)                # available stock

    variant       = relationship("Variant", back_populates="supplier_offers")
    pricing_tiers = relationship("PricingTier", back_populates="supplier_offer")


class PricingTier(Base):
    # MOQ based pricing - more you buy, cheaper the price
    __tablename__ = "pricing_tiers"

    id            = Column(String, primary_key=True)              # unique UUID
    offer_id      = Column(String, ForeignKey("supplier_offers.id")) # links to SupplierOffer
    from_quantity = Column(Integer, nullable=False)               # minimum order quantity
    to_quantity   = Column(Integer, nullable=True)                # maximum order quantity (null = no limit)
    price         = Column(Float, nullable=False)                 # price per unit in EUR

    supplier_offer = relationship("SupplierOffer", back_populates="pricing_tiers")