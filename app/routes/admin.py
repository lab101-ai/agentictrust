from flask import Blueprint, request, jsonify, current_app
from app.models import Agent, IssuedToken, TaskAuditLog, Tool
from app.utils import token_required
from datetime import datetime

admin_bp = Blueprint('admin', __name__, url_prefix='/api/admin')

@admin_bp.route('/tokens', methods=['GET'])
def list_tokens():
    """List all issued tokens."""
    tokens = IssuedToken.query.all()
    return jsonify({
        'tokens': [token.to_dict() for token in tokens]
    }), 200

@admin_bp.route('/tokens/<token_id>', methods=['GET'])
def get_token(token_id):
    """Get token details by token ID."""
    token = IssuedToken.query.get(token_id)
    if not token:
        return jsonify({'error': 'Token not found'}), 404
        
    include_children = request.args.get('include_children', 'false').lower() == 'true'
    return jsonify(token.to_dict(include_children=include_children)), 200

@admin_bp.route('/tokens/<token_id>/revoke', methods=['POST'])
def revoke_token(token_id):
    """Revoke a token by token ID."""
    token = IssuedToken.query.get(token_id)
    if not token:
        return jsonify({'error': 'Token not found'}), 404
        
    data = request.get_json() or {}
    reason = data.get('reason', 'Administratively revoked')
    
    try:
        token.revoke(reason=reason)
        return jsonify({
            'message': 'Token revoked successfully',
            'token_id': token.token_id,
            'affected_child_tokens': [child.token_id for child in token.child_tokens]
        }), 200
    except Exception as e:
        current_app.logger.error(f"Error revoking token: {str(e)}")
        return jsonify({'error': 'Failed to revoke token'}), 500

@admin_bp.route('/tokens/search', methods=['GET'])
def search_tokens():
    """Search tokens by various criteria."""
    client_id = request.args.get('client_id')
    task_id = request.args.get('task_id')
    parent_task_id = request.args.get('parent_task_id')
    is_valid = request.args.get('is_valid')
    is_revoked = request.args.get('is_revoked')
    
    # Build query
    query = IssuedToken.query
    
    if client_id:
        query = query.filter(IssuedToken.client_id == client_id)
        
    if task_id:
        query = query.filter(IssuedToken.task_id == task_id)
        
    if parent_task_id:
        query = query.filter(IssuedToken.parent_task_id == parent_task_id)
        
    if is_valid is not None:
        is_valid = is_valid.lower() == 'true'
        # Filter for valid tokens (not revoked and not expired)
        if is_valid:
            query = query.filter(
                (IssuedToken.is_revoked == False) & 
                (IssuedToken.expires_at > datetime.utcnow())
            )
        else:
            query = query.filter(
                (IssuedToken.is_revoked == True) | 
                (IssuedToken.expires_at <= datetime.utcnow())
            )
            
    if is_revoked is not None:
        is_revoked = is_revoked.lower() == 'true'
        query = query.filter(IssuedToken.is_revoked == is_revoked)
    
    # Execute query
    tokens = query.all()
    
    return jsonify({
        'tokens': [token.to_dict() for token in tokens]
    }), 200

@admin_bp.route('/audit/logs', methods=['GET'])
def list_audit_logs():
    """List audit logs with optional filtering."""
    client_id = request.args.get('client_id')
    token_id = request.args.get('token_id')
    task_id = request.args.get('task_id')
    event_type = request.args.get('event_type')
    status = request.args.get('status')
    limit = request.args.get('limit', 100, type=int)
    
    # Build query
    query = TaskAuditLog.query
    
    if client_id:
        query = query.filter(TaskAuditLog.client_id == client_id)
        
    if token_id:
        query = query.filter(TaskAuditLog.token_id == token_id)
        
    if task_id:
        query = query.filter(TaskAuditLog.task_id == task_id)
        
    if event_type:
        query = query.filter(TaskAuditLog.event_type == event_type)
        
    if status:
        query = query.filter(TaskAuditLog.status == status)
    
    # Order by timestamp (newest first) and limit results
    logs = query.order_by(TaskAuditLog.timestamp.desc()).limit(limit).all()
    
    return jsonify({
        'logs': [log.to_dict() for log in logs]
    }), 200

@admin_bp.route('/audit/task/<task_id>', methods=['GET'])
def get_task_history(task_id):
    """Get the full history of a specific task."""
    logs = TaskAuditLog.get_task_history(task_id)
    return jsonify({
        'task_id': task_id,
        'history': [log.to_dict() for log in logs]
    }), 200

@admin_bp.route('/audit/task-chain/<task_id>', methods=['GET'])
def get_task_chain(task_id):
    """Get the full chain of related tasks for a specific task."""
    task_chain = TaskAuditLog.get_task_chain(task_id)
    
    # Get details for each task in the chain
    task_details = []
    for task in task_chain:
        logs = TaskAuditLog.get_task_history(task)
        if logs:
            # Get the first log entry for basic info
            first_log = logs[0]
            task_details.append({
                'task_id': task,
                'parent_task_id': first_log.parent_task_id,
                'client_id': first_log.client_id,
                'token_id': first_log.token_id,
                'event_count': len(logs)
            })
    
    return jsonify({
        'root_task_id': task_id,
        'task_chain': task_chain,
        'task_details': task_details
    }), 200

@admin_bp.route('/stats/dashboard', methods=['GET'])
def get_dashboard_stats():
    """Get dashboard statistics."""
    try:
        # Count agents
        agents_count = Agent.query.count()
        
        # Count tools
        tools_count = Tool.query.count()
        
        # Count all tokens
        tokens_count = IssuedToken.query.count()
        
        # Count active tokens (not expired, not revoked)
        active_tokens_count = IssuedToken.query.filter(
            (IssuedToken.is_revoked == False) & 
            (IssuedToken.expires_at > datetime.utcnow())
        ).count()
        
        return jsonify({
            'agents_count': agents_count,
            'tools_count': tools_count,
            'tokens_count': tokens_count,
            'active_tokens_count': active_tokens_count
        }), 200
    except Exception as e:
        current_app.logger.error(f"Error fetching dashboard stats: {str(e)}")
        return jsonify({'error': 'Failed to fetch dashboard statistics'}), 500 