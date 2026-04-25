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
    tag_no = Column(String, nullable=True)       # Tag No (barcode)
    item_code = Column(String, nullable=True)    # It Code
    item_name = Column(String, nullable=False)   # It Name
    pcs = Column(Float, nullable=True)           # Pcs
    size = Column(String, nullable=True)         # Size
    design = Column(String, nullable=True)       # Design
    gr_wt = Column(Float, nullable=True)         # GrWt
    net_wt = Column(Float, nullable=True)        # NtWt
    ghat_wt = Column(Float, nullable=True)       # GhatWt
    touch = Column(Float, nullable=True)         # Touch
    wst_percent = Column(Float, nullable=True)   # Wst%
    mrp = Column(Float, nullable=True)           # MRP

# 2.7 Billing System (Estimates & Final Bills)
class Bill(Base):
    __tablename__ = 'bills'
    id = Column(Integer, primary_key=True)
    voucher = Column(String, nullable=True)
    customer_name = Column(String, nullable=False)
    customer_phone = Column(String)
    date = Column(DateTime, default=datetime.utcnow)
    is_estimate = Column(Boolean, default=True)
    total_amount = Column(Float, default=0.0)
    total_fine = Column(Float, nullable=True)
    fine_9950 = Column(Float, nullable=True)
    rate_cut = Column(Float, nullable=True)
    
    # 2.2 Staff Panel (Tracking who made the sale)
    created_by_id = Column(Integer, ForeignKey('users.id'))
    creator = relationship("User")
    items = relationship("BillItem", back_populates="bill")

class BillItem(Base):
    __tablename__ = 'bill_items'
    id = Column(Integer, primary_key=True)
    bill_id = Column(Integer, ForeignKey('bills.id'))
    item_id = Column(Integer, ForeignKey('inventory.id'), nullable=True)
    quantity = Column(Integer, default=1)
    price = Column(Float, nullable=False)
    
    tag = Column(String, nullable=True)
    name = Column(String, nullable=True)
    net_wt = Column(Float, nullable=True)
    touch = Column(Float, nullable=True)
    wastage = Column(Float, nullable=True)
    fine = Column(Float, nullable=True)
    
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
