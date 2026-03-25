import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

def extract_string(record: Dict[str, Any], keys: list) -> Optional[str]:
    """Helper feature to extract and strip string values by checking multiple possible ERP payload keys."""
    for key in keys:
        val = record.get(key)
        if val is not None and str(val).strip():
            return str(val).strip()
    return None

def transform_record(record: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    """
    Accepts a raw JSON record and safely extracts exactly mapped ERP entities.
    Resolves empty values, enforces strict mapping, and safely type-normalizes fields.
    """
    
    # EXACT MAPPING EXTRACTIONS as dictated
    sales_order = extract_string(record, ["salesOrder", "SalesOrder"])
    delivery_doc = extract_string(record, ["deliveryDocument", "DeliveryDocument"])
    billing_doc = extract_string(record, ["billingDocument", "BillingDocument"])
    accounting_doc = extract_string(record, ["accountingDocument", "AccountingDocument"])
    material = extract_string(record, ["material", "Material"])
    sold_to_party = extract_string(record, ["soldToParty", "SoldToParty", "customer"])

    ref_sd = extract_string(record, ["referenceSdDocument", "ReferenceSDDocument"])
    if ref_sd:
        if ref_sd.startswith("7"): sales_order = sales_order or ref_sd
        elif ref_sd.startswith("8"): delivery_doc = delivery_doc or ref_sd
        elif ref_sd.startswith("9"): billing_doc = billing_doc or ref_sd

    ref_doc = extract_string(record, ["referenceDocument", "ReferenceDocument"])
    if ref_doc:
        if ref_doc.startswith("7"): sales_order = sales_order or ref_doc
        elif ref_doc.startswith("8"): delivery_doc = delivery_doc or ref_doc
        elif ref_doc.startswith("9"): billing_doc = billing_doc or ref_doc

    # Output structure corresponding to PostgreSQL Schema
    output = {
        "customer": None,
        "product": None,
        "order": None,
        "order_item": None,
        "delivery": None,
        "invoice": None,
        "payment": None
    }

    # 1. Customer
    if sold_to_party:
        output["customer"] = {
            "customer_id": sold_to_party,
            "name": extract_string(record, ["customerName", "name"]) or f"Customer {sold_to_party}",
            "city": extract_string(record, ["city", "CustomerCity"]),
            "postal_code": extract_string(record, ["postalCode", "PostalCode"])
        }

    # 2. Product
    if material:
        output["product"] = {
            "product_id": material,
            "description": extract_string(record, ["materialDescription", "description"]) or f"Product {material}"
        }

    # 3. Order
    if sales_order:
        output["order"] = {
            "order_id": sales_order,
            "customer_id": sold_to_party, # Will be Null if missing (must handle gracefully)
            "created_at": extract_string(record, ["orderDate", "creationDate", "created_at"])
        }
        
    # 4. Order Item 
    if sales_order and material:
        qty_str = extract_string(record, ["quantity", "OrderQuantity"])
        qty = 1 # Type normalization / Default assignment
        if qty_str and qty_str.isdigit():
            qty = int(qty_str)
            
        output["order_item"] = {
            "order_id": sales_order,
            "product_id": material,
            "quantity": qty
        }

    # 5. Delivery
    if delivery_doc and sales_order:
        # Based on defined schema: delivery_id, order_id, created_at
        output["delivery"] = {
            "delivery_id": delivery_doc,
            "order_id": sales_order,
            "created_at": extract_string(record, ["deliveryDate", "created_at"])
        }

    # 6. Invoice
    if billing_doc and delivery_doc and sales_order:
        # Schema logic constraints: Requires link to both delivery and order
        amt_str = extract_string(record, ["netValue", "totalAmount", "amount"])
        amt = 0.0 # Type Normalization
        if amt_str:
            try:
                amt = float(amt_str)
            except ValueError:
                pass
                
        output["invoice"] = {
            "invoice_id": billing_doc,
            "delivery_id": delivery_doc,
            "order_id": sales_order,
            "total_amount": amt
        }

    # 7. Payment
    if accounting_doc and billing_doc:
        amt_str = extract_string(record, ["paymentAmount", "amount", "netValue"])
        amt = 0.0
        if amt_str:
            try:
                amt = float(amt_str)
            except ValueError:
                pass
                
        output["payment"] = {
            "payment_id": accounting_doc,
            "invoice_id": billing_doc,
            "amount": amt
        }

    return output
