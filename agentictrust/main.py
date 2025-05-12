from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette import status
import os
import uvicorn
from typing import Dict, Any
import time
import uuid
from contextlib import asynccontextmanager
from fastapi.encoders import jsonable_encoder

# Import routers
from agentictrust.routers import (
    agents,
    tools,
    scopes,
    policies,
    oauth,
    admin,
    users,
    discovery,
    delegations,
)

# Import key loader
from agentictrust.utils.keys import load_or_generate_keys

# Import loguru logger configured via logging.yml
from agentictrust.utils.logger import logger, format_request_log

# Generate or load JWKS keys
load_or_generate_keys()

# Define lifespan context manager before app instantiation so it's in scope
@asynccontextmanager
async def lifespan(app):
    """Lifespan context manager for database setup and teardown"""
    try:
        from agentictrust.db import init_db, db_session
        app.state.db_session = db_session
        init_db()
        print("Database initialized successfully")
        
        # Initialise core engines (singletons) after DB is ready
        try:
            from agentictrust.core import initialize_core_engines
            initialize_core_engines()
            print("Core engines initialised successfully")
        except Exception as e:
            print(f"Error initialising core engines: {str(e)}")
        
        # Load initial data from configuration files
        try:
            from agentictrust.utils.initial_data import load_initial_data
            load_initial_data()
            print("Initial configuration data loaded successfully")
        except Exception as e:
            print(f"Error loading initial data: {str(e)}")
    except Exception as e:
        print(f"Error initializing database: {str(e)}")
    yield
    try:
        from agentictrust.db import db_session
        db_session.remove()
        print("Database connections closed")
    except Exception as e:
        print(f"Error closing database connections: {str(e)}")

# Create FastAPI app
app = FastAPI(
    title="AgenticTrust OAuth Server",
    description="Secure OAuth Framework for LLM-Based Agents",
    version="1.0.1",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust as needed for your environment
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(agents.router)
app.include_router(tools.router)
app.include_router(scopes.router)
app.include_router(policies.router)
app.include_router(oauth.router)
app.include_router(admin.router)
app.include_router(users.router)
app.include_router(discovery.router)
app.include_router(delegations.router)

# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    request.state.start_time = time.time()

    # Log the request using the 'app' logger context
    logger.bind(context="app").info(f"{request.method} {request.url.path} (ID: {request_id})")

    response = await call_next(request)

    # Log the response with color-coded time and status using the helper
    request_time = time.time() - request.state.start_time
    ms = request_time * 1000
    logger.bind(context="app").info(f"Request completed: {request.method} {request.url.path} {response.status_code} in {ms:.1f}ms")

    return response

# Exception handlers
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Handle HTTP exceptions with standard format."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            'error': 'Not found' if exc.status_code == 404 else 'Request error',
            'detail': exc.detail,
            'request_id': getattr(request.state, 'request_id', 'unknown')
        }
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle Pydantic validation errors."""
    request_id = request.state.request_id if hasattr(request.state, 'request_id') else 'N/A'
    print(f"Validation error for request {request_id}: {exc.errors()}")

    # Safely handle exc.body if it's bytes
    body_content = exc.body
    if isinstance(body_content, bytes):
        try:
            body_content = body_content.decode('utf-8')
        except UnicodeDecodeError:
            body_content = f"<bytes data - length: {len(body_content)} couldn't be decoded as utf-8>"

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": jsonable_encoder(exc.errors()), "body": body_content}
    )

@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    """Handle any unhandled exceptions with a standard format."""
    # Log the exception
    print(f"Unhandled exception: {type(exc).__name__} - {str(exc)}")
    
    # Only show error details in debug mode
    debug = os.environ.get('DEBUG', 'False') == 'True'
    
    return JSONResponse(
        status_code=500,
        content={
            'error': 'Server error',
            'detail': str(exc) if debug else 'An internal server error occurred',
            'request_id': getattr(request.state, 'request_id', 'unknown')
        }
    )

# Root route
@app.get("/")
async def index() -> Dict[str, Any]:
    return {
        'service': 'AgenticTrust OAuth Server',
        'version': '1.0.1',
        'status': 'running',
        'documentation': '/docs',  
    }

# Database dependency for routes
def get_db():
    """Get database session dependency"""
    from agentictrust.db import db_session
    try:
        yield db_session
    finally:
        pass  # The scoped_session will handle cleanup automatically

if __name__ == '__main__':
    # Try loading host and port from environment, fall back to defaults
    host = os.environ.get('HOST', '127.0.0.1')
    port = int(os.environ.get('PORT', 5001))
    debug = os.environ.get('DEBUG', 'True') == 'True'
    
    # Database initialization would go here with SQLAlchemy + FastAPI integration
    # TODO: Set up proper database connection and initialization
    
    print(f"Server running at http://{host}:{port}")
    print(f"API Documentation available at http://{host}:{port}/docs")
    
    # Run the FastAPI app with Uvicorn
    uvicorn.run("agentictrust.main:app", host=host, port=port, reload=debug)
