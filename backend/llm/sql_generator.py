import os
import logging
from google import genai
from .prompt import ERP_SQL_PROMPT

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY", "AIzaSyAh_PSCS-3JoMnMeyyXisy8mO0nK7iBkZw"))

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
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt
        )
        result = response.text.strip()
        logger.info(f"Step 1 Dynamic NLP Intent: {result}")
        return result
    except Exception as e:
        logger.error(f"GenAI Intent Failure Tracker: {e}")
        return f"PURE_GUARDRAIL_BLOCK Exception Log Context: {e}"

def generate_sql(user_query: str, intent_context: str, error_context: str = None) -> str:
    """
    Step 2: Execution Text-to-SQL logic bound strictly by Step 1 intent verification.
    """
    prompt = ERP_SQL_PROMPT.format(user_query=user_query, intent_context=intent_context)
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
        
        sql = sql.strip()
        logger.info(f"Step 2 Validated SQL String:\n{sql}")
        return sql
    except Exception as e:
        logger.error(f"Failed generating SQL from Synthetic AI: {e}")
        return ""
