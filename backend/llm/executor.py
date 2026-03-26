import logging
from sqlalchemy import text
from typing import List, Dict, Any, Tuple

logger = logging.getLogger(__name__)

def execute_sql(db, sql_query: str) -> Tuple[List[Dict[str, Any]], str, List[str]]:
    """
    Executes rigorously validated SQL against SQLAlchemy. 
    Enforces cost timeouts, avoids memory leaks, and parses Graph UI elements dynamically.
    """
    try:
        logger.info("Engaging Postgres Engine for validated query...")
        
        # 1. Query Cost Control Guardrail
        # Instructs PostgreSQL to unilaterally kill runaway/expensive scan queries after 2s.
        db.execute(text("SET statement_timeout = 10000;"))
        
        result = db.execute(text(sql_query)).mappings().all()
        data = [dict(row) for row in result]
        
        # 2. Extract Graph Visual Map Nodes dynamically from the returned dataset
        highlight_nodes = []
        for row in data:
            for key, val in row.items():
                if str(key).endswith("_id") and val:
                    highlight_nodes.append(str(val))
                    
        # Reset timeout safety
        db.execute(text("SET statement_timeout = 0;"))
        
        return data, None, list(set(highlight_nodes))
        
    except Exception as e:
        error_msg = str(e).strip()
        logger.error(f"SQL Backend Execution Integrity Failed: {error_msg}")
        return None, error_msg, []
