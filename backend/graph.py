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
