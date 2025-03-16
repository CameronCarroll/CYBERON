from flask import Blueprint, render_template, current_app, send_from_directory, request
import sys
# Import the main module rather than directly importing query_engine
import app.routes.main as main_module

bp = Blueprint('visualization', __name__)

@bp.route('/ontology')
def view_ontology():
    """Render the ontology visualization page"""
    print("VIZ: /ontology endpoint called", file=sys.stderr)
    
    # Get the latest reference to query_engine
    query_engine = main_module.query_engine
    
    if query_engine is None:
        print("VIZ: Error - query_engine is None", file=sys.stderr)
        # Try to load it once more
        main_module.load_query_engine()
        query_engine = main_module.query_engine
        
        if query_engine is None:
            print("VIZ: Failed to load query_engine", file=sys.stderr)
            return render_template('error.html', message="No ontology data loaded")
    
    try:
        print(f"VIZ: Query engine loaded with data from: {query_engine.data_source if hasattr(query_engine, 'data_source') else 'unknown'}", file=sys.stderr)
        summary = query_engine.generate_ontology_summary()
        print(f"VIZ: Generated summary with {summary['node_count']} nodes and {summary['edge_count']} edges", file=sys.stderr)
        return render_template('ontology.html', summary=summary)
    except Exception as e:
        import traceback
        print(f"VIZ: Error in view_ontology: {str(e)}", file=sys.stderr)
        print(traceback.format_exc(), file=sys.stderr)
        return render_template('error.html', message=f"Error generating visualization: {str(e)}")

@bp.route('/explore')
def explore():
    """Render the explore page"""
    # Get the latest reference to query_engine
    query_engine = main_module.query_engine
    
    if query_engine is None:
        # Try to load it once more
        main_module.load_query_engine()
        query_engine = main_module.query_engine
        
        if query_engine is None:
            return render_template('error.html', message="No ontology data loaded")
    
    return render_template('explore.html')

# Serve static files for visualization
@bp.route('/libs/<path:path>')
def send_lib(path):
    return send_from_directory(current_app.root_path + '/static/libs', path)