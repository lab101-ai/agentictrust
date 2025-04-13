from flask import Blueprint, request, jsonify, current_app
from app.models import Tool
from app.utils import token_required

tools_bp = Blueprint('tools', __name__, url_prefix='/api/tools')

@tools_bp.route('', methods=['GET'])
def list_tools():
    """List all registered tools."""
    category = request.args.get('category')
    is_active = request.args.get('is_active')
    
    # Build query
    query = Tool.query
    
    if category:
        query = query.filter(Tool.category == category)
        
    if is_active is not None:
        is_active = is_active.lower() == 'true'
        query = query.filter(Tool.is_active == is_active)
    
    tools = query.all()
    tool_dicts = []
    for tool in tools:
        tool_dict = tool.to_dict()
        # Alias parameters as inputSchema for response
        tool_dict['inputSchema'] = tool_dict.pop('parameters')
        tool_dicts.append(tool_dict)
    
    return jsonify({
        'tools': tool_dicts
    }), 200

@tools_bp.route('/<tool_id>', methods=['GET'])
def get_tool(tool_id):
    """Get tool details by tool ID."""
    tool = Tool.query.get(tool_id)
    if not tool:
        return jsonify({'error': 'Tool not found'}), 404
    
    tool_dict = tool.to_dict()
    # Alias parameters as inputSchema for response
    tool_dict['inputSchema'] = tool_dict.pop('parameters')
    
    return jsonify(tool_dict), 200

@tools_bp.route('', methods=['POST'])
def create_tool():
    """Register a new tool."""
    data = request.get_json()
    
    # Validate required fields
    if not data or not data.get('name'):
        return jsonify({'error': 'Missing required fields'}), 400
        
    # Check if tool with this name already exists
    existing_tool = Tool.query.filter_by(name=data.get('name')).first()
    if existing_tool:
        return jsonify({'error': 'Tool with this name already exists'}), 409
        
    # Extract tool details
    name = data.get('name')
    description = data.get('description')
    category = data.get('category')
    permissions_required = data.get('permissions_required', [])
    
    # Support both 'parameters' and 'inputSchema' fields, with 'inputSchema' taking precedence
    parameters = data.get('inputSchema', data.get('parameters', []))
    
    # Create tool
    try:
        tool = Tool.create(
            name=name,
            description=description,
            category=category,
            permissions_required=permissions_required,
            parameters=parameters
        )
        
        tool_dict = tool.to_dict()
        # Alias parameters as inputSchema for response
        tool_dict['inputSchema'] = tool_dict.pop('parameters')
        
        return jsonify({
            'message': 'Tool registered successfully',
            'tool': tool_dict
        }), 201
    except Exception as e:
        current_app.logger.error(f"Error registering tool: {str(e)}")
        return jsonify({'error': 'Failed to register tool'}), 500

@tools_bp.route('/<tool_id>', methods=['PUT'])
def update_tool(tool_id):
    """Update an existing tool."""
    tool = Tool.query.get(tool_id)
    if not tool:
        return jsonify({'error': 'Tool not found'}), 404
        
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No update data provided'}), 400
        
    # Check name uniqueness if being updated
    if 'name' in data and data['name'] != tool.name:
        existing_tool = Tool.query.filter_by(name=data['name']).first()
        if existing_tool:
            return jsonify({'error': 'Tool with this name already exists'}), 409
    
    # Handle inputSchema alias for parameters
    if 'inputSchema' in data:
        data['parameters'] = data.pop('inputSchema')
    
    # Update fields
    try:
        tool.update(**data)
        tool_dict = tool.to_dict()
        # Alias parameters as inputSchema for response
        tool_dict['inputSchema'] = tool_dict.pop('parameters')
        
        return jsonify({
            'message': 'Tool updated successfully',
            'tool': tool_dict
        }), 200
    except Exception as e:
        current_app.logger.error(f"Error updating tool: {str(e)}")
        return jsonify({'error': 'Failed to update tool'}), 500

@tools_bp.route('/<tool_id>', methods=['DELETE'])
def delete_tool(tool_id):
    """Delete a tool by tool ID."""
    tool = Tool.query.get(tool_id)
    if not tool:
        return jsonify({'error': 'Tool not found'}), 404
        
    try:
        # Delete tool
        from app import db
        db.session.delete(tool)
        db.session.commit()
        
        return jsonify({'message': 'Tool deleted successfully'}), 200
    except Exception as e:
        current_app.logger.error(f"Error deleting tool: {str(e)}")
        return jsonify({'error': 'Failed to delete tool'}), 500

@tools_bp.route('/<tool_id>/activate', methods=['POST'])
def activate_tool(tool_id):
    """Activate a tool."""
    tool = Tool.query.get(tool_id)
    if not tool:
        return jsonify({'error': 'Tool not found'}), 404
        
    try:
        tool.update(is_active=True)
        tool_dict = tool.to_dict()
        # Alias parameters as inputSchema for response
        tool_dict['inputSchema'] = tool_dict.pop('parameters')
        
        return jsonify({
            'message': 'Tool activated successfully',
            'tool': tool_dict
        }), 200
    except Exception as e:
        current_app.logger.error(f"Error activating tool: {str(e)}")
        return jsonify({'error': 'Failed to activate tool'}), 500

@tools_bp.route('/<tool_id>/deactivate', methods=['POST'])
def deactivate_tool(tool_id):
    """Deactivate a tool."""
    tool = Tool.query.get(tool_id)
    if not tool:
        return jsonify({'error': 'Tool not found'}), 404
        
    try:
        tool.update(is_active=False)
        tool_dict = tool.to_dict()
        # Alias parameters as inputSchema for response
        tool_dict['inputSchema'] = tool_dict.pop('parameters')
        
        return jsonify({
            'message': 'Tool deactivated successfully',
            'tool': tool_dict
        }), 200
    except Exception as e:
        current_app.logger.error(f"Error deactivating tool: {str(e)}")
        return jsonify({'error': 'Failed to deactivate tool'}), 500 