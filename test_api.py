import requests
import json
import time

URL = "http://127.0.0.1:8000/query"

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
        resp = requests.post(URL, json={"query": test["query"]})
        data = resp.json()
        print(f"ANSWER:\n{data.get('answer')}")
        
        if data.get('sql'):
            print(f"\nSQL GENERATED:\n{data.get('sql')}")
            
        print("\nMETRICS:")
        print(f"Confidence Score:{data.get('confidence', 'N/A')}")
        print(f"Rows Returned:   {data.get('rows_returned', 'N/A')}")
        print(f"Schema Version:  {data.get('schema_version', 'N/A')}")
        
        # Limit nodes printed just to keep console clean if huge array
        nodes = data.get('highlight_nodes', [])
        print(f"Highlight Nodes: {nodes[:5]}{'...' if len(nodes) > 5 else ''}")
        
    except Exception as e:
        print(f"Failed to connect or parse response: {e}")
    time.sleep(1.5)
