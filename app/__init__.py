import os
import threading
from flask import Flask, request, jsonify
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# Custom key function that allows whitelisting certain IPs
def get_rate_limit_key():
    # IPs that are exempt from rate limiting (localhost and development IPs)
    whitelisted_ips = {'127.0.0.1', '::1', '192.168.1.1', '10.0.0.1'}
    
    # Get the client's IP address
    ip_address = get_remote_address()
    
    # Return None for whitelisted IPs (which disables rate limiting for them)
    if ip_address in whitelisted_ips:
        return None
    
    # Otherwise, return the IP address for rate limiting
    return ip_address

# Initialize limiter without app
limiter = Limiter(
    key_func=get_rate_limit_key,
    default_limits=["200 per day", "50 per hour", "10 per minute"],
    storage_uri="memory://"
)

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
    
    # Initialize limiter with app
    limiter.init_app(app)
    
    # Rate limit error handler
    @app.errorhandler(429)
    def ratelimit_error(e):
        # Log the rate limit violation
        app.logger.warning(
            f"Rate limit exceeded: {request.remote_addr} - {request.method} {request.path}"
        )
        
        # Import here to avoid circular imports
        from app.utils.error_handling import rate_limit_error
        
        return rate_limit_error(
            message="Too many requests. Please slow down.",
            retry_after=e.description if hasattr(e, 'description') else "a while"
        )
    
    # Disable rate limiting for tests
    if testing:
        limiter.enabled = False
    
    # Configure global rate limit defaults for API endpoints
    # These will be applied in addition to any endpoint-specific limits
    @app.after_request
    def inject_rate_limit_headers(response):
        """Add rate limit headers to responses"""
        try:
            # Add rate limit headers if not already present
            if response.status_code != 429 and limiter.enabled:
                response.headers.add('X-RateLimit-Limit', '200 per day')
                response.headers.add('X-RateLimit-Remaining', 'varies')
        except:
            # Silently fail if headers can't be added
            pass
        return response

    # Register blueprints
    from app.routes import main, api, visualization
    from app.api import entities, relationships, graph
    
    # Register main blueprint first (it contains the query engine initialization)
    app.register_blueprint(main.bp)
    
    # Make sure data is loaded
    with app.app_context():
        main.load_query_engine()
        print(f"Query engine initialized during app startup: {main.query_engine is not None}")
    
    # Register existing blueprints
    app.register_blueprint(api.bp, url_prefix='/api')
    app.register_blueprint(visualization.bp)
    
    # Register new API blueprints for CRUD operations
    app.register_blueprint(entities.bp, url_prefix='/api')
    app.register_blueprint(relationships.bp, url_prefix='/api')
    app.register_blueprint(graph.bp, url_prefix='/api/graph')
    
    # Register error handlers
    from app.utils.error_handling import register_error_handlers
    register_error_handlers(app)

    # Register cleanup
    @app.teardown_appcontext
    def cleanup(exception=None):
        if exception:
            app.logger.error(f"Exception during teardown: {exception}")
        return app
