from flask import Blueprint, request, jsonify
import app.routes.main as main_module
from app.utils.response import success_response, error_response
from app import limiter

bp = Blueprint('graph', __name__)

@bp.route('/paths', methods=['GET'])
@limiter.limit("20 per minute")
def find_paths():
    """Find paths between entities"""
    # Get the latest reference to query_engine
    query_engine = main_module.query_engine
    
    if query_engine is None:
        # Try to load it once more
        main_module.load_query_engine()
        query_engine = main_module.query_engine
        
        if query_engine is None:
            return error_response("No ontology data loaded", 404)
    
    # Get required parameters
    source_id = request.args.get('source_id')
    target_id = request.args.get('target_id')
    
    if not source_id or not target_id:
        return error_response("Source and target entity IDs are required", 400)
    
    # Get optional parameters
    max_length = int(request.args.get('max_length', 3))
    relationship_types = request.args.get('relationship_types')
    
    if relationship_types:
        relationship_types = relationship_types.split(',')
    
    try:
        # Check if source and target entities exist
        source_entity = query_engine.query_entity(source_id)
        if "error" in source_entity:
            return error_response(f"Source entity '{source_id}' not found", 404)
        
        target_entity = query_engine.query_entity(target_id)
        if "error" in target_entity:
            return error_response(f"Target entity '{target_id}' not found", 404)
        
        # Find paths
        paths = query_engine.find_paths(source_id, target_id, max_length)
        return success_response({"paths": paths})
    except Exception as e:
        return error_response(f"Error finding paths: {str(e)}", 500)

@bp.route('/related/<entity_id>', methods=['GET'])
def get_related(entity_id):
    """Get entities related to the specified entity"""
    # Get the latest reference to query_engine
    query_engine = main_module.query_engine
    
    if query_engine is None:
        # Try to load it once more
        main_module.load_query_engine()
        query_engine = main_module.query_engine
        
        if query_engine is None:
            return error_response("No ontology data loaded", 404)
    
    # Get optional parameters
    relationship_types = request.args.get('relationship_types')
    direction = request.args.get('direction', 'both')
    depth = int(request.args.get('depth', 1))
    
    if relationship_types:
        relationship_types = relationship_types.split(',')
    
    try:
        # Check if entity exists
        entity = query_engine.query_entity(entity_id)
        if "error" in entity:
            return error_response(f"Entity '{entity_id}' not found", 404)
        
        # Get related entities
        related = query_engine.get_related_concepts(entity_id, relationship_types)
        
        return success_response({
            "entity": {
                "id": entity_id,
                "label": entity["attributes"]["label"],
                "type": entity["attributes"]["type"]
            },
            "related": related
        })
    except Exception as e:
        return error_response(f"Error getting related entities: {str(e)}", 500)

@bp.route('/central', methods=['GET'])
def get_central_entities():
    """Get central entities in the graph"""
    # Get the latest reference to query_engine
    query_engine = main_module.query_engine
    
    if query_engine is None:
        # Try to load it once more
        main_module.load_query_engine()
        query_engine = main_module.query_engine
        
        if query_engine is None:
            return error_response("No ontology data loaded", 404)
    
    # Get optional parameters
    count = int(request.args.get('count', 10))
    entity_type = request.args.get('type')
    
    try:
        entities = query_engine.get_central_entities(count)
        
        # Filter by type if specified
        if entity_type:
            entities = [e for e in entities if e.get('type') == entity_type]
        
        return success_response({"entities": entities})
    except Exception as e:
        return error_response(f"Error getting central entities: {str(e)}", 500)

@bp.route('/entity-types', methods=['GET'])
def get_entity_types():
    """Get list of entity types in the graph"""
    # Get the latest reference to query_engine
    query_engine = main_module.query_engine
    
    if query_engine is None:
        # Try to load it once more
        main_module.load_query_engine()
        query_engine = main_module.query_engine
        
        if query_engine is None:
            return error_response("No ontology data loaded", 404)
    
    try:
        type_counts = query_engine.get_entity_types()
        return success_response({"types": type_counts})
    except Exception as e:
        return error_response(f"Error getting entity types: {str(e)}", 500)

@bp.route('/relationship-types', methods=['GET'])
def get_relationship_types():
    """Get list of relationship types in the graph"""
    # Get the latest reference to query_engine
    query_engine = main_module.query_engine
    
    if query_engine is None:
        # Try to load it once more
        main_module.load_query_engine()
        query_engine = main_module.query_engine
        
        if query_engine is None:
            return error_response("No ontology data loaded", 404)
    
    try:
        type_counts = query_engine.get_relationship_types()
        return success_response({"types": type_counts})
    except Exception as e:
        return error_response(f"Error getting relationship types: {str(e)}", 500)

@bp.route('/stats', methods=['GET'])
@limiter.limit("10 per minute")
def get_graph_stats():
    """Get statistics about the graph"""
    # Get the latest reference to query_engine
    query_engine = main_module.query_engine
    
    if query_engine is None:
        # Try to load it once more
        main_module.load_query_engine()
        query_engine = main_module.query_engine
        
        if query_engine is None:
            return error_response("No ontology data loaded", 404)
    
    try:
        summary = query_engine.generate_ontology_summary()
        return success_response({"stats": summary})
    except Exception as e:
        return error_response(f"Error getting graph statistics: {str(e)}", 500)