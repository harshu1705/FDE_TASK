import sys
sys.path.append('.')
from backend.main import process_intelligent_query, QueryRequest
from backend.database import SessionLocal
import json

db = SessionLocal()
data = process_intelligent_query(QueryRequest(query='Top products by billing documents'), db)
with open('debug_output.json', 'w') as f:
    json.dump(data, f, indent=4)
print("SUCCESS - saved to debug_output.json")
