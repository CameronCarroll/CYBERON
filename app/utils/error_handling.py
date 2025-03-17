from flask import jsonify, current_app, request
from typing import Dict, Any, Tuple, List, Optional, Union
import datetime
import traceback
import json

# Define error types as constants for consistency
class ErrorType:
    VALIDATION_ERROR = "validation_error"
    NOT_FOUND = "not_found"
    CONSTRAINT_VIOLATION = "constraint_violation"
    AUTH_ERROR = "auth_error"
    RATE_LIMIT_ERROR = "rate_limit_error"
    SERVER_ERROR = "server_error"
    DATA_ERROR = "data_error"
    INPUT_ERROR = "input_error"
    
# Error code prefixes
# 1xx: Validation errors
# 2xx: Not found errors
# 3xx: Constraint violations
# 4xx: Authentication/Authorization errors
# 5xx: Rate limiting errors
# 9xx: Server errors

ERROR_CODES = {
    # Validation errors (100-199)
    "missing_required_field": 101,
    "invalid_field_type": 102,
    "invalid_field_value": 103,
    "invalid_entity_type": 104,
    "invalid_relationship_type": 105,
    "invalid_query_parameter": 106,
    "invalid_request_format": 107,
    
    # Not found errors (200-299)
    "entity_not_found": 201,
    "relationship_not_found": 202,
    "resource_not_found": 203,
    "route_not_found": 204,
    
    # Constraint violations (300-399)
    "entity_already_exists": 301,
    "relationship_already_exists": 302,
    "has_dependent_relationships": 303,
    "circular_relationship": 304,
    "relationship_limit_exceeded": 305,
    
    # Authentication errors (400-499)
    "unauthorized": 401,
    "forbidden": 403,
    
    # Rate limiting errors (500-599)
    "rate_limit_exceeded": 501,
    
    # Server errors (900-999)
    "internal_server_error": 901,
    "database_error": 902,
    "service_unavailable": 903,
    "data_corruption": 904
}

def get_error_code(error_key: str) -> int:
    """Get the numeric error code for a given error key"""
    return ERROR_CODES.get(error_key, 999)  # Default to generic server error

def format_error_response(
    message: str,
    error_type: str,
    error_code: str,
    status_code: int = 400,
    invalid_fields: Optional[Dict[str, str]] = None,
    resource_id: Optional[str] = None,
    recovery_hint: Optional[str] = None,
    request_excerpt: Optional[Dict[str, Any]] = None,
    related_operations: Optional[List[str]] = None
) -> Tuple[Dict[str, Any], int]:
    """
    Format a detailed API error response
    
    Args:
        message: Human-readable error message
        error_type: Type of error (validation, not_found, etc.)
        error_code: Specific error code
        status_code: HTTP status code
        invalid_fields: Dict of field names to validation errors
        resource_id: ID of the related resource (entity, relationship)
        recovery_hint: Hint for how to recover from this error
        request_excerpt: Relevant portion of the request that caused the error
        related_operations: List of related API operations that might help
        
    Returns:
        Tuple of (JSON response object, HTTP status code)
    """
    # Build the error response
    error_response = {
        "success": False,
        "error": {
            "message": message,
            "type": error_type,
            "code": get_error_code(error_code),
            "code_name": error_code,
            "timestamp": datetime.datetime.now().isoformat()
        }
    }
    
    # Add optional fields if provided
    if invalid_fields:
        error_response["error"]["invalid_fields"] = invalid_fields
    
    if resource_id:
        error_response["error"]["resource_id"] = resource_id
    
    if recovery_hint:
        error_response["error"]["recovery_hint"] = recovery_hint
    
    if request_excerpt:
        error_response["error"]["request_excerpt"] = request_excerpt
    
    if related_operations:
        error_response["error"]["related_operations"] = related_operations
    
    # Add request details for debugging
    if current_app.debug:
        error_response["error"]["debug"] = {
            "method": request.method,
            "url": request.url,
            "headers": dict(request.headers),
            "data": request.get_json(silent=True) if request.is_json else None
        }
    
    return jsonify(error_response), status_code

# Convenience functions for common error types

def validation_error(
    message: str,
    error_code: str = "invalid_field_value",
    invalid_fields: Optional[Dict[str, str]] = None,
    request_excerpt: Optional[Dict[str, Any]] = None,
    recovery_hint: Optional[str] = None
) -> Tuple[Dict[str, Any], int]:
    """Convenience function for validation errors"""
    if not invalid_fields:
        invalid_fields = {}
    
    # Add allowed values to recovery hint if available
    enhanced_recovery_hint = recovery_hint
    if invalid_fields and not recovery_hint:
        field_hints = []
        for field, error in invalid_fields.items():
            field_hints.append(f"'{field}': {error}")
        enhanced_recovery_hint = "Fix the following fields: " + ", ".join(field_hints)
    
    return format_error_response(
        message=message,
        error_type=ErrorType.VALIDATION_ERROR,
        error_code=error_code,
        status_code=400,
        invalid_fields=invalid_fields,
        recovery_hint=enhanced_recovery_hint,
        request_excerpt=request_excerpt,
        related_operations=["GET /api/entity-types", "GET /api/relationship-types"]
    )

def not_found_error(
    message: str,
    resource_type: str,
    resource_id: str,
    error_code: str = "resource_not_found",
    recovery_hint: Optional[str] = None
) -> Tuple[Dict[str, Any], int]:
    """Convenience function for not found errors"""
    
    # Set specific error code based on resource type
    specific_error_code = error_code
    if resource_type == "entity" and error_code == "resource_not_found":
        specific_error_code = "entity_not_found"
    elif resource_type == "relationship" and error_code == "resource_not_found":
        specific_error_code = "relationship_not_found"
    
    # Generate recovery hint if not provided
    if not recovery_hint:
        if resource_type == "entity":
            recovery_hint = f"Check if the entity ID '{resource_id}' exists or create it with POST /api/entities"
        elif resource_type == "relationship":
            recovery_hint = f"Check if the relationship ID '{resource_id}' exists or create it with POST /api/relationships"
        else:
            recovery_hint = f"Check if the {resource_type} with ID '{resource_id}' exists"
    
    operations = []
    if resource_type == "entity":
        operations = ["GET /api/entities", "POST /api/entities"]
    elif resource_type == "relationship":
        operations = ["GET /api/relationships", "POST /api/relationships"]
    
    return format_error_response(
        message=message,
        error_type=ErrorType.NOT_FOUND,
        error_code=specific_error_code,
        status_code=404,
        resource_id=resource_id,
        recovery_hint=recovery_hint,
        related_operations=operations
    )

def constraint_error(
    message: str, 
    error_code: str = "constraint_violation",
    resource_id: Optional[str] = None,
    recovery_hint: Optional[str] = None,
    related_operations: Optional[List[str]] = None
) -> Tuple[Dict[str, Any], int]:
    """Convenience function for constraint violation errors"""
    
    return format_error_response(
        message=message,
        error_type=ErrorType.CONSTRAINT_VIOLATION,
        error_code=error_code,
        status_code=409,
        resource_id=resource_id,
        recovery_hint=recovery_hint,
        related_operations=related_operations
    )

def server_error(
    message: str,
    error_code: str = "internal_server_error",
    recovery_hint: Optional[str] = None,
) -> Tuple[Dict[str, Any], int]:
    """Convenience function for server errors"""
    
    if not recovery_hint:
        recovery_hint = "This is a server error. Please try again later or contact the API administrator."
    
    # Log the error
    current_app.logger.error(f"Server error: {message}\n{traceback.format_exc()}")
    
    return format_error_response(
        message=message,
        error_type=ErrorType.SERVER_ERROR,
        error_code=error_code,
        status_code=500,
        recovery_hint=recovery_hint
    )

def rate_limit_error(
    message: str,
    retry_after: str,
    error_code: str = "rate_limit_exceeded"
) -> Tuple[Dict[str, Any], int]:
    """Convenience function for rate limiting errors"""
    
    return format_error_response(
        message=message,
        error_type=ErrorType.RATE_LIMIT_ERROR,
        error_code=error_code,
        status_code=429,
        recovery_hint=f"Please wait {retry_after} before retrying, or reduce your request frequency.",
        related_operations=["See API documentation for rate limit guidelines"]
    )

# Register an error handler for the Flask app
def register_error_handlers(app):
    """Register error handlers for common HTTP status codes"""
    
    @app.errorhandler(400)
    def handle_bad_request(e):
        return validation_error(
            message="Bad request",
            error_code="invalid_request_format",
            recovery_hint="Check your request format and try again"
        )
    
    @app.errorhandler(404)
    def handle_not_found(e):
        return not_found_error(
            message=f"Route not found: {request.path}",
            resource_type="route",
            resource_id=request.path,
            error_code="route_not_found"
        )
    
    @app.errorhandler(405)
    def handle_method_not_allowed(e):
        return validation_error(
            message=f"Method {request.method} not allowed for {request.path}",
            error_code="invalid_request_format",
            recovery_hint=f"This endpoint does not support the {request.method} method"
        )
    
    @app.errorhandler(429)
    def handle_rate_limit(e):
        return rate_limit_error(
            message="Too many requests. Please slow down.",
            retry_after=e.description if hasattr(e, 'description') else "a while"
        )
    
    @app.errorhandler(500)
    def handle_server_error(e):
        return server_error(message=str(e) or "Internal server error")