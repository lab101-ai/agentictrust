import os
import json
import yaml
from app.models import db
from sqlalchemy import inspect
from app.utils.logger import logger

def initialize_database():
    """Create database tables if they don't exist."""
    # Check if tables exist, create them if they don't
    inspector = inspect(db.engine)
    if not inspector.has_table('scopes'):
        # Create all tables that don't exist yet
        db.create_all()
        logger.info("Created necessary database tables")
        return True
    return False

def load_initial_data():
    """Load initial data from configuration files."""
    # Check if we need to create tables first
    tables_created = initialize_database()
    
    # Load all known configuration types
    config_types = [
        'scopes',        # OAuth scopes
        'oauth',         # OAuth server settings
        'agents',        # Default agents
        'tools',         # Default tools
        'permissions'    # Permission mappings
    ]
    
    # If tables already existed, we might still want to load configs
    # but skip the data population
    skip_data = not tables_created
    
    # Try to load each config file
    for config_type in config_types:
        try:
            load_config_data(config_type, skip_data=skip_data)
        except Exception as e:
            logger.error(f"Error loading {config_type} data: {str(e)}")

def load_config_data(data_type, skip_data=False):
    """Load configuration data for a specific data type."""
    # Look for configuration files in several possible locations
    possible_config_paths = [
        f'configs/{data_type}.yml',
        f'configs/{data_type}.yaml',
        f'configs/{data_type}.json',
        f'../configs/{data_type}.yml',
        f'../configs/{data_type}.yaml',
        f'../configs/{data_type}.json',
    ]
    
    config_data = None
    config_path = None
    
    # Try to find and load a config file
    for path in possible_config_paths:
        if os.path.exists(path):
            config_path = path
            with open(path, 'r') as f:
                if path.endswith('.json'):
                    config_data = json.load(f)
                else:  # YAML file
                    config_data = yaml.safe_load(f)
            break
    
    if not config_data:
        logger.warning(f"No configuration file found for {data_type}")
        return
    
    logger.info(f"Loading {data_type} configuration from {config_path}")
    
    # Skip data population if requested
    if skip_data:
        logger.info(f"Skipping {data_type} data population, only loading configuration")
        return config_data
        
    # Import data-specific loading function
    if data_type == 'scopes':
        from app.models import Scope
        load_scopes(config_data)
    elif data_type == 'agents':
        from app.models import Agent
        load_agents(config_data)
    elif data_type == 'tools':
        from app.models import Tool
        load_tools(config_data)
    elif data_type == 'oauth':
        load_oauth_settings(config_data)
    elif data_type == 'permissions':
        load_permissions(config_data)
        
    return config_data

def load_scopes(config_data):
    """Load scope data from configuration."""
    from app.models import Scope
    
    if not config_data or 'scopes' not in config_data:
        logger.warning("No scope data found in configuration")
        return
    
    scopes_data = config_data['scopes']
    created_count = 0
    
    for scope_data in scopes_data:
        # Create new scope
        scope = Scope(
            name=scope_data["name"],
            description=scope_data.get("description", ""),
            category=scope_data.get("category", "read"),
            is_default=scope_data.get("is_default", False),
            is_sensitive=scope_data.get("is_sensitive", False),
            requires_approval=scope_data.get("requires_approval", False)
        )
        db.session.add(scope)
        created_count += 1
    
    if created_count > 0:
        try:
            db.session.commit()
            logger.info(f"Created {created_count} scopes from configuration")
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating scopes: {str(e)}")

def load_agents(config_data):
    """Load agent data from configuration."""
    from app.models import Agent
    
    if not config_data or 'agents' not in config_data:
        logger.warning("No agent data found in configuration")
        return
    
    agents_data = config_data['agents']
    created_count = 0
    
    for agent_data in agents_data:
        if not agent_data.get("agent_name"):
            logger.warning("Skipping agent without a name")
            continue
            
        # Check if agent already exists
        existing_agent = Agent.query.filter_by(agent_name=agent_data["agent_name"]).first()
        if existing_agent:
            logger.info(f"Agent {agent_data['agent_name']} already exists, skipping")
            continue
            
        try:
            # Use the Agent.create method which handles client secret generation
            Agent.create(
                agent_name=agent_data["agent_name"],
                description=agent_data.get("description"),
                max_scope_level=agent_data.get("max_scope_level", "restricted")
            )
            created_count += 1
        except Exception as e:
            logger.error(f"Error creating agent {agent_data['agent_name']}: {str(e)}")
    
    if created_count > 0:
        logger.info(f"Created {created_count} agents from configuration")

def load_tools(config_data):
    """Load tool data from configuration."""
    from app.models import Tool
    
    if not config_data or 'tools' not in config_data:
        logger.warning("No tool data found in configuration")
        return
    
    tools_data = config_data['tools']
    created_count = 0
    
    for tool_data in tools_data:
        if not tool_data.get("name"):
            logger.warning("Skipping tool without a name")
            continue
            
        # Check if tool already exists
        existing_tool = Tool.query.filter_by(name=tool_data["name"]).first()
        if existing_tool:
            logger.info(f"Tool {tool_data['name']} already exists, skipping")
            continue
            
        try:
            Tool.create(
                name=tool_data["name"],
                description=tool_data.get("description"),
                category=tool_data.get("category"),
                permissions_required=tool_data.get("permissions_required", []),
                parameters=tool_data.get("parameters", [])
            )
            created_count += 1
        except Exception as e:
            logger.error(f"Error creating tool {tool_data['name']}: {str(e)}")
    
    if created_count > 0:
        logger.info(f"Created {created_count} tools from configuration")

def load_oauth_settings(config_data):
    """Load OAuth server settings from configuration."""
    if not config_data or 'oauth_settings' not in config_data:
        logger.warning("No OAuth settings found in configuration")
        return
    
    oauth_settings = config_data['oauth_settings']
    
    # Store settings in environment variables or app config
    from flask import current_app
    
    for key, value in oauth_settings.items():
        if hasattr(current_app.config, key):
            current_app.config[key] = value
            logger.debug(f"Updated OAuth setting: {key}")
    
    logger.info("Applied OAuth server settings from configuration")

def load_permissions(config_data):
    """Load permission mappings from configuration."""
    if not config_data or 'permissions' not in config_data:
        logger.warning("No permission mappings found in configuration")
        return
    
    # This function can be used to set up relationships between 
    # agents, tools, and scopes based on configuration
    from app.models import Agent, Tool, Scope
    
    permissions_data = config_data['permissions']
    
    # Process agent-tool mappings
    if 'agent_tools' in permissions_data:
        for mapping in permissions_data['agent_tools']:
            agent_name = mapping.get('agent_name')
            tool_names = mapping.get('tools', [])
            
            if not agent_name or not tool_names:
                continue
                
            agent = Agent.query.filter_by(agent_name=agent_name).first()
            if not agent:
                logger.warning(f"Agent {agent_name} not found for tool mapping")
                continue
                
            for tool_name in tool_names:
                tool = Tool.query.filter_by(name=tool_name).first()
                if not tool:
                    logger.warning(f"Tool {tool_name} not found for agent {agent_name}")
                    continue
                    
                if tool not in agent.tools:
                    agent.tools.append(tool)
                    logger.debug(f"Mapped tool {tool_name} to agent {agent_name}")
    
    # Process agent-scope mappings (for default scopes)
    if 'agent_scopes' in permissions_data:
        # This would be implemented if you have an association table for agent-scope relationships
        pass
    
    # Process tool-scope mappings (for required scopes)
    if 'tool_scopes' in permissions_data:
        # This would be implemented if you have an association table for tool-scope relationships
        pass
    
    try:
        db.session.commit()
        logger.info("Applied permission mappings from configuration")
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error applying permission mappings: {str(e)}")