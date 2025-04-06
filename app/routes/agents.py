from flask import Blueprint, request, jsonify, current_app
from app.models import Agent, Tool
from app.utils import token_required

agents_bp = Blueprint('agents', __name__, url_prefix='/api/agents')

@agents_bp.route('/register', methods=['POST'])
def register_agent():
    """Register a new agent."""
    data = request.get_json()
    
    # Validate required fields
    if not data or not data.get('agent_name'):
        return jsonify({'error': 'Missing required fields'}), 400
        
    # Extract agent details
    agent_name = data.get('agent_name')
    description = data.get('description')
    allowed_resources = data.get('allowed_resources', [])
    max_scope_level = data.get('max_scope_level', 'restricted')
    tool_ids = data.get('tool_ids', [])  # Tools are now selected by ID
    
    # Create agent
    try:
        agent, client_secret = Agent.create(
            agent_name=agent_name,
            description=description,
            allowed_resources=allowed_resources,
            max_scope_level=max_scope_level
        )
        
        # Associate tools with the agent
        if tool_ids:
            for tool_id in tool_ids:
                tool = Tool.query.get(tool_id)
                if tool:
                    agent.add_tool(tool)
        
        # Return agent details and credentials
        return jsonify({
            'message': 'Agent registered successfully',
            'agent': agent.to_dict(),
            'credentials': {
                'client_id': agent.client_id,
                'client_secret': client_secret,  # Only returned once
                'registration_token': agent.registration_token  # Used to activate the agent
            }
        }), 201
    except Exception as e:
        current_app.logger.error(f"Error registering agent: {str(e)}")
        return jsonify({'error': 'Failed to register agent'}), 500

@agents_bp.route('/activate', methods=['POST'])
def activate_agent():
    """Activate a registered agent using the registration token."""
    data = request.get_json()
    
    # Validate required fields
    if not data or not data.get('registration_token'):
        return jsonify({'error': 'Missing registration token'}), 400
        
    registration_token = data.get('registration_token')
    
    # Find agent by registration token
    agent = Agent.query.filter_by(registration_token=registration_token).first()
    if not agent:
        return jsonify({'error': 'Invalid registration token'}), 404
        
    # Activate agent
    try:
        agent.activate()
        return jsonify({
            'message': 'Agent activated successfully',
            'agent': agent.to_dict()
        }), 200
    except Exception as e:
        current_app.logger.error(f"Error activating agent: {str(e)}")
        return jsonify({'error': 'Failed to activate agent'}), 500

@agents_bp.route('/list', methods=['GET'])
def list_agents():
    """List all registered agents."""
    agents = Agent.query.all()
    return jsonify({
        'agents': [agent.to_dict() for agent in agents]
    }), 200

@agents_bp.route('/<client_id>', methods=['GET'])
def get_agent(client_id):
    """Get agent details by client ID."""
    agent = Agent.query.get(client_id)
    if not agent:
        return jsonify({'error': 'Agent not found'}), 404
        
    return jsonify(agent.to_dict()), 200

@agents_bp.route('/<client_id>', methods=['DELETE'])
def delete_agent(client_id):
    """Delete an agent by client ID."""
    agent = Agent.query.get(client_id)
    if not agent:
        return jsonify({'error': 'Agent not found'}), 404
        
    try:
        # Delete agent (cascade will delete tokens and audit logs)
        from app import db
        db.session.delete(agent)
        db.session.commit()
        
        return jsonify({'message': 'Agent deleted successfully'}), 200
    except Exception as e:
        current_app.logger.error(f"Error deleting agent: {str(e)}")
        return jsonify({'error': 'Failed to delete agent'}), 500

@agents_bp.route('/me', methods=['GET'])
@token_required
def get_current_agent():
    """Get the current agent's details (using token authentication)."""
    from flask import g
    return jsonify(g.current_agent.to_dict()), 200

@agents_bp.route('/<client_id>/tools', methods=['GET'])
def get_agent_tools(client_id):
    """Get all tools assigned to an agent."""
    agent = Agent.query.get(client_id)
    if not agent:
        return jsonify({'error': 'Agent not found'}), 404
        
    return jsonify({
        'tools': [tool.to_dict() for tool in agent.tools]
    }), 200

@agents_bp.route('/<client_id>/tools/<tool_id>', methods=['POST'])
def add_tool_to_agent(client_id, tool_id):
    """Add a tool to an agent."""
    agent = Agent.query.get(client_id)
    if not agent:
        return jsonify({'error': 'Agent not found'}), 404
        
    tool = Tool.query.get(tool_id)
    if not tool:
        return jsonify({'error': 'Tool not found'}), 404
        
    try:
        agent.add_tool(tool)
        return jsonify({
            'message': 'Tool added to agent successfully',
            'agent': agent.to_dict()
        }), 200
    except Exception as e:
        current_app.logger.error(f"Error adding tool to agent: {str(e)}")
        return jsonify({'error': 'Failed to add tool to agent'}), 500

@agents_bp.route('/<client_id>/tools/<tool_id>', methods=['DELETE'])
def remove_tool_from_agent(client_id, tool_id):
    """Remove a tool from an agent."""
    agent = Agent.query.get(client_id)
    if not agent:
        return jsonify({'error': 'Agent not found'}), 404
        
    tool = Tool.query.get(tool_id)
    if not tool:
        return jsonify({'error': 'Tool not found'}), 404
        
    try:
        agent.remove_tool(tool)
        return jsonify({
            'message': 'Tool removed from agent successfully',
            'agent': agent.to_dict()
        }), 200
    except Exception as e:
        current_app.logger.error(f"Error removing tool from agent: {str(e)}")
        return jsonify({'error': 'Failed to remove tool from agent'}), 500 