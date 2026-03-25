from typing import List, Dict, Any, Set
from sqlalchemy import text
from sqlalchemy.orm import Session
import logging

logger = logging.getLogger(__name__)

# Fast memory caches tracking records that explicitly passed into Postgres
seen_orders: Set[str] = set()
seen_deliveries: Set[str] = set()
seen_invoices: Set[str] = set()
seen_payments: Set[str] = set()
seen_products: Set[str] = set()
seen_customers: Set[str] = set()

def insert_customers(db: Session, customers: List[Dict[str, Any]]) -> int:
    unique = []
    for c in customers:
        if c and c["customer_id"] and c["customer_id"] not in seen_customers:
            unique.append(c)
            seen_customers.add(c["customer_id"])
    if not unique: return 0
    try:
        # bulk_insert via sqlalchemy natively using db.execute on array mapping
        sql = text("""
            INSERT INTO customers (customer_id, name, city, postal_code) 
            VALUES (:customer_id, :name, :city, :postal_code) 
            ON CONFLICT (customer_id) DO NOTHING
        """)
        db.execute(sql, unique)
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"Error inserting customers: {e}")
    return len(unique)

def insert_products(db: Session, products: List[Dict[str, Any]]) -> int:
    unique = []
    for p in products:
        if p and p["product_id"] and p["product_id"] not in seen_products:
            unique.append(p)
            seen_products.add(p["product_id"])
    if not unique: return 0
    try:
        sql = text("""
            INSERT INTO products (product_id, description) 
            VALUES (:product_id, :description) 
            ON CONFLICT (product_id) DO NOTHING
        """)
        db.execute(sql, unique)
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"Error inserting products: {e}")
    return len(unique)

def insert_orders(db: Session, orders: List[Dict[str, Any]]) -> int:
    unique = []
    for o in orders:
        if o and o["order_id"] and o["order_id"] not in seen_orders:
            if o["customer_id"] in seen_customers:
                unique.append(o)
                seen_orders.add(o["order_id"])
    if not unique: return 0
    try:
        sql = text("""
            INSERT INTO orders (order_id, customer_id, created_at) 
            VALUES (:order_id, :customer_id, CAST(:created_at AS TIMESTAMP)) 
            ON CONFLICT (order_id) DO NOTHING
        """)
        db.execute(sql, unique)
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"Error inserting orders: {e}")
    return len(unique)

def insert_order_items(db: Session, items: List[Dict[str, Any]]) -> int:
    valid = []
    for item in items:
        if item and item["order_id"] in seen_orders and item["product_id"] in seen_products:
            valid.append(item)
    if not valid: return 0
    try:
        sql = text("""
            INSERT INTO order_items (order_id, product_id, quantity) 
            VALUES (:order_id, :product_id, :quantity)
        """)
        db.execute(sql, valid)
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"Error inserting order items: {e}")
    return len(valid)

def insert_deliveries(db: Session, deliveries: List[Dict[str, Any]]) -> int:
    unique = []
    for d in deliveries:
        if d and d["delivery_id"] and d["delivery_id"] not in seen_deliveries:
            if d["order_id"] in seen_orders:
                unique.append(d)
                seen_deliveries.add(d["delivery_id"])
    if not unique: return 0
    try:
        sql = text("""
            INSERT INTO deliveries (delivery_id, order_id, created_at) 
            VALUES (:delivery_id, :order_id, CAST(:created_at AS TIMESTAMP)) 
            ON CONFLICT (delivery_id) DO NOTHING
        """)
        db.execute(sql, unique)
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"Error inserting deliveries: {e}")
    return len(unique)

def insert_invoices(db: Session, invoices: List[Dict[str, Any]]) -> int:
    unique = []
    for i in invoices:
        if i and i["invoice_id"] and i["invoice_id"] not in seen_invoices:
            # SAP invoices usually link directly to Delivery (referenceDocument = 8*) 
            has_parent = (i["delivery_id"] in seen_deliveries) or (i["order_id"] in seen_orders)
            if has_parent:
                if i["delivery_id"] not in seen_deliveries:
                    i["delivery_id"] = None
                if i["order_id"] not in seen_orders:
                    i["order_id"] = None
                    
                unique.append(i)
                seen_invoices.add(i["invoice_id"])
    if not unique: return 0
    try:
        sql = text("""
            INSERT INTO invoices (invoice_id, delivery_id, order_id, total_amount) 
            VALUES (:invoice_id, :delivery_id, :order_id, :total_amount) 
            ON CONFLICT (invoice_id) DO NOTHING
        """)
        db.execute(sql, unique)
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"Error inserting invoices: {e}")
    return len(unique)

def insert_payments(db: Session, payments: List[Dict[str, Any]]) -> int:
    unique = []
    for p in payments:
        if p and p["payment_id"] and p["payment_id"] not in seen_payments:
            if p["invoice_id"] in seen_invoices:
                unique.append(p)
                seen_payments.add(p["payment_id"])
    if not unique: return 0
    try:
        sql = text("""
            INSERT INTO payments (payment_id, invoice_id, amount) 
            VALUES (:payment_id, :invoice_id, :amount) 
            ON CONFLICT (payment_id) DO NOTHING
        """)
        db.execute(sql, unique)
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"Error inserting payments: {e}")
    return len(unique)
