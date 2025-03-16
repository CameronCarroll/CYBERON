from flask import Blueprint, render_template, current_app, send_from_directory
from app.routes.main import query_engine

bp = Blueprint('visualization', __name__)

@bp.route('/ontology')
def view_ontology():
    """Render the ontology visualization page"""
    if query_engine is None:
        return render_template('error.html', message="No ontology data loaded")
    
    summary = query_engine.generate_ontology_summary()
    return render_template('ontology.html', summary=summary)

@bp.route('/explore')
def explore():
    """Render the explore page"""
    if query_engine is None:
        return render_template('error.html', message="No ontology data loaded")
    
    return render_template('explore.html')

# Serve static files for visualization
@bp.route('/libs/<path:path>')
def send_lib(path):
    return send_from_directory(current_app.root_path + '/static/libs', path)