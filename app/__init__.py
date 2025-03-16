import os
from flask import Flask

def create_app(test_config=None):
    """Create and configure the Flask application"""
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY='dev',
        UPLOAD_FOLDER=os.path.join(app.root_path, 'uploads'),
        DATA_FOLDER=os.path.join(app.root_path, 'data'),
    )

    # Make sure data directories exist
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['DATA_FOLDER'], exist_ok=True)

    # Register blueprints
    from app.routes import main, api, visualization
    app.register_blueprint(main.bp)
    app.register_blueprint(api.bp, url_prefix='/api')
    app.register_blueprint(visualization.bp, url_prefix='/viz')

    return app