import sys
from sqlalchemy import text
from database import engine

def main():
    try:
        with open("output_schema.txt", "w") as f:
            with engine.connect() as conn:
                for table in ['products', 'orders', 'order_items', 'invoices']:
                    schema = conn.execute(text(f"SELECT column_name, data_type FROM information_schema.columns WHERE table_name = '{table}'")).fetchall()
                    f.write(f'\nTable {table}:\n')
                    for row in schema:
                        f.write(f'{row}\n')
                    count = conn.execute(text(f"SELECT count(*) FROM {table}")).scalar()
                    f.write(f'Count: {count}\n')
                
                # test the query directly
                query = """
                SELECT
                  p.product_id,
                  p.description,
                  COUNT(DISTINCT i.invoice_id) AS total_billing_documents
                FROM
                  products AS p
                LEFT JOIN
                  order_items AS oi
                  ON p.product_id = oi.product_id
                LEFT JOIN
                  orders AS o
                  ON oi.order_id = o.order_id
                LEFT JOIN
                  invoices AS i
                  ON o.order_id = i.order_id
                GROUP BY
                  p.product_id,
                  p.description
                ORDER BY
                  total_billing_documents DESC
                LIMIT 10
                """
                f.write("\nExecuting query:\n")
                result = conn.execute(text(query)).fetchall()
                for r in result:
                    f.write(f'{r}\n')
    except Exception as e:
        with open("output_schema.txt", "w") as f:
            f.write(f"Error: {e}")

if __name__ == '__main__':
    main()
