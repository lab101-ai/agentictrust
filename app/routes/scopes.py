from flask import Blueprint, request, jsonify, current_app
from app.models import Scope
from app.utils import token_required
from app import db

scopes_bp = Blueprint('scopes', __name__, url_prefix='/api/scopes')

@scopes_bp.route('', methods=['GET'])
def list_scopes():
    """List all registered scopes."""
    category = request.args.get('category')
    is_active = request.args.get('is_active')
    is_sensitive = request.args.get('is_sensitive')
    
    # Build query
    query = Scope.query
    
    if category:
        query = query.filter(Scope.category == category)
        
    if is_active is not None:
        is_active = is_active.lower() == 'true'
        query = query.filter(Scope.is_active == is_active)
        
    if is_sensitive is not None:
        is_sensitive = is_sensitive.lower() == 'true'
        query = query.filter(Scope.is_sensitive == is_sensitive)
    
    scopes = query.all()
    return jsonify({
        'scopes': [scope.to_dict() for scope in scopes]
    }), 200

@scopes_bp.route('/<scope_id>', methods=['GET'])
def get_scope(scope_id):
    """Get scope details by scope ID."""
    scope = Scope.query.get(scope_id)
    if not scope:
        return jsonify({'error': 'Scope not found'}), 404
    
    return jsonify(scope.to_dict()), 200

@scopes_bp.route('', methods=['POST'])
@token_required
def create_scope():
    """Create a new scope."""
    data = request.get_json()
    
    # Validate required fields
    if not data.get('name'):
        return jsonify({'error': 'Scope name is required'}), 400
        
    # Check if scope with the same name already exists
    existing_scope = Scope.query.filter(Scope.name == data.get('name')).first()
    if existing_scope:
        return jsonify({'error': 'A scope with this name already exists'}), 409
    
    try:
        scope = Scope.create(
            name=data.get('name'),
            description=data.get('description'),
            category=data.get('category', 'read'),
            is_sensitive=data.get('is_sensitive', False),
            requires_approval=data.get('requires_approval', False),
            is_default=data.get('is_default', False)
        )
        return jsonify(scope.to_dict()), 201
    except Exception as e:
        current_app.logger.error(f"Error creating scope: {str(e)}")
        return jsonify({'error': 'Failed to create scope'}), 500

@scopes_bp.route('/<scope_id>', methods=['PUT'])
@token_required
def update_scope(scope_id):
    """Update an existing scope."""
    scope = Scope.query.get(scope_id)
    if not scope:
        return jsonify({'error': 'Scope not found'}), 404
    
    data = request.get_json()
    
    # Check if updating to a name that already exists
    if data.get('name') and data.get('name') != scope.name:
        existing_scope = Scope.query.filter(Scope.name == data.get('name')).first()
        if existing_scope:
            return jsonify({'error': 'A scope with this name already exists'}), 409
    
    try:
        scope.update(
            name=data.get('name', scope.name),
            description=data.get('description', scope.description),
            category=data.get('category', scope.category),
            is_sensitive=data.get('is_sensitive', scope.is_sensitive),
            requires_approval=data.get('requires_approval', scope.requires_approval),
            is_default=data.get('is_default', scope.is_default),
            is_active=data.get('is_active', scope.is_active)
        )
        return jsonify(scope.to_dict()), 200
    except Exception as e:
        current_app.logger.error(f"Error updating scope: {str(e)}")
        return jsonify({'error': 'Failed to update scope'}), 500

@scopes_bp.route('/<scope_id>', methods=['DELETE'])
@token_required
def delete_scope(scope_id):
    """Delete a scope."""
    scope = Scope.query.get(scope_id)
    if not scope:
        return jsonify({'error': 'Scope not found'}), 404
    
    try:
        db.session.delete(scope)
        db.session.commit()
        return jsonify({'message': 'Scope deleted successfully'}), 200
    except Exception as e:
        current_app.logger.error(f"Error deleting scope: {str(e)}")
        return jsonify({'error': 'Failed to delete scope'}), 500

@scopes_bp.route('/default', methods=['GET'])
def get_default_scopes():
    """Get all default scopes."""
    default_scopes = Scope.query.filter(Scope.is_default == True, Scope.is_active == True).all()
    return jsonify({
        'scopes': [scope.to_dict() for scope in default_scopes]
    }), 200

@scopes_bp.route('/categories', methods=['GET'])
def get_scope_categories():
    """Get all scope categories."""
    categories = db.session.query(Scope.category).distinct().all()
    return jsonify({
        'categories': [category[0] for category in categories]
    }), 200
