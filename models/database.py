from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from datetime import datetime

Base = declarative_base()

# 2.1 Role-Based Management System
class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(String, nullable=False) # 'Staff', 'Owner', 'MasterAdmin'
    is_active = Column(Boolean, default=True)

# 2.3 Inventory Management
class Item(Base):
    __tablename__ = 'inventory'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    category = Column(String)
    weight = Column(Float)
    stock_quantity = Column(Integer, default=0)

# 2.7 Billing System (Estimates & Final Bills)
class Bill(Base):
    __tablename__ = 'bills'
    id = Column(Integer, primary_key=True)
    customer_name = Column(String, nullable=False)
    customer_phone = Column(String)
    date = Column(DateTime, default=datetime.utcnow)
    is_estimate = Column(Boolean, default=True)
    total_amount = Column(Float, default=0.0)
    
    # 2.2 Staff Panel (Tracking who made the sale)
    created_by_id = Column(Integer, ForeignKey('users.id'))
    creator = relationship("User")
    items = relationship("BillItem", back_populates="bill")

class BillItem(Base):
    __tablename__ = 'bill_items'
    id = Column(Integer, primary_key=True)
    bill_id = Column(Integer, ForeignKey('bills.id'))
    item_id = Column(Integer, ForeignKey('inventory.id'))
    quantity = Column(Integer, default=1)
    price = Column(Float, nullable=False)
    
    bill = relationship("Bill", back_populates="items")
    item = relationship("Item")

# 2.6 Initial Setup & 2.5 Licensing
class ShopConfig(Base):
    __tablename__ = 'shop_config'
    id = Column(Integer, primary_key=True)
    shop_name = Column(String)
    owner_name = Column(String)
    contact = Column(String)
    gst_number = Column(String)
    license_key = Column(String)
    license_expiry = Column(DateTime) # Nullable for lifetime

# Setup Engine and Session
DATABASE_URL = "postgresql://neondb_owner:npg_OShnU6w1lgqo@ep-odd-mode-a4rinqs3-pooler.us-east-1.aws.neon.tech/neondb?sslmode=require"
engine = create_engine(DATABASE_URL, echo=False)
Base.metadata.create_all(engine)
SessionLocal = sessionmaker(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
