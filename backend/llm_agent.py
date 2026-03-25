import os
import logging
from sqlalchemy import text
from google import genai
import time

logger = logging.getLogger(__name__)

# Core Gemini integration mapped to the provided dataset definitions exclusively
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY", "LOCAL_TEST"))

# Strict Zero-Hallucination SQL Framework
DATABASE_SCHEMA = """
Table: customers (customer_id TEXT PRIMARY KEY, name TEXT, city TEXT, postal_code TEXT)
Table: products (product_id TEXT PRIMARY KEY, description TEXT)
Table: orders (order_id TEXT PRIMARY KEY, customer_id TEXT REFERENCES customers(customer_id), created_at TIMESTAMP)
Table: order_items (id SERIAL PRIMARY KEY, order_id TEXT REFERENCES orders(order_id), product_id TEXT REFERENCES products(product_id), quantity INT)
Table: deliveries (delivery_id TEXT PRIMARY KEY, order_id TEXT REFERENCES orders(order_id), created_at TIMESTAMP)
Table: invoices (invoice_id TEXT PRIMARY KEY, delivery_id TEXT REFERENCES deliveries(delivery_id), order_id TEXT REFERENCES orders(order_id), total_amount NUMERIC)
Table: payments (payment_id TEXT PRIMARY KEY, invoice_id TEXT REFERENCES invoices(invoice_id), amount NUMERIC)

STRICT RULES:
1. ONLY return a valid SQL SELECT query. Do not add markdown like ```sql or any explanations.
2. ALWAYS use explicitly defined columns. Never hallucinate columns.
3. If asked for a trace or specific flow, utilize LEFT JOINs to retain edge cases.
4. Default to appending LIMIT 10 to protect system resources.
5. If the request is NOT about this ERP dataset, return exactly the string: "INVALID_QUERY_OUT_OF_DOMAIN"
"""

def generate_sql(user_query: str, error_context: str = None) -> str:
    prompt = f"{DATABASE_SCHEMA}\n\nUSER QUERY: {user_query}"
    if error_context:
        prompt += f"\n\nERROR IN PREVIOUS SQL ATTEMPT: {error_context}\nPlease correct the SQL syntactically."
    
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt
        )
        
        sql = response.text.strip()
        if sql.startswith("```sql"): sql = sql[6:]
        if sql.startswith("```"): sql = sql[3:]
        if sql.endswith("```"): sql = sql[:-3]
        return sql.strip()
    except Exception as e:
        logger.error(f"GenAI Integration failure: {e}")
        return "SELECT 'GenAI Failure' as error;"

def execute_llm_query(db, user_query: str, retries: int = 2) -> dict:
    """
    Executes conversational flow: User Query -> Text2SQL -> Execution -> Self Healing Retries
    """
    error_context = None
    start_time = time.time()
    
    logger.info(f"Received query: {user_query}")
    
    for attempt in range(retries + 1):
        # 1. SQL GENERATION Pipeline
        sql_query = generate_sql(user_query, error_context)
        
        # 2. GUARDRAILS Implementation
        if "INVALID_QUERY" in sql_query.upper():
            logger.warning(f"Out of Domain request actively blocked.")
            return {"status": "rejected", "message": "This system is designed to answer questions related to the provided dataset only."}
            
        if not sql_query.upper().startswith("SELECT"):
            error_context = "CRITICAL Guardrail Failure: You are only permitted to write SELECT queries. Rewrite your query."
            continue
            
        if "LIMIT " not in sql_query.upper():
            sql_query += "\nLIMIT 10"
            
        # 3. DATABASE EXECUTION Phase
        try:
            logger.info(f"Attempt {attempt + 1}: Executing Generated SQL: {sql_query}")
            result = db.execute(text(sql_query)).mappings().all()
            
            data = [dict(row) for row in result]
            
            # 4. OBSERVABILITY & HIGHLIGHT EXTRACTION
            highlight_nodes = []
            for row in data:
                for k, v in row.items():
                    if k.endswith("_id") and v: highlight_nodes.append(str(v))
            
            exec_time = time.time() - start_time
            logger.info(f"SUCCESS Pipeline Execute. Processing time: {exec_time:.2f}s")
            
            return {
                "status": "success",
                "execution_time_seconds": round(exec_time, 2),
                "sql": sql_query,
                "data": data,
                "highlight_nodes": list(set(highlight_nodes))  # Passed visually to Graph Layer mapping
            }
            
        except Exception as e:
            logger.error(f"SQL execution failed: {str(e)}")
            error_context = str(e)
            
    # 5. RETRY FAILURE ABORT
    logger.error("SYSTEM HALT: Max retry correction sequence exceeded.")
    return {"status": "failed", "message": "Failed to generate valid SQL within retry limits.", "last_sql": sql_query, "last_error": error_context}
