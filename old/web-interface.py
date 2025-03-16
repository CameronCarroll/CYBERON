import os
import json
from flask import Flask, request, render_template, jsonify, send_from_directory
from werkzeug.utils import secure_filename

# Import our custom modules
from ontology_parser import extract_text_to_json, analyze_ontology_structure
from cybernetics_query_engine import CyberneticsQueryEngine

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['DATA_FOLDER'] = 'data'

# Make sure data directories exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['DATA_FOLDER'], exist_ok=True)

# Global variable for the query engine
query_engine = None

def load_query_engine():
    """Load the query engine with the latest data"""
    global query_engine
    data_file = os.path.join(app.config['DATA_FOLDER'], 'cybernetics_ontology.json')
    
    if os.path.exists(data_file):
        query_engine = CyberneticsQueryEngine(data_file)
        return True
    return False

# Try to load the query engine at startup
load_query_engine()

@app.route('/')
def index():
    """Render the main page"""
    return render_template('index.html', engine_loaded=query_engine is not None)

@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    """Handle file uploads"""
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
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            # Process the file
            try:
                output_file = os.path.join(app.config['DATA_FOLDER'], 'cybernetics_ontology.json')
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

@app.route('/ontology')
def view_ontology():
    """Render the ontology visualization page"""
    if query_engine is None:
        return render_template('error.html', message="No ontology data loaded")
    
    summary = query_engine.generate_ontology_summary()
    return render_template('ontology.html', summary=summary)

@app.route('/api/graph-data')
def get_graph_data():
    """API endpoint to get graph data for visualization"""
    if query_engine is None:
        return jsonify({"error": "No ontology data loaded"}), 404
    
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
    
    return jsonify({
        "nodes": nodes,
        "links": links
    })

@app.route('/api/entity/<entity_id>')
def get_entity(entity_id):
    """API endpoint to get entity details"""
    if query_engine is None:
        return jsonify({"error": "No ontology data loaded"}), 404
    
    entity_info = query_engine.query_entity(entity_id)
    return jsonify(entity_info)

@app.route('/api/search')
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

@app.route('/api/paths')
def find_paths():
    """API endpoint to find paths between entities"""
    if query_engine is None:
        return jsonify({"error": "No ontology data loaded"}), 404
    
    source = request.args.get('source', '')
    target = request.args.get('target', '')
    max_length = int(request.args.get('max_length', 3))
    
    paths = query_engine.find_paths(source, target, max_length)
    return jsonify({"paths": paths})

@app.route('/api/sections/topic/<topic>')
def find_sections(topic):
    """API endpoint to find sections by topic"""
    if query_engine is None:
        return jsonify({"error": "No ontology data loaded"}), 404
    
    sections = query_engine.find_section_by_topic(topic)
    return jsonify({"sections": sections})

@app.route('/api/concepts/evolution')
def get_concept_evolution():
    """API endpoint to get concept evolution chains"""
    if query_engine is None:
        return jsonify({"error": "No ontology data loaded"}), 404
    
    evolution_chains = query_engine.get_concept_evolution()
    return jsonify({"evolution_chains": evolution_chains})

@app.route('/api/concepts/central')
def get_central_concepts():
    """API endpoint to get central concepts"""
    if query_engine is None:
        return jsonify({"error": "No ontology data loaded"}), 404
    
    count = int(request.args.get('count', 10))
    central_entities = query_engine.get_central_entities(count)
    return jsonify({"central_entities": central_entities})

@app.route('/api/concepts/related/<concept_id>')
def get_related_concepts(concept_id):
    """API endpoint to get related concepts"""
    if query_engine is None:
        return jsonify({"error": "No ontology data loaded"}), 404
    
    relationship_types = request.args.get('types', None)
    
    if relationship_types:
        relationship_types = relationship_types.split(',')
    
    related = query_engine.get_related_concepts(concept_id, relationship_types)
    return jsonify(related)

@app.route('/explore')
def explore():
    """Render the explore page"""
    if query_engine is None:
        return render_template('error.html', message="No ontology data loaded")
    
    return render_template('explore.html')

@app.route('/concept/<concept_id>')
def view_concept(concept_id):
    """Render the concept page"""
    if query_engine is None:
        return render_template('error.html', message="No ontology data loaded")
    
    concept_info = query_engine.query_entity(concept_id)
    
    if "error" in concept_info:
        return render_template('error.html', message=concept_info["error"])
    
    related = query_engine.get_related_concepts(concept_id)
    return render_template('concept.html', concept=concept_info, related=related)

@app.route('/browse')
def browse_structure():
    """Render the browse page showing the ontology structure"""
    if query_engine is None:
        return render_template('error.html', message="No ontology data loaded")
    
    # Get the structured ontology
    structured = query_engine.structured_ontology
    return render_template('browse.html', ontology=structured)

@app.route('/api/hierarchy')
def get_hierarchy():
    """API endpoint to get concept hierarchy"""
    if query_engine is None:
        return jsonify({"error": "No ontology data loaded"}), 404
    
    hierarchy = query_engine.analyze_concept_hierarchy()
    return jsonify(hierarchy)

# Templates and static files
@app.route('/templates/<path:path>')
def send_template(path):
    return send_from_directory('templates', path)

@app.route('/static/<path:path>')
def send_static(path):
    return send_from_directory('static', path)

# Sample templates for frontend
@app.route('/templates')
def list_templates():
    """Show available templates for the frontend"""
    templates = [
        {"name": "index.html", "description": "Main page"},
        {"name": "upload.html", "description": "Upload page"},
        {"name": "ontology.html", "description": "Ontology visualization"},
        {"name": "explore.html", "description": "Exploration interface"},
        {"name": "concept.html", "description": "Concept detail page"},
        {"name": "browse.html", "description": "Browse ontology structure"},
        {"name": "error.html", "description": "Error page"}
    ]
    return jsonify({"templates": templates})

if __name__ == '__main__':
    app.run(debug=True)
