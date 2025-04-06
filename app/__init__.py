from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS
import time
import uuid

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()

def create_app(config=None):
    app = Flask(__name__)
    
    # Configure the app
    app.config.from_object('config.Config')
    if config:
        app.config.update(config)
    
    # Initialize extensions with app
    db.init_app(app)
    migrate.init_app(app, db)
    CORS(app)

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
    
    app.register_blueprint(agents_bp)
    app.register_blueprint(oauth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(tools_bp)
    
    logger.info(f"Application started with environment: {app.config.get('ENV', 'development')}")
    
    return app 