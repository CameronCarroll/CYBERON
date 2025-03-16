import os
from flask import Flask

def create_app(test_config=None, testing=False):
    """Create and configure the Flask application"""
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY='dev',
        UPLOAD_FOLDER=os.path.join(app.root_path, 'uploads'),
        DATA_FOLDER=os.path.join(app.root_path, 'data'),
        TESTING=testing
    )

    if test_config:
        # Load the test config if passed in
        app.config.from_mapping(test_config)

    # Make sure data directories exist (skip for testing)
    if not testing:
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        os.makedirs(app.config['DATA_FOLDER'], exist_ok=True)

    # Register blueprints
    from app.routes import main, api, visualization
    
    # Register main blueprint first (it contains the query engine initialization)
    app.register_blueprint(main.bp)
    
    # Make sure data is loaded
    with app.app_context():
        main.load_query_engine()
        print(f"Query engine initialized during app startup: {main.query_engine is not None}")
    
    # Register other blueprints
    app.register_blueprint(api.bp, url_prefix='/api')
    # Register visualization blueprint without a URL prefix to match the frontend requests
    app.register_blueprint(visualization.bp)

    return app