import logging
import os
from google import genai

logger = logging.getLogger(__name__)
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY", "AIzaSyAh_PSCS-3JoMnMeyyXisy8mO0nK7iBkZw"))

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
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt
        )
        return response.text.strip()
    except Exception as e:
        logger.error(f"Failed formatting response via GenAI: {e}")
        return "The executed data was successfully extracted, however the natural language processor encountered an error summarizing."
