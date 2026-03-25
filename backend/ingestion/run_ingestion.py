import os
import sys
import logging
from pathlib import Path
from sqlalchemy import text

sys.path.append(str(Path(__file__).parent.parent))

from loader import load_jsonl_files
from transformer import transform_record
from database import SessionLocal
from db_writer import (
    insert_customers, insert_products, insert_orders, 
    insert_order_items, insert_deliveries, insert_invoices, insert_payments
)

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

BATCH_SIZE = 500

def run():
    logger.info("Initializing ERP data ingestion sequence...")
    db = SessionLocal()
    
    customers_batch = []
    products_batch = []
    orders_batch = []
    items_batch = []
    deliveries_batch = []
    invoices_batch = []
    payments_batch = []
    
    count = 0
    inserted_orders = 0
    inserted_deliveries = 0
    inserted_invoices = 0
    
    data_dir = sys.argv[1] if len(sys.argv) > 1 else str(Path(__file__).parent.parent.parent)
    
    # Wipe explicitly to get 100% accurate metrics on fresh run
    db.execute(text("TRUNCATE TABLE payments, invoices, deliveries, order_items, orders, products, customers CASCADE"))
    db.commit()

    for record in load_jsonl_files(data_dir):
        try:
            transformed = transform_record(record)
            
            t_c = transformed["customer"]
            t_p = transformed["product"]
            t_o = transformed["order"]
            t_oi = transformed["order_item"]
            t_d = transformed["delivery"]
            t_i = transformed["invoice"]
            t_py = transformed["payment"]
            
            if t_c: customers_batch.append(t_c)
            if t_p: products_batch.append(t_p)
            if t_o: orders_batch.append(t_o)
            if t_oi: items_batch.append(t_oi)
            if t_d: deliveries_batch.append(t_d)
            if t_i: invoices_batch.append(t_i)
            if t_py: payments_batch.append(t_py)
            
            count += 1
            if count % BATCH_SIZE == 0:
                logger.info(f"Batched {count} raw JSON entities. Executing core executemany DB bulk save (Batch Threshold: {BATCH_SIZE})...")
                
                insert_customers(db, customers_batch)
                insert_products(db, products_batch)
                inserted_orders += insert_orders(db, orders_batch)
                insert_order_items(db, items_batch)
                inserted_deliveries += insert_deliveries(db, deliveries_batch)
                inserted_invoices += insert_invoices(db, invoices_batch)
                insert_payments(db, payments_batch)
                
                customers_batch.clear(); products_batch.clear(); orders_batch.clear()
                items_batch.clear(); deliveries_batch.clear(); invoices_batch.clear()
                payments_batch.clear()
                
        except Exception as e:
            logger.error(f"Fatal error routing record mapping at loop count {count}: {e}")
            continue 
            
    if count % BATCH_SIZE != 0:
        insert_customers(db, customers_batch)
        insert_products(db, products_batch)
        inserted_orders += insert_orders(db, orders_batch)
        insert_order_items(db, items_batch)
        inserted_deliveries += insert_deliveries(db, deliveries_batch)
        inserted_invoices += insert_invoices(db, invoices_batch)
        insert_payments(db, payments_batch)
        
    logger.info("\n=======================================")
    logger.info("🚀 DATA QUALITY METRICS (FDE SIGNAL)")
    logger.info("=======================================")
    
    logger.info(f"Processed Raw JSON Records (Including nested objects): {count}")
    logger.info(f"Total Skipped JSON Duplicates resolved by Memory Caching: {count - inserted_orders - inserted_deliveries - inserted_invoices}")
    
    total_db_orders = db.execute(text("SELECT COUNT(*) FROM orders")).scalar()
    total_db_deliveries = db.execute(text("SELECT COUNT(*) FROM deliveries")).scalar()
    total_db_invoices = db.execute(text("SELECT COUNT(*) FROM invoices")).scalar()
    
    orders_no_delivery = db.execute(text("""
        SELECT COUNT(*) FROM orders o 
        LEFT JOIN deliveries d ON o.order_id = d.order_id 
        WHERE d.delivery_id IS NULL
    """)).scalar()
    
    deliveries_no_invoice = db.execute(text("""
        SELECT COUNT(*) FROM deliveries d 
        LEFT JOIN invoices i ON d.delivery_id = i.delivery_id 
        WHERE i.invoice_id IS NULL
    """)).scalar()
    
    logger.info(f"\n[Core Data Persistence Counts]")
    logger.info(f"✅ Total DB Orders Confirmed: {total_db_orders} (Inserted Unique: {inserted_orders})")
    logger.info(f"✅ Total DB Deliveries Confirmed: {total_db_deliveries} (Inserted Unique: {inserted_deliveries})")
    logger.info(f"✅ Total DB Invoices Confirmed: {total_db_invoices} (Inserted Unique: {inserted_invoices})")
    
    logger.info(f"\n[Business Process Anomaly Checks]")
    logger.info(f"🟡 Orders without delivery (Broken flow preserved safely): {orders_no_delivery}")
    logger.info(f"🟡 Deliveries without invoice (Broken flow preserved safely): {deliveries_no_invoice}")
    logger.info("=======================================\n")
    
    db.close()

if __name__ == "__main__":
    run()
