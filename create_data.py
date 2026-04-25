"""
create_data.py
--------------
Drops the inventory table (CASCADE), recreates it with the new schema,
and bulk-inserts all rows from goldbook_full_data.xlsx.

Run:
    python create_data.py
"""

import pandas as pd
import math
from sqlalchemy import text
from models.database import engine, Base, Item, SessionLocal

EXCEL_FILE = "goldbook_full_data.xlsx"


def _f(val, fallback=None):
    """Return fallback for NaN/None, else the raw value."""
    if val is None:
        return fallback
    try:
        if math.isnan(float(val)):
            return fallback
    except (TypeError, ValueError):
        pass
    return val


def reset_and_seed_inventory():
    # 1. Drop the inventory table (CASCADE removes dependent bill_items rows/FKs too)
    with engine.connect() as conn:
        conn.execute(text("DROP TABLE IF EXISTS bill_items CASCADE"))
        conn.execute(text("DROP TABLE IF EXISTS inventory CASCADE"))
        conn.commit()
        print("[OK] inventory (and bill_items) tables dropped.")

    # 2. Recreate all tables from the updated models
    Base.metadata.create_all(engine)
    print("[OK] Tables recreated with new schema.")

    # 3. Read Excel
    df = pd.read_excel(EXCEL_FILE)
    df.columns = [c.strip() for c in df.columns]
    print(f"[>>] Read {len(df)} rows from '{EXCEL_FILE}'.")
    print("     Columns:", df.columns.tolist())

    # 4. Bulk-insert
    db = SessionLocal()
    try:
        items = []
        for _, row in df.iterrows():
            tag_raw  = _f(row.get("Tag No"))
            size_raw = _f(row.get("Size"))

            item = Item(
                tag_no      = str(int(float(tag_raw))).zfill(10) if tag_raw is not None else None,
                item_code   = str(_f(row.get("It Code"), "")).strip() or None,
                item_name   = str(_f(row.get("It Name"), "Unknown")).strip(),
                pcs         = _f(row.get("Pcs")),
                size        = str(int(float(size_raw))) if size_raw is not None else None,
                design      = str(_f(row.get("Design"), "")).strip() or None,
                gr_wt       = _f(row.get("GrWt")),
                net_wt      = _f(row.get("NtWt")),
                ghat_wt     = _f(row.get("GhatWt")),
                touch       = _f(row.get("Touch")),
                wst_percent = _f(row.get("Wst%")),
                mrp         = _f(row.get("MRP")),
            )
            items.append(item)

        db.bulk_save_objects(items)
        db.commit()
        print(f"[OK] Inserted {len(items)} items into the inventory table.")
    except Exception as e:
        db.rollback()
        print(f"[ERROR] {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    reset_and_seed_inventory()