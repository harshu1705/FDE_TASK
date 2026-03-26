import os
from google import genai

client = genai.Client(api_key="AIzaSyAh_PSCS-3JoMnMeyyXisy8mO0nK7iBkZw")
try:
    response = client.models.generate_content(model='gemini-2.5-flash', contents='Say hello')
    print("SUCCESS:", response.text)
except Exception as e:
    print("FAILURE:", e)
