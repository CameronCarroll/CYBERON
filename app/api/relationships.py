from flask import Blueprint, request, jsonify
import app.routes.main as main_module
from app.utils.validation import validate_relationship, validate_relationship_update
from app.utils.response import success_response, error_response

bp = Blueprint('relationships', __name__)

@bp.route('/relationships', methods=['POST'])
def create_relationship():
    """Create a new relationship between entities"""
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
    validation_error = validate_relationship(data)
    if validation_error:
        return error_response(validation_error, 400)
    
    try:
        # Check if source and target entities exist
        source_entity = query_engine.query_entity(data['source_id'])
        if "error" in source_entity:
            return error_response(f"Source entity '{data['source_id']}' not found", 404)
        
        target_entity = query_engine.query_entity(data['target_id'])
        if "error" in target_entity:
            return error_response(f"Target entity '{data['target_id']}' not found", 404)
        
        # Create relationship
        relationship = query_engine.create_relationship(data)
        
        # Save changes to disk
        query_engine.save_changes()
        
        return success_response({"relationship": relationship}, 201)
    except ValueError as e:
        return error_response(str(e), 400)
    except Exception as e:
        return error_response(f"Error creating relationship: {str(e)}", 500)

@bp.route('/relationships/<relationship_id>', methods=['GET'])
def get_relationship(relationship_id):
    """Get relationship by ID"""
    # Get the latest reference to query_engine
    query_engine = main_module.query_engine
    
    if query_engine is None:
        # Try to load it once more
        main_module.load_query_engine()
        query_engine = main_module.query_engine
        
        if query_engine is None:
            return error_response("No ontology data loaded", 404)
    
    try:
        # Get relationship
        relationship = query_engine.get_relationship(relationship_id)
        
        if not relationship:
            return error_response(f"Relationship '{relationship_id}' not found", 404)
        
        return success_response({"relationship": relationship})
    except Exception as e:
        return error_response(f"Error retrieving relationship: {str(e)}", 500)

@bp.route('/relationships/<relationship_id>', methods=['PUT'])
def update_relationship(relationship_id):
    """Update a relationship"""
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
    validation_error = validate_relationship_update(data)
    if validation_error:
        return error_response(validation_error, 400)
    
    try:
        # Update relationship
        relationship = query_engine.update_relationship(relationship_id, data)
        
        if not relationship:
            return error_response(f"Relationship '{relationship_id}' not found", 404)
        
        # Save changes to disk
        query_engine.save_changes()
        
        return success_response({"relationship": relationship})
    except ValueError as e:
        return error_response(str(e), 400)
    except Exception as e:
        return error_response(f"Error updating relationship: {str(e)}", 500)

@bp.route('/relationships/<relationship_id>', methods=['DELETE'])
def delete_relationship(relationship_id):
    """Delete a relationship"""
    # Get the latest reference to query_engine
    query_engine = main_module.query_engine
    
    if query_engine is None:
        # Try to load it once more
        main_module.load_query_engine()
        query_engine = main_module.query_engine
        
        if query_engine is None:
            return error_response("No ontology data loaded", 404)
    
    try:
        # Delete relationship
        success = query_engine.delete_relationship(relationship_id)
        
        if not success:
            return error_response(f"Relationship '{relationship_id}' not found", 404)
        
        # Save changes to disk
        query_engine.save_changes()
        
        return success_response({"message": "Relationship deleted successfully"})
    except Exception as e:
        return error_response(f"Error deleting relationship: {str(e)}", 500)

@bp.route('/relationships', methods=['GET'])
def list_relationships():
    """List relationships with optional filtering"""
    # Get the latest reference to query_engine
    query_engine = main_module.query_engine
    
    if query_engine is None:
        # Try to load it once more
        main_module.load_query_engine()
        query_engine = main_module.query_engine
        
        if query_engine is None:
            return error_response("No ontology data loaded", 404)
    
    # Get query parameters
    source_id = request.args.get('source_id')
    target_id = request.args.get('target_id')
    entity_id = request.args.get('entity_id')
    rel_type = request.args.get('type')
    limit = int(request.args.get('limit', 50))
    offset = int(request.args.get('offset', 0))
    sort = request.args.get('sort', 'created_at')
    order = request.args.get('order', 'desc')
    
    try:
        # List relationships
        result = query_engine.list_relationships(
            source_id=source_id,
            target_id=target_id,
            entity_id=entity_id,
            relationship_type=rel_type,
            limit=limit,
            offset=offset,
            sort=sort,
            order=order
        )
        
        return success_response({
            "relationships": result["relationships"],
            "pagination": {
                "total": result["total"],
                "offset": offset,
                "limit": limit,
                "next_offset": offset + limit if offset + limit < result["total"] else None
            }
        })
    except Exception as e:
        return error_response(f"Error listing relationships: {str(e)}", 500)