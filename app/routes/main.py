from flask import Blueprint, render_template, current_app, request, jsonify
import os
import sys
from app.utils.ontology_parser import extract_markdown_to_json, analyze_ontology_structure
from app.models.query_engine import CyberneticsQueryEngine

bp = Blueprint('main', __name__)

# Global variable for the query engine
query_engine = None

def load_query_engine():
    """Load the query engine with the latest data"""
    global query_engine
    data_file = os.path.join(current_app.config['DATA_FOLDER'], 'cybernetics_ontology.json')
    
    print(f"Looking for data file at: {data_file}")
    if os.path.exists(data_file):
        print(f"Data file found, loading query engine with: {data_file}")
        query_engine = CyberneticsQueryEngine(data_file)
        print(f"Query engine loaded with {query_engine.graph.number_of_nodes()} nodes and {query_engine.graph.number_of_edges()} edges")
        return True
    else:
        print(f"Data file not found at: {data_file}")
    return False

@bp.before_app_request
def load_engine_if_needed():
    """Try to load the query engine at startup"""
    global query_engine
    if query_engine is None:
        load_query_engine()

@bp.route('/')
def index():
    """Render the main page"""
    global query_engine
    return render_template('index.html', engine_loaded=query_engine is not None)

@bp.route('/upload', methods=['GET', 'POST'])
def upload_file():
    """Handle file uploads"""
    global query_engine
    
    if request.method == 'POST':
        # Check if the post request has the file part
        if 'ontology_file' not in request.files:
            return jsonify({"error": "No file part"}), 400
        
        file = request.files['ontology_file']
        
        # If user does not select file, browser also
        # submit an empty part without filename
        if file.filename == '':
            return jsonify({"error": "No selected file"}), 400
        
        if file:
            filename = secure_filename(file.filename)
            filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            # Process the file
            try:
                output_file = os.path.join(current_app.config['DATA_FOLDER'], 'cybernetics_ontology.json')
                extract_markdown_to_json(filepath, output_file)
                
                # Load the query engine with the new data
                load_query_engine()
                
                return jsonify({
                    "success": True,
                    "message": "File processed successfully",
                    "filename": filename
                })
            except Exception as e:
                return jsonify({
                    "error": f"Error processing file: {str(e)}"
                }), 500
    
    return render_template('upload.html')

@bp.route('/browse')
def browse_structure():
    """Render the browse page showing the ontology structure"""
    global query_engine
    
    if query_engine is None:
        return render_template('error.html', message="No ontology data loaded")
    
    # Get nodes grouped by category for the new graph-based structure
    categories = {}
    
    try:
        # Group nodes by category
        for node_id in query_engine.graph.nodes():
            attrs = query_engine.graph.nodes[node_id]
            node_type = attrs.get("type", "unknown")
            
            # Skip category nodes themselves
            if node_type == "category":
                continue
                
            # Use category as the grouping key, or node type if category is not available
            category = attrs.get("category", node_type)
            
            if category not in categories:
                categories[category] = {"title": category, "nodes": []}
                
            categories[category]["nodes"].append({
                "id": node_id,
                "label": attrs.get("label", node_id),
                "type": node_type
            })
        
        # Sort nodes within each category by label
        for category in categories.values():
            category["nodes"].sort(key=lambda x: x["label"])
            
        # Convert to format expected by template
        structured_data = {}
        for i, (category, data) in enumerate(categories.items(), 1):
            # Group nodes by type within each category
            nodes_by_type = {}
            for node in data["nodes"]:
                node_type = node["type"]
                if node_type not in nodes_by_type:
                    nodes_by_type[node_type] = []
                nodes_by_type[node_type].append(node["label"])
                
            structured_data[str(i)] = {
                "title": data["title"],
                "subsections": nodes_by_type
            }
            
        print(f"Generated structured data with {len(structured_data)} categories", file=sys.stderr)
        return render_template('browse.html', ontology=structured_data)
        
    except Exception as e:
        import traceback
        print(f"Error generating browse data: {str(e)}", file=sys.stderr)
        print(traceback.format_exc(), file=sys.stderr)
        return render_template('error.html', message=f"Error generating browse data: {str(e)}")

@bp.route('/concept/<concept_id>')
def view_concept(concept_id):
    """Render the concept page"""
    global query_engine
    
    if query_engine is None:
        return render_template('error.html', message="No ontology data loaded")
    
    concept_info = query_engine.query_entity(concept_id)
    
    if "error" in concept_info:
        return render_template('error.html', message=concept_info["error"])
    
    related = query_engine.get_related_concepts(concept_id)
    
    return render_template('concept.html', concept=concept_info, related=related)

@bp.route('/explore')
def explore():
    """Render the explore page with interactive visualization"""
    global query_engine
    
    if query_engine is None:
        return render_template('error.html', message="No ontology data loaded")
    
    return render_template('explore.html')

@bp.route('/ontology')
def visualize_ontology():
    """Render the ontology visualization page"""
    global query_engine
    
    if query_engine is None:
        return render_template('error.html', message="No ontology data loaded")
    
    # Prepare summary data for the template
    summary = {
        "node_count": query_engine.graph.number_of_nodes(),
        "edge_count": query_engine.graph.number_of_edges(),
        "entity_types": query_engine.get_entity_types(),
        "relationship_types": {},
        "central_entities": []
    }
    
    # Get relationship types
    for _, _, data in query_engine.graph.edges(data=True):
        rel_type = data.get("label", "unknown")
        summary["relationship_types"][rel_type] = summary["relationship_types"].get(rel_type, 0) + 1
    
    # Get central entities
    central_entities = query_engine.get_central_entities(5)  # Top 5 central entities
    summary["central_entities"] = central_entities
    
    return render_template('ontology.html', summary=summary)
