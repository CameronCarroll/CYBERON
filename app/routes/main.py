import os
from flask import Blueprint, render_template, current_app, request, jsonify
from werkzeug.utils import secure_filename
from app.utils.ontology_parser import extract_text_to_json, analyze_ontology_structure
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
                extract_text_to_json(filepath, output_file)
                
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
    
    # Get the structured ontology
    structured = query_engine.structured_ontology
    return render_template('browse.html', ontology=structured)

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