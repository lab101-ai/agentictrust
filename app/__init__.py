from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS
import time
import uuid
import os
from datetime import datetime, timedelta

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()

def create_app(config=None):
    app = Flask(__name__, static_folder=None, template_folder=None)
    
    # Load configuration from YAML file
    try:
        from app.utils.config import load_config
        flask_config = load_config("flask")
        app.config.update(flask_config)
    except (ImportError, FileNotFoundError):
        # Fallback to old configuration method
        app.config.from_object('config.Config')
    
    # Override with environment-specific config
    if config:
        app.config.update(config)
    
    # Configure database URI
    if "DATABASE_URI" in app.config:
        app.config["SQLALCHEMY_DATABASE_URI"] = app.config["DATABASE_URI"]
        app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    
    # Initialize extensions with app
    db.init_app(app)
    migrate.init_app(app, db)
    
    # Configure CORS based on settings
    cors_origins = app.config.get("CORS_ORIGINS", "*")
    CORS(app, resources={r"/*": {"origins": cors_origins}})

    # Import logger after app configuration
    from app.utils.logger import logger
    
    # Request logging middleware
    @app.before_request
    def before_request():
        request_id = request.headers.get('X-Request-ID', str(uuid.uuid4()))
        request.request_id = request_id
        request.start_time = time.time()
        logger.bind(request_id=request_id).info(
            f"Request started: {request.method} {request.path}"
        )

    @app.after_request
    def after_request(response):
        request_time = time.time() - request.start_time
        logger.bind(request_id=getattr(request, 'request_id', 'unknown')).info(
            f"Request completed: {request.method} {request.path} "
            f"- Status: {response.status_code} - Duration: {request_time:.4f}s"
        )
        return response
    
    # Register blueprints
    from app.routes.agents import agents_bp
    from app.routes.oauth import oauth_bp
    from app.routes.admin import admin_bp
    from app.routes.tools import tools_bp
    from app.routes.scopes import scopes_bp
    
    app.register_blueprint(agents_bp)
    app.register_blueprint(oauth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(tools_bp)
    app.register_blueprint(scopes_bp)
    
    # Initialize database and load configuration data
    with app.app_context():
        try:
            from app.utils.initial_data import load_initial_data
            load_initial_data()
        except Exception as e:
            logger.error(f"Error initializing database and configuration: {str(e)}")
    
    @app.route('/')
    def index():
        return jsonify({
            'service': 'AgenticTrust OAuth Server',
            'version': '1.0.1',
            'status': 'running',
            'documentation': '/api/docs',
            'features': [
                'OAuth 2.1 with PKCE',
                'Task-based token issuance',
                'Parent-child token inheritance',
                'Tool-specific authorization',
                'Token revocation',
                'Task context verification',
                'Audit logging',
                'Multiple parent token verification (NEW)',
                'Tool access check endpoint (NEW)',
                'Tool permission verification (NEW)',
                'Task lineage verification (NEW)',
                'Scope management (NEW)'
            ]
        })
    
    @app.errorhandler(404)
    def not_found(e):
        return jsonify({'error': 'Not found'}), 404
        
    @app.errorhandler(403)
    def forbidden(e):
        """
        Enhanced error handler for 403 Forbidden responses.
        Provides more detailed information for OAuth scope errors.
        """
        logger.warning(f"Forbidden access: {request.path} - {str(e)}")
        
        # Check if this is a JSON response from our routes
        if request.path.startswith('/api/oauth/'):
            # Try to get response data if it's from our OAuth routes
            error_data = getattr(e, 'description', None)
            if isinstance(error_data, dict):
                # Already formatted response with details, just return it
                return jsonify(error_data), 403
                
        # Default generic forbidden response
        return jsonify({
            'error': 'forbidden',
            'error_description': str(e),
            'request_id': getattr(request, 'request_id', 'unknown'),
            'documentation': '/api/docs#errors'
        }), 403
        
    @app.errorhandler(500)
    def server_error(e):
        app.logger.error(f"Server error: {str(e)}")
        return jsonify({'error': 'Server error'}), 500
        
    # Global exception handler for better error responses
    @app.errorhandler(Exception)
    def handle_unhandled_exception(e):
        """Handle any unhandled exceptions and return meaningful error responses."""
        
        # Get exception details
        error_type = type(e).__name__
        error_message = str(e)
        
        # Import logger here to avoid circular import
        from app.utils.logger import logger
        
        # Log the exception
        logger.exception(f"Unhandled exception: {error_type} - {error_message}")
        
        # Create a meaningful response based on error type
        if error_type == 'HTTPException':
            # Already handled by other error handlers
            raise e
            
        # Check if this is an OAuth error
        if request.path.startswith('/api/oauth/'):
            # OAuth errors should be more detailed
            from app.utils.oauth import log_oauth_error
            
            # Try to parse client info from request
            client_id = None
            data = request.get_json() if request.is_json else request.form
            if data:
                client_id = data.get('client_id')
                
            # Log OAuth error
            log_oauth_error(
                error_type='server_error',
                error_description=f"Unhandled exception: {error_type}",
                client_id=client_id,
                request=request
            )
            
            # Return OAuth error format
            return jsonify({
                'error': 'server_error',
                'error_description': 'The server encountered an unexpected condition',
                'request_id': getattr(request, 'request_id', 'unknown'),
                'error_details': error_message if app.config.get('DEBUG', False) else None
            }), 500
        
        # Generic error response
        return jsonify({
            'error': 'Server error', 
            'request_id': getattr(request, 'request_id', 'unknown')
        }), 500
    
    @app.after_request
    def enhance_error_responses(response):
        """Add more details to error responses, particularly for OAuth errors."""
        if response.status_code in (400, 401, 403) and response.content_type == 'application/json':
            try:
                # Try to parse the response data
                data = response.get_json()
                if isinstance(data, dict) and 'error' in data:
                    # Enhanced logging for OAuth errors
                    error_type = data.get('error', 'unknown')
                    error_desc = data.get('error_description', 'No description')
                    details = data.get('details', {})
                    
                    # Log differently based on error type
                    if error_type == 'invalid_scope':
                        # Log detailed scope errors
                        if 'exceeded_scopes' in details:
                            logger.warning(
                                f"Scope error: {error_desc} - " 
                                f"Requested scopes: {details.get('requested_scopes')} - "
                                f"Available parent scopes: {details.get('available_parent_scopes')} - "
                                f"Exceeded: {details.get('exceeded_scopes')}"
                            )
                        else:
                            logger.warning(f"Scope error: {error_desc}")
                    elif error_type in ('invalid_request', 'invalid_client', 'invalid_grant'):
                        logger.warning(f"OAuth error: {error_type} - {error_desc}")
                    else:
                        logger.warning(f"Error response: {error_type} - {error_desc}")
            except Exception as parse_err:
                # If parsing fails, just log the status
                logger.warning(f"Error response ({response.status_code}): Could not parse response - {str(parse_err)}")
        
        return response
    
    # Create database tables if they don't exist (for SQLite)
    with app.app_context():
        if app.config.get('SQLALCHEMY_DATABASE_URI', '').startswith('sqlite'):
            db.create_all()
            
    # Configure scope expansion policy
    app.config['SCOPE_EXPANSION_POLICY'] = {
        'global': {
            # Define global rules for scope expansions
            'allowed_expansions': [
                # Allow read:web to expand to write:content for LLM summarization
                {'from_scope': 'read:web', 'to_scope': 'write:content'},
                
                # Other common expansions that might make sense
                {'from_scope': 'read:data', 'to_scope': 'write:data'},
                {'from_scope': 'read:calendar', 'to_scope': 'write:calendar'},
            ],
            'allowed_patterns': [
                # Allow read:* to expand to corresponding write:* in the same domain
                {'required_scope': 'read:web', 'allowed_expansion': 'write:web'},
            ]
        },
        'clients': {
            # You can define client-specific policies here
            # 'client-id-here': {
            #    'allow_all_expansions': False,
            #    'allowed_expansions': []
            # }
        }
    }
    
    logger.info(f"Application started with environment: {os.environ.get('FLASK_ENV', app.config.get('ENV', 'development'))}")
    
    return app 