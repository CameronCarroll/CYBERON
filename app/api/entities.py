from flask import Blueprint, request, jsonify
import app.routes.main as main_module
from app.utils.validation import validate_entity, validate_entity_update
from app.utils.response import success_response, error_response
from app import limiter
import datetime

bp = Blueprint('entities', __name__)

@bp.route('/entities', methods=['POST'])
@limiter.limit("5 per minute")
def create_entity():
    """Create a new entity"""
    # Get the latest reference to query_engine
    query_engine = main_module.query_engine
    
    if query_engine is None:
        # Try to load it once more
        main_module.load_query_engine()
        query_engine = main_module.query_engine
        
        if query_engine is None:
            return error_response("No ontology data loaded", 404)
    
    # Get request data
    data = request.get_json()
    
    # Validate input data
    validation_error = validate_entity(data)
    if validation_error:
        return error_response(validation_error, 400)
    
    try:
        # Create entity
        entity = query_engine.create_entity(data)
        
        # Save changes to disk
        query_engine.save_changes()
        
        return success_response({"entity": entity}, 201)
    except ValueError as e:
        return error_response(str(e), 400)
    except Exception as e:
        return error_response(f"Error creating entity: {str(e)}", 500)

@bp.route('/entities/<entity_id>', methods=['GET'])
def get_entity(entity_id):
    """Get entity by ID"""
    # Get the latest reference to query_engine
    query_engine = main_module.query_engine
    
    if query_engine is None:
        # Try to load it once more
        main_module.load_query_engine()
        query_engine = main_module.query_engine
        
        if query_engine is None:
            return error_response("No ontology data loaded", 404)
    
    try:
        entity = query_engine.query_entity(entity_id)
        if "error" in entity:
            return error_response(entity["error"], 404)
        return success_response({"entity": entity})
    except Exception as e:
        return error_response(f"Error retrieving entity: {str(e)}", 500)

@bp.route('/entities/<entity_id>', methods=['PUT'])
def update_entity(entity_id):
    """Update an entity"""
    # Get the latest reference to query_engine
    query_engine = main_module.query_engine
    
    if query_engine is None:
        # Try to load it once more
        main_module.load_query_engine()
        query_engine = main_module.query_engine
        
        if query_engine is None:
            return error_response("No ontology data loaded", 404)
    
    # Get request data
    data = request.get_json()
    
    # Validate input data
    validation_error = validate_entity_update(data)
    if validation_error:
        return error_response(validation_error, 400)
    
    try:
        # Update entity
        entity = query_engine.update_entity(entity_id, data)
        if not entity:
            return error_response(f"Entity '{entity_id}' not found", 404)
        
        # Save changes to disk
        query_engine.save_changes()
        
        return success_response({"entity": entity})
    except ValueError as e:
        return error_response(str(e), 400)
    except Exception as e:
        return error_response(f"Error updating entity: {str(e)}", 500)

@bp.route('/entities/<entity_id>', methods=['DELETE'])
@limiter.limit("5 per minute")
def delete_entity(entity_id):
    """Delete an entity"""
    # Get the latest reference to query_engine
    query_engine = main_module.query_engine
    
    if query_engine is None:
        # Try to load it once more
        main_module.load_query_engine()
        query_engine = main_module.query_engine
        
        if query_engine is None:
            return error_response("No ontology data loaded", 404)
    
    # Check for cascade parameter
    cascade = request.args.get('cascade', 'false').lower() == 'true'
    
    try:
        # Delete entity
        result = query_engine.delete_entity(entity_id, cascade)
        
        if not result["success"]:
            if result.get("not_found", False):
                return error_response(f"Entity '{entity_id}' not found", 404)
            return error_response(result.get("message", "Error deleting entity"), 409)
        
        # Save changes to disk
        query_engine.save_changes()
        
        return success_response({
            "message": "Entity deleted successfully",
            "relationships_removed": result.get("relationships_removed", 0)
        })
    except Exception as e:
        return error_response(f"Error deleting entity: {str(e)}", 500)

@bp.route('/entities', methods=['GET'])
@limiter.limit("30 per minute")
def list_entities():
    """List entities with optional filtering"""
    # Get the latest reference to query_engine
    query_engine = main_module.query_engine
    
    if query_engine is None:
        # Try to load it once more
        main_module.load_query_engine()
        query_engine = main_module.query_engine
        
        if query_engine is None:
            return error_response("No ontology data loaded", 404)
    
    # Get query parameters
    entity_type = request.args.get('type')
    query = request.args.get('q')
    limit = int(request.args.get('limit', 50))
    offset = int(request.args.get('offset', 0))
    sort = request.args.get('sort', 'created_at')
    order = request.args.get('order', 'desc')
    
    try:
        # List entities
        result = query_engine.list_entities(
            entity_type=entity_type,
            query=query,
            limit=limit,
            offset=offset,
            sort=sort,
            order=order
        )
        
        return success_response({
            "entities": result["entities"],
            "pagination": {
                "total": result["total"],
                "offset": offset,
                "limit": limit,
                "next_offset": offset + limit if offset + limit < result["total"] else None
            }
        })
    except Exception as e:
        return error_response(f"Error listing entities: {str(e)}", 500)

@bp.route('/test-rate-limit', methods=['GET'])
# Force rate limiting regardless of IP by using a fixed key
@limiter.limit("3 per minute", key_func=lambda: "test_client")
def test_rate_limit():
    """A simple endpoint to test rate limiting"""
    return success_response({
        "message": "This endpoint is limited to 3 requests per minute",
        "timestamp": datetime.datetime.now().isoformat()
    })