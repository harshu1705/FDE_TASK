import sys
sys.path.append('.')
from backend.main import process_intelligent_query, QueryRequest
from backend.database import SessionLocal
from backend.llm.executor import execute_sql
import json

db = SessionLocal()
sql = """SELECT
    p.description,
    COUNT(i.invoice_id) AS total_invoices
FROM
    products AS p
LEFT JOIN
    order_items AS oi ON p.product_id = oi.product_id
LEFT JOIN
    orders AS o ON oi.order_id = o.order_id
LEFT JOIN
    deliveries AS d ON o.order_id = d.order_id
LEFT JOIN
    invoices AS i ON d.delivery_id = i.delivery_id
GROUP BY
    p.description
ORDER BY
    total_invoices DESC
LIMIT 10;"""

data, db_err, highlight_ids = execute_sql(db, sql)
with open('db_err.txt', 'w') as f:
    f.write(str(db_err))
