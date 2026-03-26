from sqlalchemy import text
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

def trace_order_flow(db, order_id: str) -> Dict[str, Any]:
    """
    Returns the explicitly derived relationship graph spanning the complete 
    lineage of an Order. It uses LEFT JOINs across the dependent domains to 
    dynamically expose valid or broken flows (e.g. missing invoices).
    """
    # Specifically linking Order -> Invoice directly (derived) to sidestep 
    # delivery-only isolation loops if deliveries never triggered.
    query = text("""
        SELECT 
            o.order_id, o.customer_id, o.created_at as order_date,
            d.delivery_id, d.created_at as delivery_date,
            i.invoice_id, i.total_amount as invoice_amount,
            p.payment_id, p.amount as payment_amount
        FROM orders o
        LEFT JOIN deliveries d ON o.order_id = d.order_id
        LEFT JOIN invoices i ON o.order_id = i.order_id OR d.delivery_id = i.delivery_id
        LEFT JOIN payments p ON i.invoice_id = p.invoice_id
        WHERE o.order_id = :order_id
    """)
    result = db.execute(query, {"order_id": order_id}).mappings().all()
    
    if not result:
        return {"error": f"Order {order_id} not found."}

    # Structuring Output Graph Node Tree mapping explicitly
    output = {
        "order": {
            "order_id": result[0]["order_id"],
            "customer_id": result[0]["customer_id"],
            "created_at": str(result[0]["order_date"]) if result[0]["order_date"] else None
        },
        "deliveries": [],
        "invoices": [],
        "payments": []
    }
    
    seen_d = set()
    seen_i = set()
    seen_p = set()
    
    for row in result:
        did = row["delivery_id"]
        iid = row["invoice_id"]
        pid = row["payment_id"]
        
        if did and did not in seen_d:
            output["deliveries"].append({"delivery_id": did, "created_at": str(row["delivery_date"])})
            seen_d.add(did)
            
        if iid and iid not in seen_i:
            output["invoices"].append({"invoice_id": iid, "amount": float(row["invoice_amount"]) if row["invoice_amount"] else 0.0})
            seen_i.add(iid)
            
        if pid and pid not in seen_p:
            output["payments"].append({"payment_id": pid, "amount": float(row["payment_amount"]) if row["payment_amount"] else 0.0})
            seen_p.add(pid)
            
    return output

def get_entire_graph(db, limit=50) -> Dict[str, Any]:
    """
    Returns a generalized graph structure of interconnected entities for visualization.
    """
    nodes = []
    edges = []
    
    # 1. Orders and Customers
    orders = db.execute(text("SELECT order_id, customer_id FROM orders LIMIT :limit"), {"limit": limit}).mappings().fetchall()
    for o in orders:
        nodes.append({"id": o["order_id"], "label": f"Order {o['order_id']}", "group": "order"})
        if o["customer_id"]:
            nodes.append({"id": o["customer_id"], "label": f"Cust {o['customer_id']}", "group": "customer"})
            edges.append({"source": o["order_id"], "target": o["customer_id"], "type": "placed_by"})
            
    # 2. Deliveries
    deliveries = db.execute(text("SELECT delivery_id, order_id FROM deliveries LIMIT :limit"), {"limit": limit}).mappings().fetchall()
    for d in deliveries:
        nodes.append({"id": d["delivery_id"], "label": f"Delivery {d['delivery_id']}", "group": "delivery"})
        if d["order_id"]:
            edges.append({"source": d["delivery_id"], "target": d["order_id"], "type": "fulfills_order"})
            
    # 3. Invoices
    invoices = db.execute(text("SELECT invoice_id, order_id, delivery_id FROM invoices LIMIT :limit"), {"limit": limit}).mappings().fetchall()
    for i in invoices:
        nodes.append({"id": i["invoice_id"], "label": f"Invoice {i['invoice_id']}", "group": "invoice"})
        if i["order_id"]:
            edges.append({"source": i["invoice_id"], "target": i["order_id"], "type": "bills_order"})
        if i["delivery_id"]:
            edges.append({"source": i["invoice_id"], "target": i["delivery_id"], "type": "bills_delivery"})

    # 4. Payments
    payments = db.execute(text("SELECT payment_id, invoice_id FROM payments LIMIT :limit"), {"limit": limit}).mappings().fetchall()
    for p in payments:
        nodes.append({"id": p["payment_id"], "label": f"Payment {p['payment_id']}", "group": "payment"})
        if p["invoice_id"]:
            edges.append({"source": p["payment_id"], "target": p["invoice_id"], "type": "pays_invoice"})

    # 5. Order Items & Products
    order_items = db.execute(text("SELECT id, order_id, product_id FROM order_items LIMIT :limit"), {"limit": limit}).mappings().fetchall()
    for oi in order_items:
        oi_id = f"oi_{oi['id']}"
        nodes.append({"id": oi_id, "label": f"Item {oi['id']}", "group": "order_item"})
        nodes.append({"id": oi["product_id"], "label": f"Product {oi['product_id']}", "group": "product"})
        if oi["order_id"]:
            edges.append({"source": oi["order_id"], "target": oi_id, "type": "contains_item"})
        if oi["product_id"]:
            edges.append({"source": oi_id, "target": oi["product_id"], "type": "is_product"})

    unique_nodes = list({n["id"]: n for n in nodes}.values())
    return {"nodes": unique_nodes, "links": edges}
