from flask import Blueprint, request, jsonify, current_app, g, render_template, redirect, url_for, session
from werkzeug.security import check_password_hash
import uuid
import hashlib
import base64
import secrets
import re
from datetime import datetime, timedelta
from jwt import decode

from app.models import Agent, IssuedToken, TaskAuditLog
from app.utils import (
    token_required, 
    verify_task_context, 
    generate_task_id,
    verify_token,
    verify_task_lineage,
    verify_scope_inheritance,
    is_scope_expansion_allowed,
    log_token_usage,
    verify_token_chain,
    verify_tool_access,
    decode_jwt_token
)
from app.utils.oauth import (
    log_oauth_error
)

oauth_bp = Blueprint('oauth', __name__, url_prefix='/api/oauth')

@oauth_bp.route('/authorize', methods=['GET', 'POST'])
def authorize():
    """
    OAuth 2.1 authorization endpoint.
    Supports Authorization Code flow with PKCE.
    """
    # Validate required parameters
    client_id = request.args.get('client_id')
    redirect_uri = request.args.get('redirect_uri')
    response_type = request.args.get('response_type')
    scope = request.args.get('scope', '')
    state = request.args.get('state')
    code_challenge = request.args.get('code_challenge')
    code_challenge_method = request.args.get('code_challenge_method', 'plain')
    task_id = request.args.get('task_id') or generate_task_id()
    parent_task_id = request.args.get('parent_task_id')
    parent_token = request.args.get('parent_token')
    
    # Validate required parameters
    if not client_id or not redirect_uri or not response_type:
        return jsonify({
            'error': 'invalid_request',
            'error_description': 'Missing required parameters'
        }), 400
        
    # Validate response type
    if response_type != 'code':
        return jsonify({
            'error': 'unsupported_response_type',
            'error_description': 'Only code response type is supported'
        }), 400
        
    # PKCE is mandatory in OAuth 2.1
    if not code_challenge:
        return jsonify({
            'error': 'invalid_request',
            'error_description': 'PKCE code_challenge is required'
        }), 400
        
    # Validate code challenge method
    if code_challenge_method not in ['plain', 'S256']:
        return jsonify({
            'error': 'invalid_request',
            'error_description': 'Invalid code_challenge_method'
        }), 400
        
    # Validate code challenge format
    if code_challenge_method == 'S256':
        # S256 should be URL-safe Base64 encoded string
        if not re.match(r'^[A-Za-z0-9\-_]+$', code_challenge) or len(code_challenge) < 43 or len(code_challenge) > 128:
            return jsonify({
                'error': 'invalid_request',
                'error_description': 'Invalid code_challenge format'
            }), 400
    
    # Get the agent/client
    agent = Agent.query.get(client_id)
    if not agent or not agent.is_active:
        return jsonify({
            'error': 'invalid_client',
            'error_description': 'Invalid or inactive client'
        }), 401
    
    # Parse scope
    if isinstance(scope, str):
        scope = [s.strip() for s in scope.split(' ') if s.strip()]
    
    # Check parent token if provided
    parent_token_obj = None
    if parent_token:
        parent_token_obj = verify_token(parent_token)
        if not parent_token_obj:
            return jsonify({
                'error': 'invalid_request', 
                'error_description': 'Invalid parent token'
            }), 401
            
        # Verify parent task ID if provided
        if parent_task_id and parent_token_obj.task_id != parent_task_id:
            return jsonify({
                'error': 'invalid_request',
                'error_description': 'Parent token does not match parent task ID'
            }), 400
            
        # Use parent task ID from token if not explicitly provided
        if not parent_task_id:
            parent_task_id = parent_token_obj.task_id
            
        # Verify scope inheritance
        if not set(scope).issubset(set(parent_token_obj.scope)):
            return jsonify({
                'error': 'invalid_scope',
                'error_description': 'Requested scope exceeds parent token scope'
            }), 403
    
    # For simplicity, we'll auto-approve the request
    # In a real implementation, you would render a consent form to the user
    task_description = request.args.get('task_description', f'Authorization request for {agent.agent_name}')
    granted_tools = []
    
    # Create authorization code with PKCE challenge
    try:
        token_obj, authorization_code = IssuedToken.create_authorization_code(
            client_id=client_id,
            scope=scope,
            granted_tools=granted_tools,
            task_id=task_id,
            task_description=task_description,
            parent_task_id=parent_task_id,
            parent_token_id=parent_token_obj.token_id if parent_token_obj else None,
            scope_inheritance_type='restricted',
            code_challenge=code_challenge,
            code_challenge_method=code_challenge_method
        )
        
        # Log authorization code issuance
        log_token_usage(token_obj, 'authorization_code_issued', 'success', {
            'response_type': response_type,
            'redirect_uri': redirect_uri,
            'parent_token_id': parent_token_obj.token_id if parent_token_obj else None,
            'code_challenge_method': code_challenge_method,
            'scope': scope
        })
        
        # Redirect to client with authorization code
        redirect_params = f'code={authorization_code}'
        if state:
            redirect_params += f'&state={state}'
            
        redirect_url = f"{redirect_uri}?{redirect_params}"
        return redirect(redirect_url)
        
    except Exception as e:
        current_app.logger.error(f"Error issuing authorization code: {str(e)}")
        return jsonify({
            'error': 'server_error',
            'error_description': 'Failed to issue authorization code'
        }), 500

@oauth_bp.route('/token', methods=['POST'])
def issue_token():
    """OAuth 2.1 token endpoint. Supports authorization code flow with PKCE and client credentials."""
    data = request.form if request.form else request.get_json()
    
    if not data:
        return jsonify({'error': 'invalid_request', 'error_description': 'Missing request data'}), 400
        
    grant_type = data.get('grant_type')
    
    if not grant_type:
        return jsonify({'error': 'invalid_request', 'error_description': 'Missing grant_type parameter'}), 400
        
    # Handle authorization code grant type (with PKCE)
    if grant_type == 'authorization_code':
        code = data.get('code')
        redirect_uri = data.get('redirect_uri')
        client_id = data.get('client_id')
        code_verifier = data.get('code_verifier')
        
        # Validate required parameters
        if not code or not redirect_uri or not client_id or not code_verifier:
            return jsonify({
                'error': 'invalid_request', 
                'error_description': 'Missing required parameters for authorization code grant'
            }), 400
            
        # Find authorization code
        token = IssuedToken.query.filter_by(
            client_id=client_id,
        ).filter(
            IssuedToken.authorization_code_hash.isnot(None)
        ).all()
        
        # Find the token with the matching authorization code
        valid_token = None
        for t in token:
            if t.is_valid() and check_password_hash(t.authorization_code_hash, code):
                valid_token = t
                break
                
        if not valid_token:
            return jsonify({
                'error': 'invalid_grant',
                'error_description': 'Invalid authorization code'
            }), 400
            
        # Verify client matches
        if valid_token.client_id != client_id:
            return jsonify({
                'error': 'invalid_grant',
                'error_description': 'Authorization code was not issued to this client'
            }), 400
            
        # Exchange code for tokens with PKCE verification
        success, result = valid_token.exchange_code_for_tokens(code_verifier)
        if not success:
            return jsonify({
                'error': 'invalid_grant',
                'error_description': result  # Error message
            }), 400
            
        access_token, refresh_token = result
        
        # Log token issuance
        log_token_usage(valid_token, 'token_issued', 'success', {
            'grant_type': grant_type,
            'parent_token_id': valid_token.parent_token_id,
            'code_verifier_valid': True
        })
        
        # Return tokens
        return jsonify({
            'access_token': access_token,
            'refresh_token': refresh_token,
            'token_type': 'Bearer',
            'expires_in': int((valid_token.expires_at - valid_token.issued_at).total_seconds()),
            'scope': ' '.join(valid_token.scope),
            'task_id': valid_token.task_id,
            'granted_tools': valid_token.granted_tools,
            'parent_task_id': valid_token.parent_task_id,
            'parent_token_id': valid_token.parent_token_id
        }), 200
        
    # Handle client credentials grant type
    elif grant_type == 'client_credentials':
        client_id = data.get('client_id')
        client_secret = data.get('client_secret')
        scope = data.get('scope', [])
        task_id = data.get('task_id') or generate_task_id()
        task_description = data.get('task_description')
        required_tools = data.get('required_tools', [])
        parent_task_id = data.get('parent_task_id')
        parent_token = data.get('parent_token')
        
        # Support for multiple parent tokens (new feature)
        parent_tokens = data.get('parent_tokens', [])
        
        # In OAuth 2.1, PKCE is mandatory even for client credentials
        code_challenge = data.get('code_challenge')
        code_challenge_method = data.get('code_challenge_method', 'S256')
        
        try:
            # Initialize parent_chain_verification here to fix the unbound local variable error
            parent_chain_verification = None
            
            # Log request parameters for debugging
            current_app.logger.debug(f"Client credentials token request: client_id={client_id}, task_id={task_id}")
            current_app.logger.debug(f"Required tools: {required_tools}")
            
            # PKCE is mandatory in OAuth 2.1
            if not code_challenge:
                current_app.logger.warning("PKCE code_challenge missing in token request")
                return jsonify({
                    'error': 'invalid_request',
                    'error_description': 'PKCE code_challenge is required'
                }), 400
                
            # Validate code challenge method
            if code_challenge_method not in ['plain', 'S256']:
                current_app.logger.warning(f"Invalid code_challenge_method: {code_challenge_method}")
                return jsonify({
                    'error': 'invalid_request',
                    'error_description': 'Invalid code_challenge_method'
                }), 400
            
            # Convert scope to list if string
            if isinstance(scope, str):
                scope = [s.strip() for s in scope.split(' ') if s.strip()]
                current_app.logger.debug(f"Converted scope string to list: {scope}")
                
            # Validate client credentials
            if not client_id or not client_secret:
                current_app.logger.warning("Missing client credentials in token request")
                return jsonify({'error': 'invalid_client', 'error_description': 'Missing client credentials'}), 401
                
            # Find agent
            agent = Agent.query.get(client_id)
            if not agent:
                current_app.logger.warning(f"Agent not found for client_id: {client_id}")
                return jsonify({'error': 'invalid_client', 'error_description': 'Invalid or inactive client'}), 401
            
            if not agent.is_active:
                current_app.logger.warning(f"Inactive agent for client_id: {client_id}")
                return jsonify({'error': 'invalid_client', 'error_description': 'Invalid or inactive client'}), 401
                
            # Verify client secret
            try:
                if not agent.verify_client_secret(client_secret):
                    current_app.logger.warning(f"Invalid client secret for client_id: {client_id}")
                    return jsonify({'error': 'invalid_client', 'error_description': 'Invalid client credentials'}), 401
            except Exception as secret_err:
                current_app.logger.error(f"Error verifying client secret: {str(secret_err)}", exc_info=True)
                return jsonify({'error': 'server_error', 'error_description': 'Error verifying client credentials'}), 500
                
            # Prepare for parent token verification
            parent_token_obj = None
            parent_token_id = None
            parent_verifications = None
            
            # Verify single parent token if provided (legacy support)
            if parent_token:
                try:
                    current_app.logger.debug(f"Verifying parent token for client_id: {client_id}")
                    parent_token_obj = verify_token(parent_token)
                    if not parent_token_obj:
                        current_app.logger.warning(f"Invalid parent token for client_id: {client_id}")
                        return jsonify({'error': 'invalid_grant', 'error_description': 'Invalid parent token'}), 401
                        
                    parent_token_id = parent_token_obj.token_id
                        
                    # Verify parent task ID if provided
                    if parent_task_id and parent_token_obj.task_id != parent_task_id:
                        current_app.logger.warning(f"Parent task ID mismatch: {parent_task_id} vs {parent_token_obj.task_id}")
                        return jsonify({'error': 'invalid_request', 'error_description': 'Parent token does not match parent task ID'}), 400
                        
                    # Use parent task ID from token if not explicitly provided
                    if not parent_task_id:
                        parent_task_id = parent_token_obj.task_id
                        current_app.logger.debug(f"Using parent task ID from token: {parent_task_id}")
                except Exception as parent_err:
                    current_app.logger.error(f"Error verifying parent token: {str(parent_err)}", exc_info=True)
                    return jsonify({'error': 'server_error', 'error_description': 'Error verifying parent token'}), 500
                    
            # Verify multiple parent tokens if provided
            if parent_tokens:
                try:
                    current_app.logger.debug(f"Verifying parent token chain for client_id: {client_id}")
                    # Create a temporary token for verification
                    tmp_token = IssuedToken(
                        token_id=str(uuid.uuid4()),
                        client_id=client_id,
                        access_token_hash="temporary",
                        scope=scope,
                        granted_tools=[],
                        task_id=task_id,
                        parent_task_id=parent_task_id,
                        parent_token_id=parent_token_id
                    )
                    
                    # Add the single parent token to the list if provided
                    if parent_token and parent_token_obj:
                        parent_tokens_data = [{'token': parent_token, 'task_id': parent_task_id}]
                        # Add additional parent tokens from the list
                        if isinstance(parent_tokens, list):
                            parent_tokens_data.extend(parent_tokens)
                        else:
                            parent_tokens_data.append(parent_tokens)
                    else:
                        parent_tokens_data = parent_tokens if isinstance(parent_tokens, list) else [parent_tokens]
                        
                    # Verify the token chain
                    parent_chain_verification = verify_token_chain(tmp_token, parent_tokens_data, 
                                                                  allow_clock_skew=True, 
                                                                  max_clock_skew_seconds=86400)
                    
                    # If verification failed, return error
                    if not parent_chain_verification["success"]:
                        current_app.logger.warning(f"Parent token chain verification failed: {parent_chain_verification}")
                        return jsonify({
                            'error': 'invalid_request', 
                            'error_description': 'Invalid parent token chain',
                            'details': parent_chain_verification
                        }), 400
                        
                    # If we don't have a direct parent yet but verification succeeded, use the first parent
                    if not parent_token_obj and parent_chain_verification["parent_verifications"]:
                        for parent_ver in parent_chain_verification["parent_verifications"]:
                            if parent_ver.get("is_direct_parent"):
                                # Find this token
                                direct_parent_id = parent_ver.get("token_id")
                                if direct_parent_id:
                                    parent_token_id = direct_parent_id
                                    parent_token_obj = IssuedToken.query.get(direct_parent_id)
                                    if parent_token_obj and not parent_task_id:
                                        parent_task_id = parent_token_obj.task_id
                                        current_app.logger.debug(f"Using direct parent task ID: {parent_task_id}")
                                break
                except Exception as chain_err:
                    current_app.logger.error(f"Error verifying parent token chain: {str(chain_err)}", exc_info=True)
                    return jsonify({'error': 'server_error', 'error_description': 'Error verifying parent token chain'}), 500
                        
            # Validate requested scope against agent's allowed capabilities
            try:
                current_app.logger.debug(f"Granting tools for agent: {client_id}")
                granted_tools = []
                for tool in required_tools:
                    # Check if the agent has this tool by name
                    if any(t.name == tool for t in agent.tools):
                        granted_tools.append(tool)
                        current_app.logger.debug(f"Granted tool: {tool}")
                    else:
                        current_app.logger.debug(f"Tool not granted: {tool}")
            except Exception as tool_err:
                current_app.logger.error(f"Error granting tools: {str(tool_err)}", exc_info=True)
                return jsonify({'error': 'server_error', 'error_description': 'Error granting tools'}), 500
                
            # If parent token exists, verify scope inheritance
            if parent_token_obj:
                try:
                    current_app.logger.debug("Verifying scope inheritance against parent token")
                    # Verify all requested scopes are subset of parent's scopes
                    if not set(scope).issubset(set(parent_token_obj.scope)):
                        current_app.logger.warning(f"Scope inheritance validation failed. Requested: {scope}, Parent: {parent_token_obj.scope}")
                        
                        # Check if expansion is allowed by policy
                        exceeded_scopes = set(scope) - set(parent_token_obj.scope)
                        expansion_allowed = is_scope_expansion_allowed(
                            exceeded_scopes, 
                            set(parent_token_obj.scope), 
                            client_id, 
                            parent_token_obj.client_id
                        )
                        
                        if expansion_allowed:
                            current_app.logger.info(f"Scope expansion allowed by policy. Expansion: {exceeded_scopes}")
                        else:
                            # Create more detailed error message
                            error_response = {
                                'error': 'invalid_scope', 
                                'error_description': 'Requested scope exceeds parent token scope',
                                'request_id': getattr(request, 'request_id', 'unknown'),
                                'details': {
                                    'requested_scopes': list(scope),
                                    'available_parent_scopes': list(parent_token_obj.scope),
                                    'exceeded_scopes': list(exceeded_scopes),
                                    'task_id': task_id,
                                    'parent_task_id': parent_task_id,
                                    'client_id': client_id,
                                    'resolution': 'Child tasks can only request scopes that are equal to or a subset of their parent task\'s scopes, unless allowed by policy'
                                }
                            }
                            # Log detailed analytics for this security restriction
                            current_app.logger.info(f"SECURITY_EVENT: Scope inheritance restriction enforced | Client: {client_id} | Task: {task_id} | Parent: {parent_task_id} | Exceeded scopes: {list(exceeded_scopes)}")
                            
                            # Use new error logging function
                            log_oauth_error(
                                error_type='invalid_scope',
                                error_description='Requested scope exceeds parent token scope',
                                details=error_response['details'],
                                client_id=client_id,
                                request=request
                            )
                            
                            return jsonify(error_response), 403
                        
                    # Verify all tools are subset of parent's tools
                    if not set(granted_tools).issubset(set(parent_token_obj.granted_tools)):
                        current_app.logger.warning(f"Tool inheritance validation failed. Granted: {granted_tools}, Parent: {parent_token_obj.granted_tools}")
                        # Create more detailed error message
                        exceeded_tools = set(granted_tools) - set(parent_token_obj.granted_tools)
                        error_response = {
                            'error': 'invalid_scope', 
                            'error_description': 'Requested tools exceed parent token tools',
                            'request_id': getattr(request, 'request_id', 'unknown'),
                            'details': {
                                'requested_tools': list(granted_tools),
                                'available_parent_tools': list(parent_token_obj.granted_tools),
                                'exceeded_tools': list(exceeded_tools),
                                'task_id': task_id,
                                'parent_task_id': parent_task_id,
                                'client_id': client_id,
                                'resolution': 'Child tasks can only use tools that are available to their parent task'
                            }
                        }
                        # Log detailed analytics for this security restriction
                        current_app.logger.info(f"SECURITY_EVENT: Tool inheritance restriction enforced | Client: {client_id} | Task: {task_id} | Parent: {parent_task_id} | Exceeded tools: {list(exceeded_tools)}")
                        return jsonify(error_response), 403
                        

                except Exception as inherit_err:
                    current_app.logger.error(f"Error verifying scope inheritance: {str(inherit_err)}", exc_info=True)
                    return jsonify({'error': 'server_error', 'error_description': 'Error verifying scope inheritance'}), 500
            
            # Create token record
            try:
                current_app.logger.debug(f"Creating token for client_id: {client_id}, task_id: {task_id}")
                token_obj, access_token, refresh_token = IssuedToken.create(
                    client_id=client_id,
                    scope=scope,
                    granted_tools=granted_tools,
                    task_id=task_id,
                    task_description=task_description,
                    parent_task_id=parent_task_id,
                    parent_token_id=parent_token_id,
                    scope_inheritance_type='restricted',
                    code_challenge=code_challenge,
                    code_challenge_method=code_challenge_method
                )
                
                # Log token issuance
                log_details = {
                    'grant_type': grant_type,
                    'parent_token_id': parent_token_id,
                    'requested_tools': required_tools,
                    'granted_tools': granted_tools,
                    'requested_scope': scope,
                    'code_challenge_method': code_challenge_method
                }
                
                # Add parent verification details if available
                if parent_chain_verification:
                    log_details['parent_verifications'] = parent_chain_verification
                    
                log_token_usage(token_obj, 'token_issued', 'success', log_details)
                
                # Prepare response
                response = {
                    'access_token': access_token,
                    'refresh_token': refresh_token,
                    'token_type': 'Bearer',
                    'expires_in': int((token_obj.expires_at - token_obj.issued_at).total_seconds()),
                    'scope': ' '.join(scope),
                    'task_id': task_id,
                    'granted_tools': granted_tools,
                    'parent_task_id': parent_task_id,
                    'parent_token_id': parent_token_id
                }
                
                # Include parent verification results if available
                if parent_chain_verification:
                    response['parent_verifications'] = parent_chain_verification
                    
                return jsonify(response), 200
                
            except Exception as e:
                # Log the detailed error
                current_app.logger.error(f"Error issuing token: {str(e)}", exc_info=True)
                
                # Get the full traceback
                import traceback
                tb = traceback.format_exc()
                current_app.logger.error(f"Token issuance traceback: {tb}")
                
                # Try to identify specific error type
                error_type = type(e).__name__
                error_msg = str(e)
                
                if "verify_token_chain" in error_msg or "parent_tokens" in error_msg:
                    return jsonify({'error': 'server_error', 'error_description': f'Parent token chain verification error: {error_type} - {error_msg}'}), 500
                elif "scope" in error_msg:
                    return jsonify({'error': 'server_error', 'error_description': f'Scope validation error: {error_type} - {error_msg}'}), 500
                elif "tool" in error_msg:
                    return jsonify({'error': 'server_error', 'error_description': f'Tool validation error: {error_type} - {error_msg}'}), 500
                else:
                    return jsonify({'error': 'server_error', 'error_description': 'Failed to issue token', 'details': {'error_type': error_type, 'error_message': error_msg}}), 500
            
        except Exception as e:
            current_app.logger.error(f"Error issuing token: {str(e)}")
            return jsonify({'error': 'server_error', 'error_description': 'Failed to issue token'}), 500
            
    # Handle refresh token grant type
    elif grant_type == 'refresh_token':
        refresh_token = data.get('refresh_token')
        client_id = data.get('client_id')
        client_secret = data.get('client_secret')
        code_verifier = data.get('code_verifier')  # PKCE is required for token refresh too
        
        # Validate required parameters
        if not refresh_token or not client_id or not client_secret or not code_verifier:
            return jsonify({
                'error': 'invalid_request',
                'error_description': 'Missing required parameters for refresh token grant'
            }), 400
            
        # Verify client credentials
        agent = Agent.query.get(client_id)
        if not agent or not agent.is_active or not agent.verify_client_secret(client_secret):
            return jsonify({'error': 'invalid_client', 'error_description': 'Invalid client credentials'}), 401
            
        # Find token with matching refresh token
        tokens = IssuedToken.query.filter_by(
            client_id=client_id,
            is_revoked=False
        ).all()
        
        valid_token = None
        for token in tokens:
            if token.refresh_token_hash and check_password_hash(token.refresh_token_hash, refresh_token):
                valid_token = token
                break
                
        if not valid_token:
            return jsonify({'error': 'invalid_grant', 'error_description': 'Invalid refresh token'}), 400
            
        # Verify token is not expired
        if not valid_token.is_valid():
            return jsonify({'error': 'invalid_grant', 'error_description': 'Refresh token expired'}), 400
            
        # Verify PKCE code verifier against stored challenge
        if valid_token.code_challenge_method == 'S256':
            hash_obj = hashlib.sha256(code_verifier.encode())
            calculated_challenge = base64.urlsafe_b64encode(hash_obj.digest()).decode().rstrip('=')
            is_valid = (calculated_challenge == valid_token.code_challenge)
        elif valid_token.code_challenge_method == 'plain':
            is_valid = (code_verifier == valid_token.code_challenge)
        else:
            is_valid = False
            
        if not is_valid:
            return jsonify({'error': 'invalid_grant', 'error_description': 'Invalid code verifier'}), 400
            
        # Generate new tokens
        new_access_token = secrets.token_urlsafe(32)
        new_refresh_token = secrets.token_urlsafe(48)
        
        # Update token
        valid_token.access_token_hash = generate_password_hash(new_access_token)
        valid_token.refresh_token_hash = generate_password_hash(new_refresh_token)
        
        # Update expiration
        expires_in = current_app.config.get('ACCESS_TOKEN_EXPIRY', timedelta(hours=1))
        valid_token.expires_at = datetime.utcnow() + expires_in
        
        db.session.commit()
        
        # Log token refresh
        log_token_usage(valid_token, 'token_refreshed', 'success', {
            'grant_type': grant_type
        })
        
        # Return new tokens
        return jsonify({
            'access_token': new_access_token,
            'refresh_token': new_refresh_token,
            'token_type': 'Bearer',
            'expires_in': int((valid_token.expires_at - valid_token.issued_at).total_seconds()),
            'scope': ' '.join(valid_token.scope),
            'task_id': valid_token.task_id,
            'granted_tools': valid_token.granted_tools,
            'parent_task_id': valid_token.parent_task_id,
            'parent_token_id': valid_token.parent_token_id
        }), 200
    else:
        return jsonify({'error': 'unsupported_grant_type', 'error_description': 'Unsupported grant type'}), 400

@oauth_bp.route('/verify', methods=['POST'])
def verify_token_endpoint():
    """Verify a token and its task context."""
    try:
        data = request.get_json()
        
        if not data or not data.get('token'):
            return jsonify({'error': 'Missing token'}), 400
            
        token_str = data.get('token')
        task_id = data.get('task_id')
        parent_task_id = data.get('parent_task_id')
        parent_token = data.get('parent_token')
        
        # Extract clock skew parameters
        allow_clock_skew = data.get('allow_clock_skew', True)
        max_clock_skew_seconds = data.get('max_clock_skew_seconds', 86400)  # Default 1 day
        
        # Support for multiple parent tokens (new feature)
        parent_tokens = data.get('parent_tokens', [])
        
        # Debug logging for the request
        current_app.logger.debug(f"Token verification request: token_str (first 10 chars): {token_str[:10] if token_str else None}, task_id: {task_id}")
        current_app.logger.debug(f"Clock skew settings: allow_clock_skew={allow_clock_skew}, max_clock_skew_seconds={max_clock_skew_seconds}")
        
        # Try to decode as JWT first for better diagnostics
        jwt_info = {}
        try:
            import jwt
            import time
            current_time = time.time()
            
            # Try decoding without verification first to get structure
            jwt_payload = jwt.decode(token_str, options={"verify_signature": False})
            jwt_info["decoded"] = True
            jwt_info["payload"] = jwt_payload
            
            # Check for clock skew issues
            if 'iat' in jwt_payload:
                iat = jwt_payload['iat']
                time_until_valid = iat - current_time
                jwt_info["time_until_valid"] = time_until_valid
                
                if time_until_valid > 0:
                    if allow_clock_skew and time_until_valid <= max_clock_skew_seconds:
                        jwt_info["clock_skew_handled"] = True
                        current_app.logger.info(f"Token has future iat timestamp but within allowed clock skew: {time_until_valid} seconds")
                    else:
                        jwt_info["clock_skew_handled"] = False
                        current_app.logger.warning(f"Token has future iat timestamp outside allowed clock skew: {time_until_valid} seconds")
            
            # Now try with verification and clock skew handling
            verification_options = {"leeway": 30}  # Default minimal leeway
            
            # For significant clock skew, we need to override nbf/iat validation
            if allow_clock_skew and max_clock_skew_seconds > 30:
                verification_options["verify_nbf"] = False
                verification_options["verify_iat"] = False
                current_app.logger.debug(f"Disabling nbf/iat verification due to large clock skew allowance: {max_clock_skew_seconds} seconds")
            
            verified_payload = jwt.decode(
                token_str, 
                current_app.config.get('SECRET_KEY', 'default-secret'),
                algorithms=['HS256'],
                options=verification_options
            )
            jwt_info["verified"] = True
            
            if 'token_id' in verified_payload:
                jwt_info["token_id"] = verified_payload['token_id']
                # Check if token exists in database
                db_token = IssuedToken.query.filter_by(token_id=verified_payload['token_id']).first()
                if db_token:
                    jwt_info["found_in_db"] = True
                    jwt_info["token_valid"] = db_token.is_valid()
                    
                    # Check for hash match (but not critical for JWTs)
                    hash_valid = check_password_hash(db_token.access_token_hash, token_str)
                    jwt_info["hash_valid"] = hash_valid
                else:
                    jwt_info["found_in_db"] = False
            
        except Exception as jwt_err:
            jwt_info["decoded"] = False
            jwt_info["error"] = str(jwt_err)
            current_app.logger.debug(f"Token is not a valid JWT: {str(jwt_err)}")
        
        # Verify token using the standard verify_token function - pass clock skew parameters
        token = verify_token(token_str, allow_clock_skew=allow_clock_skew, max_clock_skew_seconds=max_clock_skew_seconds)
        if not token:
            # Return detailed error information
            error_response = {
                'is_valid': False,
                'error': 'Invalid or expired token',
                'debug_info': {
                    'token_starts_with': token_str[:20] if token_str else None,
                    'token_length': len(token_str) if token_str else 0,
                    'jwt_info': jwt_info,
                    'allow_clock_skew': allow_clock_skew,
                    'max_clock_skew_seconds': max_clock_skew_seconds
                }
            }
            
            if jwt_info.get("found_in_db", False):
                db_token = IssuedToken.query.filter_by(token_id=jwt_info["token_id"]).first()
                if db_token:
                    error_response['debug_info']['token_found_in_db'] = True
                    error_response['debug_info']['is_revoked'] = db_token.is_revoked
                    error_response['debug_info']['is_expired'] = db_token.expires_at < datetime.utcnow()
                    error_response['debug_info']['expires_at'] = db_token.expires_at.isoformat()
            
            return jsonify(error_response), 200  # Return 200 with validation info
        
        # Token is valid - continue with the rest of the verification
        # Verify task context if provided
        task_context_valid = True
        if task_id and token.task_id != task_id:
            task_context_valid = False
            current_app.logger.warning(f"Task ID mismatch: token task_id={token.task_id}, requested task_id={task_id}")
        
        # Verify single parent token if provided (legacy support)
        parent_token_obj = None
        parent_valid = True
        scope_inheritance_valid = True
        
        if parent_token:
            parent_token_obj = verify_token(parent_token)
            if not parent_token_obj:
                parent_valid = False
                current_app.logger.warning("Parent token validation failed")
            else:
                # Verify parent task ID
                if parent_task_id and parent_token_obj.task_id != parent_task_id:
                    parent_valid = False
                    current_app.logger.warning(f"Parent task ID mismatch: token={parent_token_obj.task_id}, requested={parent_task_id}")
                    
                # Verify token lineage
                if not verify_task_lineage(token, parent_token=parent_token_obj):
                    parent_valid = False
                    current_app.logger.warning("Token lineage verification failed")
                    
                # Verify scope inheritance
                if not verify_scope_inheritance(token, parent_token_obj):
                    scope_inheritance_valid = False
                    current_app.logger.warning("Scope inheritance verification failed")
        
        # Handle verification against multiple parent tokens (new feature)
        parent_chain_verification = None
        if parent_tokens:
            # Convert to the format expected by verify_token_chain
            if not isinstance(parent_tokens, list):
                parent_tokens = [parent_tokens]
                
            # Add the single parent token to the list if provided
            if parent_token and parent_token_obj:
                parent_tokens_data = [{'token': parent_token, 'task_id': parent_task_id}]
                # Add additional parent tokens from the list
                parent_tokens_data.extend(parent_tokens)
            else:
                parent_tokens_data = parent_tokens
                
            # Verify the token chain
            parent_chain_verification = verify_token_chain(token, parent_tokens_data, 
                                                         allow_clock_skew=allow_clock_skew, 
                                                         max_clock_skew_seconds=max_clock_skew_seconds)
            
            # Update the overall parent_valid flag based on chain verification
            if not parent_chain_verification["success"]:
                parent_valid = False
                current_app.logger.warning("Parent token chain verification failed")
        
        # Log verification attempt
        log_token_usage(token, 'token_verification', 'success', {
            'task_id': task_id,
            'parent_task_id': parent_task_id,
            'task_context_valid': task_context_valid,
            'parent_valid': parent_valid,
            'scope_inheritance_valid': scope_inheritance_valid,
            'parent_chain_verified': parent_chain_verification["success"] if parent_chain_verification else None
        })
        
        # Add more detailed information about the token for debugging
        token_debug_info = {
            'token_id': token.token_id,
            'client_id': token.client_id,
            'task_id': token.task_id,
            'is_revoked': token.is_revoked,
            'expires_at': token.expires_at.isoformat(),
            'is_expired': token.expires_at < datetime.utcnow(),
            'issued_at': token.issued_at.isoformat(),
            'jwt_info': jwt_info
        }
        
        # Return verification result
        result = {
            'is_valid': token.is_valid(),
            'task_context_valid': task_context_valid,
            'parent_valid': parent_valid,
            'scope_inheritance_valid': scope_inheritance_valid,
            'token_info': token.to_dict(),
            'debug_info': token_debug_info
        }
        
        # Include parent chain verification if performed
        if parent_chain_verification:
            result['parent_chain_verification'] = parent_chain_verification
        
        return jsonify(result), 200

    except Exception as e:
        # Log the error
        current_app.logger.error(f"Error in verify_token_endpoint: {str(e)}", exc_info=True)
        
        # Return a meaningful error response
        return jsonify({
            'is_valid': False,
            'error': 'Server error during token verification',
            'error_detail': str(e),
            'error_type': type(e).__name__
        }), 500

@oauth_bp.route('/tool', methods=['POST'])
@token_required
def verify_tool_access_endpoint():
    """Verify if a token has access to use a specific tool."""
    data = request.get_json()
    
    if not data or not data.get('tool_name'):
        return jsonify({'error': 'Missing tool_name parameter'}), 400
        
    tool_name = data.get('tool_name')
    task_id = data.get('task_id', g.token.task_id)
    parent_tokens = data.get('parent_tokens', [])
    
    # Extract clock skew parameters
    allow_clock_skew = data.get('allow_clock_skew', True)
    max_clock_skew_seconds = data.get('max_clock_skew_seconds', 86400)  # Default 1 day
    
    current_app.logger.debug(f"Tool access verification request: tool_name={tool_name}, task_id={task_id}")
    current_app.logger.debug(f"Clock skew settings: allow_clock_skew={allow_clock_skew}, max_clock_skew_seconds={max_clock_skew_seconds}")
    
    # Verify task context
    if g.token.task_id != task_id:
        return jsonify({
            'access_granted': False,
            'error': 'Task ID mismatch',
            'task_id': task_id,
            'token_task_id': g.token.task_id
        }), 200
    
    # Verify parent tokens if provided
    parent_chain_valid = True
    parent_chain_verification = None
    
    if parent_tokens:
        # Apply clock skew settings to token chain verification
        for token_data in parent_tokens:
            if 'token' in token_data:
                # Create a temporary token object with the parent token for verification
                parent_token_obj = verify_token(
                    token_data['token'], 
                    allow_clock_skew=allow_clock_skew,
                    max_clock_skew_seconds=max_clock_skew_seconds
                )
                if not parent_token_obj:
                    current_app.logger.warning(f"Parent token verification failed with clock skew: allow_clock_skew={allow_clock_skew}, max_clock_skew_seconds={max_clock_skew_seconds}")
        
        parent_chain_verification = verify_token_chain(g.token, parent_tokens, 
                                                     allow_clock_skew=allow_clock_skew, 
                                                     max_clock_skew_seconds=max_clock_skew_seconds)
        parent_chain_valid = parent_chain_verification["success"]
        
        if not parent_chain_valid:
            return jsonify({
                'access_granted': False,
                'error': 'Invalid parent token chain',
                'parent_chain_verification': parent_chain_verification,
                'clock_skew_settings': {
                    'allow_clock_skew': allow_clock_skew,
                    'max_clock_skew_seconds': max_clock_skew_seconds
                }
            }), 200
    
    # Check tool access permission
    has_access = verify_tool_access(g.token, tool_name)
    
    # Log verification attempt
    log_token_usage(g.token, 'tool_access_verification', 
                   'success' if has_access else 'denied', {
        'tool_name': tool_name,
        'task_id': task_id,
        'access_granted': has_access,
        'parent_chain_valid': parent_chain_valid,
        'allow_clock_skew': allow_clock_skew,
        'max_clock_skew_seconds': max_clock_skew_seconds
    })
    
    # Return verification result
    result = {
        'access_granted': has_access,
        'tool_name': tool_name,
        'granted_tools': g.token.granted_tools,
        'task_id': task_id,
        'clock_skew_settings': {
            'allow_clock_skew': allow_clock_skew,
            'max_clock_skew_seconds': max_clock_skew_seconds
        }
    }
    
    # Include parent chain verification if performed
    if parent_chain_verification:
        result['parent_chain_verification'] = parent_chain_verification
    
    return jsonify(result), 200

@oauth_bp.route('/introspect', methods=['POST'])
def introspect_token():
    """Introspect a token to get detailed information about it."""
    data = request.get_json()
    
    if not data or not data.get('token'):
        return jsonify({'error': 'Missing token'}), 400
        
    token_str = data.get('token')
    include_task_history = data.get('include_task_history', False)
    include_children = data.get('include_children', False)
    
    # Verify token
    token = verify_token(token_str)
    if not token:
        return jsonify({
            'active': False
        }), 200  # Return 200 with inactive status
    
    # Build response with token details
    response = {
        'active': token.is_valid(),
        'token_info': token.to_dict(include_children=include_children)
    }
    
    # Include task history if requested
    if include_task_history:
        task_history = TaskAuditLog.get_task_history(token.task_id)
        response['task_history'] = [log.to_dict() for log in task_history]
        
        # Get task chain if parent exists
        if token.parent_task_id:
            task_chain = TaskAuditLog.get_task_chain(token.task_id)
            response['task_chain'] = task_chain
    
    # Log introspection
    log_token_usage(token, 'token_introspection', 'success', {
        'include_task_history': include_task_history,
        'include_children': include_children
    })
    
    return jsonify(response), 200

@oauth_bp.route('/revoke', methods=['POST'])
def revoke_token():
    """Revoke a token."""
    data = request.get_json()
    
    if not data or not data.get('token'):
        return jsonify({'error': 'Missing token'}), 400
        
    token_str = data.get('token')
    reason = data.get('reason')
    revoke_children = data.get('revoke_children', True)
    
    # Verify token
    token = verify_token(token_str)
    if not token:
        return jsonify({
            'revoked': False,
            'error': 'Invalid token'
        }), 200  # Return 200 with status
    
    # Revoke token (this will also revoke child tokens if revoke_children is True)
    try:
        token.revoke(reason=reason)
        
        # Log revocation
        log_token_usage(token, 'token_revoked', 'success', {
            'reason': reason,
            'revoke_children': revoke_children,
            'affected_child_tokens': [child.token_id for child in token.child_tokens] if revoke_children else []
        })
        
        return jsonify({
            'revoked': True,
            'token_id': token.token_id,
            'affected_child_tokens': [child.token_id for child in token.child_tokens] if revoke_children else []
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Error revoking token: {str(e)}")
        return jsonify({
            'revoked': False,
            'error': 'Failed to revoke token'
        }), 500

@oauth_bp.route('/protected', methods=['GET'])
@token_required
@verify_task_context
def protected_endpoint():
    """Example protected endpoint requiring token authentication and task context verification."""
    # Extract clock skew parameters from headers for logging
    allow_clock_skew = request.headers.get('X-Allow-Clock-Skew', 'true').lower() == 'true'
    try:
        max_clock_skew_seconds = int(request.headers.get('X-Max-Clock-Skew-Seconds', '86400'))
    except ValueError:
        max_clock_skew_seconds = 86400  # Default to 1 day
    
    # Add clock skew settings to the response for debugging
    current_app.logger.debug(f"Protected endpoint accessed with clock skew settings: allow_clock_skew={allow_clock_skew}, max_clock_skew_seconds={max_clock_skew_seconds}")
    
    return jsonify({
        'message': 'Access granted to protected resource',
        'agent': g.current_agent.to_dict(),
        'token': g.token.to_dict(),
        'clock_skew_settings': {
            'allow_clock_skew': allow_clock_skew,
            'max_clock_skew_seconds': max_clock_skew_seconds
        }
    }), 200
    
@oauth_bp.route('/.well-known/oauth-authorization-server', methods=['GET'])
def metadata_endpoint():
    """Authorization Server Metadata endpoint (RFC 8414)"""
    # Build the issuer URL based on the current request
    issuer_url = f"{request.scheme}://{request.host}"
    
    metadata = {
        "issuer": issuer_url,
        "authorization_endpoint": f"{issuer_url}/api/oauth/authorize",
        "token_endpoint": f"{issuer_url}/api/oauth/token",
        "token_endpoint_auth_methods_supported": [
            "client_secret_basic",
            "client_secret_post"
        ],
        "token_endpoint_auth_signing_alg_values_supported": [
            "RS256"
        ],
        "introspection_endpoint": f"{issuer_url}/api/oauth/introspect",
        "revocation_endpoint": f"{issuer_url}/api/oauth/revoke",
        "jwks_uri": f"{issuer_url}/api/oauth/jwks",
        "response_types_supported": [
            "code"
        ],
        "grant_types_supported": [
            "authorization_code",
            "client_credentials",
            "refresh_token"
        ],
        "revocation_endpoint_auth_methods_supported": [
            "client_secret_basic",
            "client_secret_post"
        ],
        "revocation_endpoint_auth_signing_alg_values_supported": [
            "RS256" 
        ],
        "introspection_endpoint_auth_methods_supported": [
            "client_secret_basic",
            "client_secret_post"
        ],
        "code_challenge_methods_supported": [
            "plain",
            "S256"
        ],
        "service_documentation": f"{issuer_url}/api/docs",
        "ui_locales_supported": [
            "en-US"
        ]
    }
    
    return jsonify(metadata), 200
    
@oauth_bp.route('/validation/test', methods=['POST'])
def validation_test_endpoint():
    """
    Test endpoint specifically for validating negative examples.
    This endpoint deliberately performs strict validation to help identify security issues.
    """
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'Missing request data'}), 400
    
    validation_type = data.get('validation_type')
    if not validation_type:
        return jsonify({'error': 'Missing validation_type parameter'}), 400
    
    # Validate token and task context
    token_str = data.get('token')
    task_id = data.get('task_id')
    parent_token = data.get('parent_token')
    parent_task_id = data.get('parent_task_id')
    
    results = {
        'validation_type': validation_type,
        'validation_errors': [],
        'validation_passed': False
    }
    
    # Check token validity
    if not token_str:
        results['validation_errors'].append('Missing token')
    else:
        token = verify_token(token_str)
        if not token:
            results['validation_errors'].append('Invalid or expired token')
        else:
            results['token_valid'] = True
            
            # Check task context
            if not task_id:
                results['validation_errors'].append('Missing task_id')
            elif token.task_id != task_id:
                results['validation_errors'].append('Token does not match task_id')
            else:
                results['task_context_valid'] = True
                
            # Check parent token if provided
            if parent_token:
                parent_token_obj = verify_token(parent_token)
                if not parent_token_obj:
                    results['validation_errors'].append('Invalid parent token')
                else:
                    results['parent_token_valid'] = True
                    
                    # Check parent task ID
                    if not parent_task_id:
                        results['validation_errors'].append('Missing parent_task_id when parent_token provided')
                    elif parent_token_obj.task_id != parent_task_id:
                        results['validation_errors'].append('Parent token does not match parent_task_id')
                    else:
                        results['parent_task_context_valid'] = True
                        
                    # Check lineage
                    if not verify_task_lineage(token, parent_token=parent_token_obj):
                        results['validation_errors'].append('Task lineage verification failed')
                    else:
                        results['lineage_valid'] = True
                        
                    # Check scope inheritance
                    if not verify_scope_inheritance(token, parent_token_obj):
                        results['validation_errors'].append('Scope inheritance verification failed')
                    else:
                        results['scope_inheritance_valid'] = True
    
    # Additional validation types
    if validation_type == 'permission_escalation':
        # Check for any signs of permission escalation
        requested_scope = data.get('requested_scope', [])
        if isinstance(requested_scope, str):
            requested_scope = requested_scope.split()
        
        granted_scope = token.scope if token else []
        
        escalated_scopes = [s for s in granted_scope if s not in requested_scope]
        if escalated_scopes:
            results['validation_errors'].append(f'Scope escalation detected: {escalated_scopes}')
        else:
            results['no_scope_escalation'] = True
            
    elif validation_type == 'tool_access':
        # Check if token has access to requested tools
        requested_tools = data.get('requested_tools', [])
        if token:
            unauthorized_tools = [t for t in requested_tools if t not in token.granted_tools]
            if unauthorized_tools:
                results['validation_errors'].append(f'Unauthorized tool access: {unauthorized_tools}')
            else:
                results['tool_access_valid'] = True
        
    elif validation_type == 'token_replay':
        # Check if this appears to be a token replay attack
        usage_count = data.get('usage_count', 1)
        if token and usage_count > 1:
            # In a real implementation, this would check a token usage counter
            results['validation_errors'].append('Potential token replay detected')
    
    # Update overall validation status
    results['validation_passed'] = len(results['validation_errors']) == 0
    
    # Log validation attempt if we have a valid token
    if token:
        log_token_usage(token, 'validation_test', 
                        'success' if results['validation_passed'] else 'failure',
                        {
                            'validation_type': validation_type,
                            'validation_errors': results['validation_errors'],
                            'request_data': {k: v for k, v in data.items() if k != 'token' and k != 'parent_token'}
                        })
    
    return jsonify(results), 200

@oauth_bp.route('/register', methods=['POST'])
def register_client():
    """Dynamic Client Registration endpoint"""
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'invalid_request', 'error_description': 'Missing request data'}), 400
        
    # Extract client metadata
    client_name = data.get('client_name')
    client_uri = data.get('client_uri')
    redirect_uris = data.get('redirect_uris', [])
    grant_types = data.get('grant_types', ['authorization_code'])
    response_types = data.get('response_types', ['code'])
    token_endpoint_auth_method = data.get('token_endpoint_auth_method', 'client_secret_basic')
    
    # Validate required fields
    if not client_name:
        return jsonify({'error': 'invalid_client_metadata', 'error_description': 'Missing required field: client_name'}), 400
        
    if 'authorization_code' in grant_types and not redirect_uris:
        return jsonify({'error': 'invalid_client_metadata', 'error_description': 'redirect_uris are required for authorization_code grant type'}), 400
        
    # Validate supported values
    for grant_type in grant_types:
        if grant_type not in ['authorization_code', 'client_credentials', 'refresh_token']:
            return jsonify({'error': 'invalid_client_metadata', 'error_description': f'Unsupported grant_type: {grant_type}'}), 400
            
    for response_type in response_types:
        if response_type != 'code':
            return jsonify({'error': 'invalid_client_metadata', 'error_description': f'Unsupported response_type: {response_type}'}), 400
            
    if token_endpoint_auth_method not in ['client_secret_basic', 'client_secret_post']:
        return jsonify({'error': 'invalid_client_metadata', 'error_description': f'Unsupported token_endpoint_auth_method: {token_endpoint_auth_method}'}), 400
        
    # Create the client
    try:
        agent, client_secret = Agent.create(
            agent_name=client_name,
            description=client_uri,
            max_scope_level='restricted'
        )
        
        # Activate client immediately for testing purposes
        # In production, you might want to require admin approval
        agent.is_active = True
        db.session.commit()
        
        # Return client information
        return jsonify({
            'client_id': agent.client_id,
            'client_secret': client_secret,  # Only returned once during registration
            'client_id_issued_at': int(agent.created_at.timestamp()),
            'client_secret_expires_at': 0,  # Does not expire
            'client_name': agent.agent_name,
            'client_uri': agent.description,
            'redirect_uris': redirect_uris,
            'grant_types': grant_types,
            'response_types': response_types,
            'token_endpoint_auth_method': token_endpoint_auth_method,
            'registration_client_uri': f"{request.host_url.rstrip('/')}/api/oauth/register/{agent.client_id}",
            'registration_access_token': agent.registration_token
        }), 201
        
    except Exception as e:
        current_app.logger.error(f"Error registering client: {str(e)}")
        return jsonify({'error': 'server_error', 'error_description': 'Failed to register client'}), 500 