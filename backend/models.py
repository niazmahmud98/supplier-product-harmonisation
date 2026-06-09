import os
from sqlalchemy import create_engine, Column, String, Text, Integer, Numeric, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

# Database configuration logic we set up earlier
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    DATABASE_URL = "sqlite:///./local_harmonised.db"

if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
else:
    engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# =========================================================================
# REFACTORED MODELS WITH EXPLICIT FOREIGN KEY RELATIONSHIPS
# =========================================================================

class Product(Base):
    __tablename__ = "HarmonizedProducts"
    
    id = Column(String, primary_key=True)  # Using String for SQLite compatibility
    name = Column(String, nullable=False)
    description = Column(Text)
    category = Column(String, nullable=False)
    material = Column(String)
    brand = Column(String)
    
    # Explicitly mapping relationship to Variant class
    variants = relationship("Variant", back_populates="product", cascade="all, delete-orphan")


class Variant(Base):
    __tablename__ = "HarmonizedVariants"
    
    id = Column(String, primary_key=True)
    # Explicitly targeting HarmonizedProducts.id
    product_id = Column(String, ForeignKey("HarmonizedProducts.id", ondelete="CASCADE"), nullable=False)
    color = Column(String)
    size = Column(String)
    dimensions = Column(String)  # Simple fallback or JSON representation
    
    product = relationship("Product", back_populates="variants")
    # Explicitly mapping relationship to SupplierOffer class
    offers = relationship("SupplierOffer", back_populates="variant", cascade="all, delete-orphan")


class SupplierOffer(Base):
    __tablename__ = "HarmonizedSupplierOffers"
    
    id = Column(String, primary_key=True)
    # Explicitly targeting HarmonizedVariants.id
    variant_id = Column(String, ForeignKey("HarmonizedVariants.id", ondelete="CASCADE"), nullable=False)
    supplier = Column(String, nullable=False)
    supplier_sku = Column(String, nullable=False)
    currency = Column(String, nullable=False, default="EUR")
    stock = Column(Integer, nullable=False, default=0)
    
    variant = relationship("Variant", back_populates="offers")
    # Explicitly mapping relationship to PricingTier class
    pricing_tiers = relationship("PricingTier", back_populates="offer", cascade="all, delete-orphan")


class PricingTier(Base):
    __tablename__ = "HarmonizedPricingTiers"
    
    id = Column(String, primary_key=True)
    # Explicitly targeting HarmonizedSupplierOffers.id
    offer_id = Column(String, ForeignKey("HarmonizedSupplierOffers.id", ondelete="CASCADE"), nullable=False)
    from_quantity = Column(Integer, nullable=False)
    to_quantity = Column(Integer)
    price = Column(Numeric(10, 2), nullable=False)
    
    offer = relationship("SupplierOffer", back_populates="pricing_tiers")