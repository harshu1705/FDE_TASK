import logging
import os
from google import genai

logger = logging.getLogger(__name__)
api_keys = [
    os.environ.get("GEMINI_API_KEY", "AIzaSyDEmnDxb2E97FJ8c3VLv4fPMYBgFVNr-A4"),
    "AIzaSyAh_PSCS-3JoMnMeyyXisy8mO0nK7iBkZw"
]
clients = [genai.Client(api_key=k) for k in api_keys]

def format_response(sql_result: list, user_query: str) -> str:
    """
    Accepts raw DB dictionary array output and translates it into natural language strictly 
    without synthesizing or extending underlying data boundaries.
    """
    prompt = f"""
    You are an expert data analyst reporting exclusively on exact ERP metrics.
    Translate the following raw SQL dataset array result into a brief, professional natural language answer.
    
    User Query: {user_query}
    Database Result: {sql_result}
    
    STRICT RULES:
    1. Base your answer EXCLUSIVELY on the Database Result provided.
    2. Do NOT hallucinate names, quantities, or metrics that are not physically present in the result bounds.
    3. Deliver a highly concise and direct confirmation to the user.
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
            
        return response.text.strip()
    except Exception as e:
        logger.error(f"Failed formatting response via GenAI: {e}")
        return "The executed data was successfully extracted, however the natural language processor encountered an error summarizing."
