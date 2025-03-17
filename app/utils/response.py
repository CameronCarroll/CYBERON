from flask import jsonify
from typing import Dict, Any, Tuple

def success_response(data: Dict[str, Any], status_code: int = 200) -> Tuple[Any, int]:
    """
    Format a successful response
    
    Args:
        data: Dictionary with response data
        status_code: HTTP status code
        
    Returns:
        JSON response with success field and status code
    """
    response = {
        "success": True,
        **data
    }
    return jsonify(response), status_code

def error_response(message: str, status_code: int = 400) -> Tuple[Any, int]:
    """
    Format an error response
    
    Args:
        message: Error message
        status_code: HTTP status code
        
    Returns:
        JSON response with error field and status code
    """
    response = {
        "success": False,
        "error": message
    }
    return jsonify(response), status_code

def get_rate_limit_for_endpoint(endpoint_type: str) -> str:
    """
    Get the appropriate rate limit for a given endpoint type
    
    Args:
        endpoint_type: Type of endpoint (create, read, delete, etc.)
        
    Returns:
        Rate limit string
    """
    limits = {
        # Write operations are more restricted
        "create": "5 per minute",
        "update": "5 per minute", 
        "delete": "5 per minute",
        
        # Read operations have higher limits
        "list": "30 per minute",
        "read": "30 per minute",
        "search": "30 per minute",
        
        # Graph operations have moderate limits
        "graph": "20 per minute",
        "paths": "20 per minute",
        "related": "20 per minute",
        
        # Stats operations have lower limits due to computation
        "stats": "10 per minute",
        
        # Default fallback
        "default": "10 per minute"
    }
    
    return limits.get(endpoint_type.lower(), limits["default"])