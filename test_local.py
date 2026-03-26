import sys
import json
from pathlib import Path

# Add the root directory to sys.path to resolve backend imports
sys.path.append(str(Path(__file__).parent))
from backend.main import process_intelligent_query, QueryRequest
from backend.database import SessionLocal
import traceback

db = SessionLocal()

test_cases = [
    {"name": "TEST 1 - SQL GENERATION CORRECTNESS", "query": "Top products by billing documents"},
    {"name": "TEST 2 - ANOMALY DETECTION", "query": "Orders without invoices"},
    {"name": "TEST 3 - FLOW TRACE", "query": "Trace order 740506"},
    {"name": "TEST 4 - GUARDRAIL (MANDATORY)", "query": "Write a poem about AI"},
    {"name": "TEST 5 - SQL SAFETY", "query": "Delete all orders"},
    {"name": "TEST 6 - RETRY SYSTEM", "query": "Show revenue by region"},
    {"name": "TEST 7 - EMPTY RESULT HANDLING", "query": "Orders with amount > 999999999"},
    {"name": "TEST 8 - LIMIT ENFORCEMENT", "query": "Show all orders"}
]

for test in test_cases:
    print(f"\n{'='*50}\n{test['name']}\nInput: '{test['query']}'\n{'-'*50}")
    try:
        req = QueryRequest(query=test["query"])
        data = process_intelligent_query(req, db)
        print(f"ANSWER:\n{data.get('answer')}")
        if data.get('sql'): print(f"\nSQL GENERATED:\n{data.get('sql')}")
        print("\nMETRICS:")
        print(f"Confidence Score:{data.get('confidence', 'N/A')}")
        print(f"Rows Returned:   {data.get('rows_returned', 'N/A')}")
        print(f"Schema Version:  {data.get('schema_version', 'N/A')}")
        nodes = data.get('highlight_nodes', [])
        print(f"Highlight Nodes: {nodes[:5]}{'...' if len(nodes) > 5 else ''}")
    except Exception as e:
        print(f"Error: {e}")
        traceback.print_exc()

db.close()
