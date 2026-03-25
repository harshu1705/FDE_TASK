def validate_sql(sql: str) -> bool:
    """
    Validates that a generated SQL string adheres to strict read-only execution constraints.
    Raises ValueError with precise context if validation fails, enabling the Self-Healing Retry engine.
    """
    query = sql.upper().strip()
    
    if not query.startswith("SELECT") and not query.startswith("WITH"):
        raise ValueError("SQL Governance Violation: Query must exclusively start with SELECT or WITH.")
        
    forbidden_keywords = ["DELETE", "UPDATE", "DROP", "INSERT", "ALTER", "TRUNCATE", "GRANT", "REVOKE"]
    for keyword in forbidden_keywords:
        # Check globally for destructive keyword boundaries 
        if f" {keyword} " in f" {query} " or query.startswith(f"{keyword} "):
            raise ValueError(f"SQL Governance Violation: Destructive operation keyword '{keyword}' actively intercepted and blocked.")
            
    if "LIMIT " not in query:
        raise ValueError("SQL Governance Violation: Query must include a LIMIT clause to prevent systemic table scans.")
        
    return True
