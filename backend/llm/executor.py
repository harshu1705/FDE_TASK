import logging
from sqlalchemy import text
from typing import List, Dict, Any, Tuple

logger = logging.getLogger(__name__)

def execute_sql(db, sql_query: str) -> Tuple[List[Dict[str, Any]], str, List[str]]:
    """
    Executes validated SQL against SQLAlchemy and parses Graph UI highlight nodes.
    """
    try:
        logger.info("Engaging Postgres Engine for validated query...")
        
        result = db.execute(text(sql_query)).mappings().all()
        data = [dict(row) for row in result]
        
        # Extract Graph Visual Map Nodes dynamically from the returned dataset
        highlight_nodes = []
        for row in data:
            for key, val in row.items():
                if str(key).endswith("_id") and val:
                    highlight_nodes.append(str(val))
                    
        return data, None, list(set(highlight_nodes))
        
    except Exception as e:
        error_msg = str(e).strip()
        logger.error(f"SQL Backend Execution Integrity Failed: {error_msg}")
        try:
            db.rollback()
        except Exception:
            pass
        return None, error_msg, []
