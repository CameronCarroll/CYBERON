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