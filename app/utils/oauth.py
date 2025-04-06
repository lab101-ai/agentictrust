import uuid
import jwt
from datetime import datetime, timedelta
from functools import wraps
from flask import current_app, request, jsonify, g
from werkzeug.security import check_password_hash

from app.models import Agent, IssuedToken, TaskAuditLog
from app.utils.logger import logger

def generate_task_id():
    """Generate a unique task ID."""
    task_id = str(uuid.uuid4())
    logger.bind(task_id=task_id).debug("Generated new task ID")
    return task_id

def create_jwt_token(token_data, expiry=None):
    """Create a JWT token with the given data and expiry."""
    if not expiry:
        expiry = current_app.config.get('ACCESS_TOKEN_EXPIRY', timedelta(hours=1))
        
    payload = {
        **token_data,
        'exp': datetime.utcnow() + expiry,
        'iat': datetime.utcnow()
    }
    
    token = jwt.encode(payload, current_app.config['SECRET_KEY'], algorithm='HS256')
    logger.bind(
        token_id=token_data.get('token_id'),
        client_id=token_data.get('client_id')
    ).info(f"Created JWT token with expiry {expiry}")
    
    return token

def decode_jwt_token(token):
    """Decode and validate a JWT token."""
    try:
        payload = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])
        logger.bind(
            token_id=payload.get('token_id'),
            client_id=payload.get('client_id')
        ).debug("Successfully decoded JWT token")
        return payload
    except jwt.ExpiredSignatureError:
        logger.warning("JWT token validation failed: expired signature")
        return None
    except jwt.InvalidTokenError:
        logger.warning("JWT token validation failed: invalid token")
        return None

def verify_token(token_str):
    """Verify an access token and return the corresponding token object if valid."""
    # First check if it's a JWT token
    payload = decode_jwt_token(token_str)
    if not payload or 'token_id' not in payload:
        logger.warning("Token verification failed: invalid JWT payload")
        return None
        
    # Find the token in database
    token = IssuedToken.query.filter_by(token_id=payload['token_id']).first()
    if not token:
        logger.warning(f"Token verification failed: token_id {payload['token_id']} not found in database")
        return None
        
    # Check if token is still valid
    if not token.is_valid():
        logger.warning(f"Token verification failed: token_id {token.token_id} is no longer valid")
        return None
        
    # Verify token hash
    if not check_password_hash(token.access_token_hash, token_str):
        logger.warning(f"Token verification failed: token_id {token.token_id} hash mismatch")
        return None
    
    logger.bind(
        token_id=token.token_id,
        client_id=token.client_id,
        task_id=token.task_id
    ).debug("Token verification successful")
    
    return token

def verify_task_lineage(token, parent_token=None, task_id=None, parent_task_id=None):
    """Verify that a token has valid task lineage with its parent token."""
    log_ctx = {
        "token_id": token.token_id,
        "client_id": token.client_id,
        "task_id": token.task_id,
        "parent_task_id": token.parent_task_id
    }
    
    # If no parent token/task, just verify the token itself is valid
    if not parent_token and not parent_task_id:
        result = token.is_valid()
        logger.bind(**log_ctx).debug(f"Task lineage verification (token only): {result}")
        return result
        
    # If token doesn't have parent info, but parent is specified, invalid
    if not token.parent_token_id and not token.parent_task_id and (parent_token or parent_task_id):
        logger.bind(**log_ctx).warning("Task lineage verification failed: no parent info but parent specified")
        return False
        
    # Verify parent token matches
    if parent_token and token.parent_token_id != parent_token.token_id:
        logger.bind(**log_ctx).warning(
            f"Task lineage verification failed: parent token mismatch. Expected: {token.parent_token_id}, Got: {parent_token.token_id}"
        )
        return False
        
    # Verify parent task matches
    if parent_task_id and token.parent_task_id != parent_task_id:
        logger.bind(**log_ctx).warning(
            f"Task lineage verification failed: parent task mismatch. Expected: {token.parent_task_id}, Got: {parent_task_id}"
        )
        return False
        
    # Verify task ID 
    if task_id and token.task_id != task_id:
        logger.bind(**log_ctx).warning(
            f"Task lineage verification failed: task ID mismatch. Expected: {token.task_id}, Got: {task_id}"
        )
        return False
    
    logger.bind(**log_ctx).debug("Task lineage verification successful")    
    return True

def verify_scope_inheritance(token, parent_token):
    """Verify that a token's scope is a valid subset of its parent token's scope."""
    # Get the parent token's scope
    parent_scope = set(parent_token.scope)
    
    # Get this token's scope
    token_scope = set(token.scope)
    
    # Check if this token's scope is a subset of the parent's scope
    return token_scope.issubset(parent_scope)

def log_token_usage(token, event_type, status, details=None, source_ip=None):
    """Log token usage for audit purposes."""
    log_ctx = {
        "token_id": token.token_id,
        "client_id": token.client_id,
        "task_id": token.task_id,
        "parent_task_id": token.parent_task_id,
        "event_type": event_type,
        "status": status
    }
    
    if status == 'success':
        logger.bind(**log_ctx).info(f"Token usage: {event_type}")
    else:
        logger.bind(**log_ctx).warning(f"Token usage ({status}): {event_type} - {details}")
    
    return TaskAuditLog.log_event(
        client_id=token.client_id,
        token_id=token.token_id,
        access_token_hash=token.access_token_hash,
        task_id=token.task_id,
        parent_task_id=token.parent_task_id,
        event_type=event_type,
        status=status,
        source_ip=source_ip or request.remote_addr,
        details=details
    )

def token_required(f):
    """Decorator to require a valid token for API access."""
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Missing or invalid Authorization header'}), 401
            
        token_str = auth_header.split('Bearer ')[1]
        token = verify_token(token_str)
        
        if not token:
            return jsonify({'error': 'Invalid or expired token'}), 401
            
        # Store token in g for later use
        g.token = token
        g.current_agent = Agent.query.get(token.client_id)
        
        # Log token usage
        log_token_usage(token, 'api_access', 'success', {
            'endpoint': request.path,
            'method': request.method
        })
        
        return f(*args, **kwargs)
    
    return decorated

def verify_task_context(f):
    """Decorator to verify task context for API access."""
    @wraps(f)
    def decorated(*args, **kwargs):
        # Get task context from request
        task_id = request.headers.get('X-Task-ID')
        parent_task_id = request.headers.get('X-Parent-Task-ID')
        parent_token_id = request.headers.get('X-Parent-Token-ID')
        
        if not task_id:
            return jsonify({'error': 'Missing task context (X-Task-ID header)'}), 400
            
        # Get token from g (set by token_required decorator)
        token = g.token
        
        # Verify task ID matches token's task ID
        if token.task_id != task_id:
            log_token_usage(token, 'task_context_verification', 'failed', {
                'reason': 'task_id_mismatch',
                'expected': token.task_id,
                'received': task_id
            })
            return jsonify({'error': 'Task ID mismatch'}), 403
            
        # If parent context provided, verify it
        if parent_task_id or parent_token_id:
            # If token doesn't have parent info but parent context provided, that's an error
            if not token.parent_task_id and not token.parent_token_id:
                log_token_usage(token, 'task_context_verification', 'failed', {
                    'reason': 'unexpected_parent_context',
                    'token_has_parent': False
                })
                return jsonify({'error': 'Unexpected parent context'}), 403
                
            # Verify parent task ID
            if parent_task_id and token.parent_task_id != parent_task_id:
                log_token_usage(token, 'task_context_verification', 'failed', {
                    'reason': 'parent_task_id_mismatch',
                    'expected': token.parent_task_id,
                    'received': parent_task_id
                })
                return jsonify({'error': 'Parent task ID mismatch'}), 403
                
            # Verify parent token ID
            if parent_token_id and token.parent_token_id != parent_token_id:
                log_token_usage(token, 'task_context_verification', 'failed', {
                    'reason': 'parent_token_id_mismatch',
                    'expected': token.parent_token_id,
                    'received': parent_token_id
                })
                return jsonify({'error': 'Parent token ID mismatch'}), 403
        
        # Log successful verification
        log_token_usage(token, 'task_context_verification', 'success')
        
        return f(*args, **kwargs)
    
    return decorated 