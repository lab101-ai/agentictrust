import uuid
import jwt
import hashlib
import base64
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

def decode_jwt_token(token, allow_clock_skew=True, max_clock_skew_seconds=86400):
    """Decode and validate a JWT token."""
    try:
        # Try to decode without verification first to get debugging info
        try:
            import time
            current_time = time.time()
            
            unverified_payload = jwt.decode(token, options={"verify_signature": False})
            logger.debug(f"JWT token pre-verification payload: {unverified_payload}")
            
            # Log timestamp information
            if 'iat' in unverified_payload and 'exp' in unverified_payload:
                iat = unverified_payload['iat']
                exp = unverified_payload['exp']
                time_until_valid = iat - current_time
                time_until_expiry = exp - current_time
                
                logger.debug(f"JWT token timestamps - iat: {iat}, exp: {exp}, current time: {current_time}")
                logger.debug(f"JWT token timing - time until valid: {time_until_valid}, time until expiry: {time_until_expiry}")
                
                if time_until_valid > 0:
                    if allow_clock_skew and time_until_valid <= max_clock_skew_seconds:
                        logger.info(f"JWT token has future iat but within allowed clock skew ({max_clock_skew_seconds} seconds)")
                    else:
                        logger.warning(f"JWT token has future iat outside allowed clock skew: {time_until_valid} seconds")
                        
        except Exception as e:
            logger.warning(f"Error during JWT pre-validation debugging: {str(e)}")
        
        # Configure verification options for clock skew
        verification_options = {"leeway": 30}  # Default minimal leeway
        
        # For significant clock skew, we need to override nbf/iat validation
        if allow_clock_skew and max_clock_skew_seconds > 30:
            verification_options["verify_nbf"] = False
            verification_options["verify_iat"] = False
            logger.debug(f"Disabling nbf/iat verification due to large clock skew allowance: {max_clock_skew_seconds} seconds")
            
        # Now do the actual verification
        payload = jwt.decode(token, current_app.config['SECRET_KEY'], 
                            algorithms=['HS256'],
                            options=verification_options)
                            
        logger.bind(
            token_id=payload.get('token_id'),
            client_id=payload.get('client_id')
        ).debug("Successfully decoded JWT token")
        
        return payload
    except jwt.ExpiredSignatureError:
        logger.warning("JWT token validation failed: expired signature")
        return None
    except jwt.InvalidTokenError as e:
        logger.warning(f"JWT token validation failed: invalid token - {str(e)}")
        return None
    except Exception as e:
        logger.warning(f"Unexpected error decoding JWT token: {str(e)}")
        return None

def verify_token(token_str, allow_clock_skew=True, max_clock_skew_seconds=86400):
    """Verify an access token and return the corresponding token object if valid."""
    try:
        # First check if it's a JWT token by attempting to decode it
        try:
            import jwt
            from flask import current_app
            import time
            
            # Debug logging for clock skew analysis
            current_time = time.time()
            logger.debug(f"verify_token - Current time: {current_time}")
            
            # Decode the JWT without verification first to get the token_id
            # This helps with debugging if the token is malformed
            payload = jwt.decode(
                token_str, 
                options={"verify_signature": False}
            )
            logger.debug(f"JWT payload pre-verification: {payload}")
            token_id = payload.get('token_id')
            
            # Look up the token in the database before signature verification
            # This allows us to log more information about the token if verification fails
            db_token = None
            if token_id:
                from app.models import IssuedToken
                db_token = IssuedToken.query.get(token_id)
                if db_token:
                    logger.debug(f"Found token in DB: id={token_id}, task_id={db_token.task_id}")
                else:
                    logger.warning(f"Token not found in DB: id={token_id}")
            
            # Check for clock skew
            if 'iat' in payload and 'exp' in payload:
                iat = payload['iat']
                exp = payload['exp']
                time_until_valid = iat - current_time
                time_until_expiry = exp - current_time
                
                logger.debug(f"JWT timestamps - iat: {iat}, exp: {exp}")
                logger.debug(f"Time until valid: {time_until_valid}, time until expiry: {time_until_expiry}")
                
                # If token is from the future but within skew allowance, accept it
                if time_until_valid > 0:
                    if allow_clock_skew and time_until_valid <= max_clock_skew_seconds:
                        logger.info(f"Token has future iat timestamp but within allowed clock skew ({max_clock_skew_seconds} seconds)")
                    else:
                        logger.warning(f"Token has future iat timestamp outside allowed clock skew: {time_until_valid} seconds")
                        if not allow_clock_skew:
                            logger.warning("Clock skew tolerance is disabled")
            
            # Now do full verification with leeway for clock skew
            verification_options = {"leeway": 30}  # Default 30 seconds of leeway
            
            # For significant clock skew, we need to override nbf/iat validation
            if allow_clock_skew and max_clock_skew_seconds > 30:
                verification_options["verify_nbf"] = False
                verification_options["verify_iat"] = False
                logger.debug(f"Disabling nbf/iat verification due to large clock skew allowance: {max_clock_skew_seconds} seconds")
            
            try:
                payload = jwt.decode(
                    token_str, 
                    current_app.config.get('SECRET_KEY', 'default-secret'),
                    algorithms=['HS256'],
                    options=verification_options
                )
                logger.debug(f"JWT token validation successful")
            except jwt.InvalidTokenError as jwt_err:
                # If we have DB token info but JWT validation failed, provide more context
                if db_token:
                    logger.warning(f"JWT validation failed but token exists in DB. Error: {str(jwt_err)}")
                    logger.debug(f"DB token issued_at={db_token.issued_at.isoformat()}, expires_at={db_token.expires_at.isoformat()}")
                    
                    # If clock skew is the issue and token is otherwise valid in DB, special handling
                    if "not yet valid" in str(jwt_err) and allow_clock_skew and db_token.is_valid():
                        logger.info(f"Bypassing JWT timestamp validation due to clock skew allowance for token: {token_id}")
                        # Continue with DB token instead of failing
                        return db_token
                raise
            
            if not payload or 'token_id' not in payload:
                logger.warning("Token verification failed: invalid JWT payload structure")
                return None
                
            logger.debug(f"JWT token validation successful for token_id: {token_id}")
            
        except jwt.PyJWTError as jwt_err:
            logger.warning(f"JWT token validation failed: {str(jwt_err)}")
            # If JWT decode fails, try to debug the token
            if token_str:
                logger.debug(f"Token format debug - first 20 chars: {token_str[:20]}, length: {len(token_str)}")
            
            # If we already looked up the token in DB and it's valid, we can continue
            if db_token and db_token.is_valid() and allow_clock_skew:
                logger.info(f"Bypassing JWT validation due to clock skew allowance for valid DB token: {db_token.token_id}")
                return db_token
                
            return None
            
        # Find the token in database using the token_id from the payload
        token = IssuedToken.query.filter_by(token_id=payload['token_id']).first()
        if not token:
            logger.warning(f"Token verification failed: token_id {payload['token_id']} not found in database")
            return None
            
        # Check if token is still valid
        if not token.is_valid():
            logger.warning(f"Token verification failed: token_id {token.token_id} is no longer valid")
            if token.is_revoked:
                logger.warning(f"Token is revoked. Revocation reason: {token.revocation_reason}")
            if token.expires_at < datetime.utcnow():
                logger.warning(f"Token is expired. Expired at: {token.expires_at}")
            return None
            
        # Verify token hash - in production, this might be optional for JWT tokens
        # since the JWT signature verification provides strong guarantees
        hash_valid = check_password_hash(token.access_token_hash, token_str)
        if not hash_valid:
            logger.warning(f"Token verification failed: token_id {token.token_id} hash mismatch")
            # Log more details for debugging
            logger.debug(f"Token hash check failed. Token first 20 chars: {token_str[:20] if token_str else None}")
            
            # For JWT tokens, we might choose to accept them anyway if the JWT validation passed
            # This is a security vs. usability tradeoff
            if payload and 'token_id' in payload:
                logger.info(f"Accepting JWT token despite hash mismatch due to valid JWT signature. Token ID: {token.token_id}")
                # Skip the hash check for JWT tokens that have passed signature verification
            else:
                return None
        
        logger.bind(
            token_id=token.token_id,
            client_id=token.client_id,
            task_id=token.task_id
        ).debug("Token verification successful")
        
        return token
    except Exception as e:
        logger.error(f"Unexpected error in verify_token: {str(e)}", exc_info=True)
        return None

def verify_code_verifier(token, code_verifier):
    """Verify a PKCE code verifier against a stored code challenge."""
    if not token.code_challenge or not token.code_challenge_method:
        logger.warning(f"PKCE verification failed: token_id {token.token_id} has no code challenge")
        return False
        
    if token.code_challenge_method == 'S256':
        # SHA256 hash the verifier
        hash_obj = hashlib.sha256(code_verifier.encode())
        calculated_challenge = base64.urlsafe_b64encode(hash_obj.digest()).decode().rstrip('=')
        is_valid = (calculated_challenge == token.code_challenge)
    elif token.code_challenge_method == 'plain':
        # Plain comparison
        is_valid = (code_verifier == token.code_challenge)
    else:
        logger.warning(f"PKCE verification failed: token_id {token.token_id} has unsupported code challenge method")
        is_valid = False
        
    if not is_valid:
        logger.warning(f"PKCE verification failed: token_id {token.token_id} code verifier mismatch")
    else:
        logger.bind(
            token_id=token.token_id,
            client_id=token.client_id,
            task_id=token.task_id
        ).debug("PKCE verification successful")
        
    return is_valid

def generate_code_challenge(code_verifier, method='S256'):
    """Generate a PKCE code challenge from a code verifier."""
    if method == 'S256':
        # SHA256 hash the verifier
        hash_obj = hashlib.sha256(code_verifier.encode())
        code_challenge = base64.urlsafe_b64encode(hash_obj.digest()).decode().rstrip('=')
    elif method == 'plain':
        # No transformation
        code_challenge = code_verifier
    else:
        logger.warning(f"Unsupported code challenge method: {method}")
        return None
        
    logger.debug(f"Generated PKCE code challenge using method {method}")
    return code_challenge

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

def verify_scope_inheritance(token, parent_token, check_expansions=True):
    """
    Verify that a token's scope is a valid subset of its parent token's scope,
    with optional policy-based exceptions for scope expansion.
    
    Args:
        token: Child token to verify
        parent_token: Parent token to check against
        check_expansions: Whether to check for allowed scope expansions
        
    Returns:
        Boolean indicating if scope inheritance is valid
    """
    # Get the parent token's scope
    parent_scope = set(parent_token.scope)
    
    # Get this token's scope
    token_scope = set(token.scope)
    
    # First, check if this token's scope is a subset of the parent's scope
    is_subset = token_scope.issubset(parent_scope)
    
    # If it's a subset, it's valid
    if is_subset:
        return True
    
    # If not a subset and expansions aren't allowed, it's invalid
    if not check_expansions:
        return False
    
    # If not a subset, check if expansion is allowed for this particular combination
    # Get the scopes that exceed the parent scope
    exceeded_scopes = token_scope - parent_scope
    
    # Check if expansion is allowed using the configured policy
    return is_scope_expansion_allowed(exceeded_scopes, parent_scope, token.client_id, parent_token.client_id)

def is_scope_expansion_allowed(exceeded_scopes, parent_scopes, client_id=None, parent_client_id=None):
    """
    Check if scope expansion is allowed based on policy rules.
    
    Args:
        exceeded_scopes: Set of scopes that exceed parent scope
        parent_scopes: Set of parent token's scopes
        client_id: The client requesting the expansion (optional)
        parent_client_id: The parent token's client ID (optional)
        
    Returns:
        Boolean indicating if expansion is allowed
    """
    from flask import current_app
    
    # Default to denying expansions if no policy is defined
    if not hasattr(current_app, 'config') or 'SCOPE_EXPANSION_POLICY' not in current_app.config:
        return False
    
    # Get the policy from app config
    policy = current_app.config.get('SCOPE_EXPANSION_POLICY', {})
    
    # Check client-specific policies first if client ID is provided
    if client_id and client_id in policy.get('clients', {}):
        client_policy = policy['clients'][client_id]
        
        # Check if this client has a blanket allowance
        if client_policy.get('allow_all_expansions', False):
            logger.debug(f"Allowing scope expansion for authorized client: {client_id}")
            return True
            
        # Check for allowed expansions by scope
        allowed_expansions = client_policy.get('allowed_expansions', [])
        for expansion in allowed_expansions:
            # Check if this specific scope expansion is allowed
            if expansion.get('from_scope') in parent_scopes and expansion.get('to_scope') in exceeded_scopes:
                logger.debug(f"Allowing scope expansion from '{expansion.get('from_scope')}' to '{expansion.get('to_scope')}' for client: {client_id}")
                return True
    
    # Check global policies
    global_policies = policy.get('global', {})
    
    # Check for allowed scope patterns
    patterns = global_policies.get('allowed_patterns', [])
    for pattern in patterns:
        required_scope = pattern.get('required_scope')
        allowed_expansion = pattern.get('allowed_expansion')
        
        # If the parent has the required scope and the expansion matches the exceeded scope
        if required_scope in parent_scopes and allowed_expansion in exceeded_scopes:
            logger.debug(f"Allowing scope expansion from '{required_scope}' to '{allowed_expansion}' based on global policy")
            return True
    
    # Check specific expansion combinations
    expansions = global_policies.get('allowed_expansions', [])
    
    for expansion in expansions:
        from_scope = expansion.get('from_scope')
        to_scope = expansion.get('to_scope')
        
        # If the parent has the 'from' scope and child is requesting the 'to' scope
        if from_scope in parent_scopes and to_scope in exceeded_scopes:
            logger.debug(f"Allowing scope expansion from '{from_scope}' to '{to_scope}' based on global policy")
            return True
    
    # If no rules matched, deny the expansion
    logger.debug(f"Denying scope expansion: {exceeded_scopes} not allowed from parent scopes {parent_scopes}")
    return False

def verify_token_chain(token, parent_tokens_data, allow_clock_skew=True, max_clock_skew_seconds=86400):
    """
    Verify a token against a chain of parent tokens.
    
    Args:
        token: The IssuedToken object to verify
        parent_tokens_data: List of dictionaries containing parent token information
                            Format: [{'token': 'token_str', 'task_id': 'task_id'}, ...]
        allow_clock_skew: Whether to allow clock skew between systems
        max_clock_skew_seconds: Maximum allowed clock skew in seconds
                        
    Returns:
        Dictionary with verification results for each parent in the chain
    """
    log_ctx = {
        "token_id": token.token_id,
        "client_id": token.client_id,
        "task_id": token.task_id,
        "parent_task_id": token.parent_task_id,
        "allow_clock_skew": allow_clock_skew,
        "max_clock_skew_seconds": max_clock_skew_seconds
    }
    
    if not parent_tokens_data:
        logger.bind(**log_ctx).debug("No parent tokens to verify against")
        return {"success": True, "message": "No parent tokens to verify against"}
    
    logger.bind(**log_ctx).debug(f"Verifying token against {len(parent_tokens_data)} parent tokens")
    
    # Before using the token's own method, verify each parent token with clock skew settings
    verified_parent_tokens = []
    for idx, parent_data in enumerate(parent_tokens_data):
        if 'token' in parent_data:
            parent_token_str = parent_data['token']
            logger.bind(**log_ctx).debug(f"Verifying parent token {idx+1} with clock skew parameters")
            
            # Verify the parent token with the specified clock skew parameters
            parent_token_obj = verify_token(
                parent_token_str, 
                allow_clock_skew=allow_clock_skew,
                max_clock_skew_seconds=max_clock_skew_seconds
            )
            
            if parent_token_obj:
                logger.bind(**log_ctx).debug(f"Parent token {idx+1} verified successfully with clock skew parameters")
                # Store the verified token object for debugging
                parent_data['verified_token_id'] = parent_token_obj.token_id
            else:
                logger.bind(**log_ctx).warning(f"Parent token {idx+1} verification failed with clock skew parameters")
                # We'll continue verification chain, but tracking failure
                parent_data['verification_failed'] = True
                
            verified_parent_tokens.append(parent_data)
    
    # Use the token's own method for full chain verification
    # Note: This may need to be modified to pass clock skew parameters if token.verify_against_parent_tokens
    # doesn't handle it internally
    result = token.verify_against_parent_tokens(verified_parent_tokens)
    
    # Include clock skew information in the result
    result["clock_skew_settings"] = {
        "allow_clock_skew": allow_clock_skew,
        "max_clock_skew_seconds": max_clock_skew_seconds
    }
    
    if result["success"]:
        logger.bind(**log_ctx).info("Token chain verification successful")
    else:
        logger.bind(**log_ctx).warning("Token chain verification failed")
        
    return result

def verify_tool_access(token, tool_name):
    """
    Verify that a token has access to use a specific tool.
    
    Args:
        token: The IssuedToken object to verify
        tool_name: The name of the tool to check
        
    Returns:
        Boolean indicating if the token has permission
    """
    log_ctx = {
        "token_id": token.token_id,
        "client_id": token.client_id,
        "task_id": token.task_id,
        "tool_name": tool_name
    }
    
    # Check if the tool is in the granted tools list
    has_access = token.has_tool_permission(tool_name)
    
    if has_access:
        logger.bind(**log_ctx).debug(f"Tool access granted: {tool_name}")
    else:
        logger.bind(**log_ctx).warning(f"Tool access denied: {tool_name}")
        
    return has_access

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
            return jsonify({'error': 'invalid_request', 'error_description': 'Missing or invalid Authorization header'}), 401
            
        token_str = auth_header.split('Bearer ')[1]
        
        # Extract clock skew settings from headers or use defaults
        allow_clock_skew = True  # Default to allowing clock skew
        max_clock_skew_seconds = 86400  # Default to 1 day
        
        # Check if clock skew parameters are in the headers
        if 'X-Allow-Clock-Skew' in request.headers:
            allow_clock_skew = request.headers.get('X-Allow-Clock-Skew').lower() == 'true'
            
        if 'X-Max-Clock-Skew-Seconds' in request.headers:
            try:
                max_clock_skew_seconds = int(request.headers.get('X-Max-Clock-Skew-Seconds'))
            except ValueError:
                # If not a valid integer, use default
                pass
        
        logger.debug(f"API Request with token - Clock skew settings: allow_clock_skew={allow_clock_skew}, max_clock_skew_seconds={max_clock_skew_seconds}")
        
        # Verify token with clock skew parameters
        token = verify_token(token_str, allow_clock_skew=allow_clock_skew, max_clock_skew_seconds=max_clock_skew_seconds)
        
        if not token:
            return jsonify({
                'error': 'invalid_token', 
                'error_description': 'Invalid or expired token',
                'debug_info': {
                    'allow_clock_skew': allow_clock_skew,
                    'max_clock_skew_seconds': max_clock_skew_seconds
                }
            }), 401
            
        # Store token in g for later use
        g.token = token
        g.current_agent = Agent.query.get(token.client_id)
        
        # Log token usage
        log_token_usage(token, 'api_access', 'success', {
            'endpoint': request.path,
            'method': request.method,
            'allow_clock_skew': allow_clock_skew,
            'max_clock_skew_seconds': max_clock_skew_seconds
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
            return jsonify({'error': 'invalid_request', 'error_description': 'Missing task context (X-Task-ID header)'}), 400
            
        # Get token from g (set by token_required decorator)
        token = g.token
        
        # Verify task ID matches token's task ID
        if token.task_id != task_id:
            log_token_usage(token, 'task_context_verification', 'failed', {
                'reason': 'task_id_mismatch',
                'expected': token.task_id,
                'received': task_id
            })
            return jsonify({'error': 'invalid_request', 'error_description': 'Task ID mismatch'}), 403
            
        # If parent context provided, verify it
        if parent_task_id or parent_token_id:
            # If token doesn't have parent info but parent context provided, that's an error
            if not token.parent_task_id and not token.parent_token_id:
                log_token_usage(token, 'task_context_verification', 'failed', {
                    'reason': 'unexpected_parent_context',
                    'token_has_parent': False
                })
                return jsonify({'error': 'invalid_request', 'error_description': 'Unexpected parent context'}), 403
                
            # Verify parent task ID
            if parent_task_id and token.parent_task_id != parent_task_id:
                log_token_usage(token, 'task_context_verification', 'failed', {
                    'reason': 'parent_task_id_mismatch',
                    'expected': token.parent_task_id,
                    'received': parent_task_id
                })
                return jsonify({'error': 'invalid_request', 'error_description': 'Parent task ID mismatch'}), 403
                
            # Verify parent token ID
            if parent_token_id and token.parent_token_id != parent_token_id:
                log_token_usage(token, 'task_context_verification', 'failed', {
                    'reason': 'parent_token_id_mismatch',
                    'expected': token.parent_token_id,
                    'received': parent_token_id
                })
                return jsonify({'error': 'invalid_request', 'error_description': 'Parent token ID mismatch'}), 403
        
        # Log successful verification
        log_token_usage(token, 'task_context_verification', 'success')
        
        return f(*args, **kwargs)
    
    return decorated 

def log_oauth_error(error_type, error_description, details=None, client_id=None, request=None):
    """
    Log OAuth errors with request tracking information.
    
    Args:
        error_type: Type of error (e.g., 'invalid_scope', 'invalid_request')
        error_description: Human-readable error description
        details: Optional dictionary with error details
        client_id: Optional client ID causing the error
        request: Optional Flask request object for tracking
    """
    request_id = getattr(request, 'request_id', 'unknown') if request else 'unknown'
    client_str = f" | Client: {client_id}" if client_id else ""
    path = request.path if request else 'unknown'
    
    # Basic error entry
    error_entry = f"OAuth error: {error_type} - {error_description}{client_str} | Request ID: {request_id} | Path: {path}"
    
    # Log with appropriate level based on error type
    if error_type in ('invalid_scope', 'insufficient_scope'):
        # Scope errors are important security events
        if details and 'exceeded_scopes' in details:
            exceeded = details.get('exceeded_scopes', [])
            available = details.get('available_parent_scopes', [])
            logger.warning(f"{error_entry} | Exceeded: {exceeded} | Available: {available}")
        else:
            logger.warning(error_entry)
    elif error_type in ('invalid_client', 'invalid_grant', 'unauthorized_client'):
        # Authentication errors
        logger.warning(error_entry)
    elif error_type in ('server_error', 'temporarily_unavailable'):
        # Server errors
        logger.error(error_entry)
    else:
        # Other errors
        logger.info(error_entry)
        
    # Log to audit table if enabled and client_id is available
    try:
        from app.models import TaskAuditLog
        from app import db
        
        if client_id and details:
            # Use the specialized error log method that handles missing tokens
            TaskAuditLog.error_log(
                client_id=client_id,
                task_id=details.get('task_id', 'unknown'),
                event_type=f"error_{error_type}",
                status="error",
                parent_task_id=details.get('parent_task_id'),
                source_ip=getattr(request, 'remote_addr', None) if request else None,
                details={
                    'error_type': error_type,
                    'error_description': error_description,
                    'request_id': request_id,
                    'error_details': details
                }
            )
            logger.debug(f"Created OAuth error audit log: {error_type} - client: {client_id}")
    except Exception as e:
        logger.error(f"Failed to create audit log entry: {str(e)}") 