from models.database import SessionLocal, User, Item, Bill, BillItem, ShopConfig
from datetime import datetime, timedelta

def seed_data():
    db = SessionLocal()
    
    # 1. Add ShopConfig
    if not db.query(ShopConfig).first():
        shop = ShopConfig(
            shop_name="Luxe Jewels",
            owner_name="Jane Doe",
            contact="123-456-7890",
            gst_number="22AAAAA0000A1Z5",
            license_key="ABCD-EFGH-IJKL",
            license_expiry=datetime.utcnow() + timedelta(days=365)
        )
        db.add(shop)

    # 2. Add Users (Roles: Staff, Owner, MasterAdmin)
    if not db.query(User).first():
        master = User(username="master", password_hash="hashed_pw_master", role="MasterAdmin")
        owner = User(username="owner", password_hash="hashed_pw_owner", role="Owner")
        staff = User(username="staff1", password_hash="hashed_pw_staff", role="Staff")
        db.add_all([master, owner, staff])
        db.commit() # commit to get IDs

    staff_user = db.query(User).filter_by(role="Staff").first()

    # 3. Add Inventory
    if not db.query(Item).first():
        ring = Item(name="Gold Ring 24k", category="Rings", weight=5.5, stock_quantity=10)
        necklace = Item(name="Diamond Necklace", category="Necklaces", weight=15.0, stock_quantity=3)
        bangle = Item(name="Silver Bangle", category="Bangles", weight=20.0, stock_quantity=25)
        db.add_all([ring, necklace, bangle])
        db.commit() # commit to get IDs
        
    ring_item = db.query(Item).filter_by(name="Gold Ring 24k").first()
    necklace_item = db.query(Item).filter_by(name="Diamond Necklace").first()

    # 4. Add Bill & Bill Items
    if not db.query(Bill).first():
        bill1 = Bill(
            customer_name="John Smith",
            customer_phone="987-654-3210",
            is_estimate=False,
            total_amount=5500.0,
            created_by_id=staff_user.id
        )
        db.add(bill1)
        db.commit() # commit to get bill ID
        
        bill_item1 = BillItem(bill_id=bill1.id, item_id=ring_item.id, quantity=1, price=1500.0)
        bill_item2 = BillItem(bill_id=bill1.id, item_id=necklace_item.id, quantity=1, price=4000.0)
        db.add_all([bill_item1, bill_item2])

    db.commit()
    print("Database seeded successfully with sample data!")
    db.close()

if __name__ == "__main__":
    seed_data()
