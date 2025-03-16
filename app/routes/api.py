from flask import Blueprint, jsonify, request
from app.routes.main import query_engine

bp = Blueprint('api', __name__)

@bp.route('/graph-data')
def get_graph_data():
    """API endpoint to get graph data for visualization"""
    if query_engine is None:
        return jsonify({"error": "No ontology data loaded"}), 404
    
    try:
        # Convert graph to visualization format
        nodes = []
        for node_id in query_engine.graph.nodes():
            attrs = query_engine.graph.nodes[node_id]
            nodes.append({
                "id": node_id,
                "label": attrs.get("label", node_id),
                "type": attrs.get("type", "unknown")
            })
        
        links = []
        for source, target, data in query_engine.graph.edges(data=True):
            links.append({
                "source": source,
                "target": target,
                "label": data.get("label", "")
            })
        
        # Log data for debugging
        print(f"Returning graph data with {len(nodes)} nodes and {len(links)} links")
        
        return jsonify({
            "nodes": nodes,
            "links": links
        })
    except Exception as e:
        import traceback
        print(f"Error in get_graph_data: {str(e)}")
        print(traceback.format_exc())
        return jsonify({"error": f"Error processing graph data: {str(e)}"}), 500

@bp.route('/entity/<entity_id>')
def get_entity(entity_id):
    """API endpoint to get entity details"""
    if query_engine is None:
        return jsonify({"error": "No ontology data loaded"}), 404
    
    entity_info = query_engine.query_entity(entity_id)
    return jsonify(entity_info)

@bp.route('/search')
def search():
    """API endpoint to search entities"""
    if query_engine is None:
        return jsonify({"error": "No ontology data loaded"}), 404
    
    query = request.args.get('q', '')
    entity_types = request.args.get('types', None)
    
    if entity_types:
        entity_types = entity_types.split(',')
    
    results = query_engine.search_entities(query, entity_types)
    return jsonify({"results": results})

@bp.route('/paths')
def find_paths():
    """API endpoint to find paths between entities"""
    if query_engine is None:
        return jsonify({"error": "No ontology data loaded"}), 404
    
    source = request.args.get('source', '')
    target = request.args.get('target', '')
    max_length = int(request.args.get('max_length', 3))
    
    paths = query_engine.find_paths(source, target, max_length)
    return jsonify({"paths": paths})

@bp.route('/sections/topic/<topic>')
def find_sections(topic):
    """API endpoint to find sections by topic"""
    if query_engine is None:
        return jsonify({"error": "No ontology data loaded"}), 404
    
    sections = query_engine.find_section_by_topic(topic)
    return jsonify({"sections": sections})

@bp.route('/concepts/evolution')
def get_concept_evolution():
    """API endpoint to get concept evolution chains"""
    if query_engine is None:
        return jsonify({"error": "No ontology data loaded"}), 404
    
    evolution_chains = query_engine.get_concept_evolution()
    return jsonify({"evolution_chains": evolution_chains})

@bp.route('/concepts/central')
def get_central_concepts():
    """API endpoint to get central concepts"""
    if query_engine is None:
        return jsonify({"error": "No ontology data loaded"}), 404
    
    count = int(request.args.get('count', 10))
    central_entities = query_engine.get_central_entities(count)
    return jsonify({"central_entities": central_entities})

@bp.route('/concepts/related/<concept_id>')
def get_related_concepts(concept_id):
    """API endpoint to get related concepts"""
    if query_engine is None:
        return jsonify({"error": "No ontology data loaded"}), 404
    
    relationship_types = request.args.get('types', None)
    
    if relationship_types:
        relationship_types = relationship_types.split(',')
    
    related = query_engine.get_related_concepts(concept_id, relationship_types)
    return jsonify(related)

@bp.route('/hierarchy')
def get_hierarchy():
    """API endpoint to get concept hierarchy"""
    if query_engine is None:
        return jsonify({"error": "No ontology data loaded"}), 404
    
    hierarchy = query_engine.analyze_concept_hierarchy()
    return jsonify(hierarchy)