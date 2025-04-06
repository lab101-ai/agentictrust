from flask import Blueprint, request, jsonify, current_app, g
from werkzeug.security import check_password_hash
import uuid

from app.models import Agent, IssuedToken, TaskAuditLog
from app.utils import (
    token_required, 
    verify_task_context, 
    generate_task_id,
    verify_token,
    verify_task_lineage,
    verify_scope_inheritance,
    log_token_usage
)

oauth_bp = Blueprint('oauth', __name__, url_prefix='/api/oauth')

@oauth_bp.route('/token', methods=['POST'])
def issue_token():
    """Issue a new token using client credentials grant."""
    data = request.get_json()
    
    # Validate required fields
    if not data:
        return jsonify({'error': 'Missing request data'}), 400
        
    grant_type = data.get('grant_type', 'client_credentials')
    
    if grant_type != 'client_credentials':
        return jsonify({'error': 'Unsupported grant type'}), 400
        
    client_id = data.get('client_id')
    client_secret = data.get('client_secret')
    scope = data.get('scope', [])
    task_id = data.get('task_id') or generate_task_id()
    task_description = data.get('task_description')
    required_tools = data.get('required_tools', [])
    required_resources = data.get('required_resources', [])
    parent_task_id = data.get('parent_task_id')
    parent_token = data.get('parent_token')
    
    # Convert scope to list if string
    if isinstance(scope, str):
        scope = [s.strip() for s in scope.split(' ') if s.strip()]
        
    # Validate client credentials
    if not client_id or not client_secret:
        return jsonify({'error': 'Missing client credentials'}), 400
        
    # Find agent
    agent = Agent.query.get(client_id)
    if not agent or not agent.is_active:
        return jsonify({'error': 'Invalid client credentials or inactive agent'}), 401
        
    # Verify client secret
    if not agent.verify_client_secret(client_secret):
        return jsonify({'error': 'Invalid client credentials'}), 401
    
    # Verify parent token if provided
    parent_token_obj = None
    if parent_token:
        parent_token_obj = verify_token(parent_token)
        if not parent_token_obj:
            return jsonify({'error': 'Invalid parent token'}), 401
            
        # Verify parent task ID if provided
        if parent_task_id and parent_token_obj.task_id != parent_task_id:
            return jsonify({'error': 'Parent token does not match parent task ID'}), 400
            
        # Use parent task ID from token if not explicitly provided
        if not parent_task_id:
            parent_task_id = parent_token_obj.task_id
    
    # Validate requested scope against agent's allowed capabilities
    granted_tools = []
    for tool in required_tools:
        if tool in agent.allowed_tools:
            granted_tools.append(tool)
            
    granted_resources = []
    for resource in required_resources:
        if resource in agent.allowed_resources:
            granted_resources.append(resource)
    
    # If parent token exists, verify scope inheritance
    if parent_token_obj:
        # Verify all requested scopes are subset of parent's scopes
        if not set(scope).issubset(set(parent_token_obj.scope)):
            return jsonify({'error': 'Requested scope exceeds parent token scope'}), 403
            
        # Verify all tools are subset of parent's tools
        if not set(granted_tools).issubset(set(parent_token_obj.granted_tools)):
            return jsonify({'error': 'Requested tools exceed parent token tools'}), 403
            
        # Verify all resources are subset of parent's resources
        if not set(granted_resources).issubset(set(parent_token_obj.granted_resources)):
            return jsonify({'error': 'Requested resources exceed parent token resources'}), 403
    
    # Create token record
    try:
        token_obj, access_token, refresh_token = IssuedToken.create(
            client_id=client_id,
            scope=scope,
            granted_tools=granted_tools,
            granted_resources=granted_resources,
            task_id=task_id,
            task_description=task_description,
            parent_task_id=parent_task_id,
            parent_token_id=parent_token_obj.token_id if parent_token_obj else None,
            scope_inheritance_type='restricted'
        )
        
        # Log token issuance
        log_token_usage(token_obj, 'token_issued', 'success', {
            'grant_type': grant_type,
            'parent_token_id': parent_token_obj.token_id if parent_token_obj else None,
            'requested_tools': required_tools,
            'granted_tools': granted_tools,
            'requested_resources': required_resources,
            'granted_resources': granted_resources,
            'requested_scope': scope
        })
        
        # Return token response
        return jsonify({
            'access_token': access_token,
            'refresh_token': refresh_token,
            'token_type': 'Bearer',
            'expires_in': (token_obj.expires_at - token_obj.issued_at).total_seconds(),
            'scope': ' '.join(scope),
            'task_id': task_id,
            'granted_tools': granted_tools,
            'granted_resources': granted_resources,
            'parent_task_id': parent_task_id,
            'parent_token_id': parent_token_obj.token_id if parent_token_obj else None
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Error issuing token: {str(e)}")
        return jsonify({'error': 'Failed to issue token'}), 500

@oauth_bp.route('/verify', methods=['POST'])
def verify_token_endpoint():
    """Verify a token and its task context."""
    data = request.get_json()
    
    if not data or not data.get('token'):
        return jsonify({'error': 'Missing token'}), 400
        
    token_str = data.get('token')
    task_id = data.get('task_id')
    parent_task_id = data.get('parent_task_id')
    parent_token = data.get('parent_token')
    
    # Verify token
    token = verify_token(token_str)
    if not token:
        return jsonify({
            'is_valid': False,
            'error': 'Invalid or expired token'
        }), 200  # Return 200 with validation info
    
    # Verify task context if provided
    task_context_valid = True
    if task_id and token.task_id != task_id:
        task_context_valid = False
    
    # Verify parent token if provided
    parent_token_obj = None
    parent_valid = True
    scope_inheritance_valid = True
    
    if parent_token:
        parent_token_obj = verify_token(parent_token)
        if not parent_token_obj:
            parent_valid = False
        else:
            # Verify parent task ID
            if parent_task_id and parent_token_obj.task_id != parent_task_id:
                parent_valid = False
                
            # Verify token lineage
            if not verify_task_lineage(token, parent_token=parent_token_obj):
                parent_valid = False
                
            # Verify scope inheritance
            if not verify_scope_inheritance(token, parent_token_obj):
                scope_inheritance_valid = False
    
    # Log verification attempt
    log_token_usage(token, 'token_verification', 'success', {
        'task_id': task_id,
        'parent_task_id': parent_task_id,
        'task_context_valid': task_context_valid,
        'parent_valid': parent_valid,
        'scope_inheritance_valid': scope_inheritance_valid
    })
    
    # Return verification result
    return jsonify({
        'is_valid': token.is_valid(),
        'task_context_valid': task_context_valid,
        'parent_valid': parent_valid,
        'scope_inheritance_valid': scope_inheritance_valid,
        'token_info': token.to_dict()
    }), 200

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
    return jsonify({
        'message': 'Access granted to protected resource',
        'agent': g.current_agent.to_dict(),
        'token': g.token.to_dict()
    }), 200 