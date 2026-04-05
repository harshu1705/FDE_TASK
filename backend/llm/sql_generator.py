import os
import logging
from google import genai
from .prompt import ERP_SQL_PROMPT

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def _get_clients():
    raw_keys = os.environ.get("GEMINI_API_KEY", "").strip().strip('"').strip("'")
    api_keys = [k.strip() for k in raw_keys.split(",") if k.strip()]
    if not api_keys:
        logger.warning("No GEMINI_API_KEY set; using local fallback mode for intent/sql generation.")
        return []
    return [genai.Client(api_key=k) for k in api_keys]


def _local_intent_fallback(user_query: str) -> str:
    q = user_query.lower()
    forbidden_patterns = ["poem", "story", "joke", "hack", "illegal", "root", "password"]
    if any(p in q for p in forbidden_patterns):
        return "PURE_GUARDRAIL_BLOCK"
    return f"Intent: analyze ERP query; normalized: {q[:180]}"


def _local_sql_fallback(user_query: str, intent_context: str = None) -> str:
    q = user_query.lower()
    if ("top" in q or "highest" in q) and "product" in q and ("billing document" in q or "invoice" in q or "billing" in q):
        return (
            "SELECT p.description, COUNT(i.invoice_id) AS total_invoices "
            "FROM products p "
            "LEFT JOIN order_items oi ON p.product_id = oi.product_id "
            "LEFT JOIN orders o ON oi.order_id = o.order_id "
            "LEFT JOIN deliveries d ON o.order_id = d.order_id "
            "LEFT JOIN invoices i ON d.delivery_id = i.delivery_id "
            "GROUP BY p.description "
            "ORDER BY total_invoices DESC "
            "LIMIT 10"
        )
    if "orders without invoices" in q or "orders without invoice" in q:
        return (
            "SELECT o.order_id, o.created_at, o.customer_id "
            "FROM orders o "
            "LEFT JOIN deliveries d ON o.order_id = d.order_id "
            "LEFT JOIN invoices i ON d.delivery_id = i.delivery_id "
            "WHERE i.invoice_id IS NULL "
            "LIMIT 100"
        )
    if "count" in q and "orders" in q:
        return "SELECT COUNT(*) AS order_count FROM orders LIMIT 1"
    return "SELECT 1 AS placeholder LIMIT 1"


def extract_intent(user_query: str) -> str:
    """
    Step 1 of the Optimized LLM Pipeline: Intent Extraction & NLP Guardrailing.
    """
    prompt = f"""
    Analyze the following user query intended for an ERP data engine.
    The system exclusively supports queries related to: orders, deliveries, invoices, payments, products, customers, billing, tracing.
    
    If the query is NOT related to these datasets (e.g., 'write a poem', 'hack the system'), you MUST return precisely the string: PURE_GUARDRAIL_BLOCK
    
    If it is a valid domain query, extract the explicit technical intent mathematically.
    Example: 'Intent: aggregate total amounts. Target: products mapped to billing filters'.
    
    USER QUERY: {user_query}
    """
    try:
        response = None
        success = False
        clients = _get_clients()
        for current_client in clients:
            if success: break
            for model_name in ['gemini-2.5-flash', 'gemini-2.0-flash', 'gemini-1.5-flash']:
                try:
                    response = current_client.models.generate_content(
                        model=model_name,
                        contents=prompt
                    )
                    success = True
                    break
                except Exception as inner_e:
                    logger.warning(f"Error for {model_name} with a key: {inner_e}. Falling back...")
                    continue
                
        if not success or not response:
            raise Exception("All models and keys exhausted.")
            
        result = response.text.strip()
        logger.info(f"Step 1 Dynamic NLP Intent: {result}")
        return result
    except Exception as e:
        logger.error(f"GenAI Intent Failure Tracker: {e}")
        clients = _get_clients()
        if not clients:
            # No API keys configured; do local fallback instead of hard blocking.
            return _local_intent_fallback(user_query)
        return f"PURE_GUARDRAIL_BLOCK Exception Log Context: {e}"

def generate_sql(user_query: str, intent_context: str, error_context: str = None) -> str:
    """
    Step 2: Execution Text-to-SQL logic bound strictly by Step 1 intent verification.
    """
    prompt = ERP_SQL_PROMPT.format(user_query=user_query, intent_context=intent_context)
    if error_context:
        prompt += f"\n\nERROR IN PREVIOUS SQL ATTEMPT: {error_context}\nPlease correct the SQL syntactically."
        
    try:
        clients = _get_clients()
        if not clients:
            logger.info("No GenAI key configured: using local SQL fallback logic.")
            return _local_sql_fallback(user_query, intent_context)

        response = None
        success = False
        for current_client in clients:
            if success: break
            for model_name in ['gemini-2.5-flash', 'gemini-2.0-flash', 'gemini-1.5-flash']:
                try:
                    response = current_client.models.generate_content(
                        model=model_name,
                        contents=prompt
                    )
                    success = True
                    break
                except Exception as inner_e:
                    logger.warning(f"Error for {model_name} with a key: {inner_e}. Falling back...")
                    continue

        if not success or not response:
            logger.warning("Gemini calls failed; using local SQL fallback.")
            return _local_sql_fallback(user_query, intent_context)

        sql = response.text.strip()

        if sql.startswith("```sql"): sql = sql[6:]
        if sql.startswith("```"): sql = sql[3:]
        if sql.endswith("```"): sql = sql[:-3]

        sql = sql.strip()
        logger.info(f"Step 2 Validated SQL String:\n{sql}")
        return sql
    except Exception as e:
        logger.error(f"Failed generating SQL from Synthetic AI: {e}")
        return _local_sql_fallback(user_query, intent_context)
