import os
import logging
from google import genai
from .prompt import ERP_SQL_PROMPT

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

api_keys = [
    os.environ.get("GEMINI_API_KEY", "AIzaSyDEmnDxb2E97FJ8c3VLv4fPMYBgFVNr-A4"),
    "AIzaSyAh_PSCS-3JoMnMeyyXisy8mO0nK7iBkZw"
]
clients = [genai.Client(api_key=k) for k in api_keys]

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
        for current_client in clients:
            if success: break
            for model_name in ['gemini-2.5-flash', 'gemini-1.5-flash']:
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
        return f"PURE_GUARDRAIL_BLOCK Exception Log Context: {e}"

def generate_sql(user_query: str, intent_context: str, error_context: str = None) -> str:
    """
    Step 2: Execution Text-to-SQL logic bound strictly by Step 1 intent verification.
    """
    prompt = ERP_SQL_PROMPT.format(user_query=user_query, intent_context=intent_context)
    if error_context:
        prompt += f"\n\nERROR IN PREVIOUS SQL ATTEMPT: {error_context}\nPlease correct the SQL syntactically."
        
    try:
        response = None
        success = False
        for current_client in clients:
            if success: break
            for model_name in ['gemini-2.5-flash', 'gemini-1.5-flash']:
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
