import os
import json
import yaml
from agentictrust.db import db_session
from sqlalchemy import inspect
from agentictrust.utils.logger import logger

def initialize_database():
    """Create database tables if they don't exist."""
    # In the new FastAPI structure, we don't need to check tables this way
    # The init_db() function in agentictrust.db.__init__ is already called from main.py
    # This is just a placeholder for compatibility
    from agentictrust.db import engine
    
    # Check if tables exist, create them if they don't
    inspector = inspect(engine)
    if not inspector.has_table('scopes'):
        # Tables will be created by init_db() in main.py
        logger.info("Database tables need to be created")
        return True
    
    logger.info("Database tables already exist")
    return False

def load_initial_data():
    """Load initial data from configuration files."""
    # Check if tables exist
    initialize_database()
    
    # Load all known configuration types (scopes moved to engine initialization)
    config_types = [
        'agents',        # Default agents
        'tools',         # Default tools
        'users'          # Predefined platform users
    ]
    
    # Always attempt to load the data, regardless of whether tables existed
    # In FastAPI migration, we want to make sure data is loaded
    skip_data = False
    
    # Try to load each config file
    for config_type in config_types:
        try:
            load_config_data(config_type, skip_data=skip_data)
        except Exception as e:
            logger.error(f"Error loading {config_type} data: {str(e)}")

def load_config_data(data_type, skip_data=False):
    """Load configuration data for a specific data type."""
    import pathlib
    
    # Find the project root directory
    app_dir = pathlib.Path(__file__).parent.parent  # utils -> app
    project_root = app_dir.parent  # app -> project_root
    config_dir = project_root / 'data'
    
    # Look for configuration files with absolute paths
    possible_config_paths = [
        config_dir / f'{data_type}.yml',
        config_dir / f'{data_type}.yaml',
        config_dir / f'{data_type}.json',
    ]
    
    config_data = None
    config_path = None
    
    # Try to find and load a config file
    for path in possible_config_paths:
        if path.exists():
            config_path = path
            with open(path, 'r') as f:
                if str(path).endswith('.json'):
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
    if data_type == 'agents':
        from agentictrust.db.models import Agent
        load_agents(config_data)
    elif data_type == 'tools':
        from agentictrust.db.models import Tool
        load_tools(config_data)
    elif data_type == 'users':
        load_users(config_data)
        
    return config_data

def load_agents(config_data):
    """Load agent data from configuration."""
    from agentictrust.db.models import Agent
    
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
    from agentictrust.db.models import Tool
    
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

def load_users(config_data):
    """Load predefined user data from configuration."""
    from agentictrust.db.models import User

    if not config_data or 'users' not in config_data:
        logger.warning("No user data found in configuration")
        return

    users_data = config_data['users']
    created_count = 0

    for user_data in users_data:
        username = user_data.get('username')
        email = user_data.get('email')
        if not username or not email:
            logger.warning("Skipping user entry missing username/email")
            continue

        # Check if user already exists
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            logger.info(f"User {username} already exists, skipping")
            continue

        try:
            attrs = {}
            if 'partner' in user_data:
                attrs['partner'] = user_data['partner']

            # Resolve scope and policy names to IDs if necessary
            scope_ids = []
            from agentictrust.db.models.scope import Scope
            for s in user_data.get('scopes', []) or []:
                if len(s) == 36 and "-" in s:
                    scope_ids.append(s)
                else:
                    scope_obj = Scope.query.filter_by(name=s).first()
                    if scope_obj:
                        scope_ids.append(scope_obj.scope_id)

            User.create(
                username=username,
                email=email,
                full_name=user_data.get('full_name'),
                hashed_password=user_data.get('hashed_password'),
                is_external=user_data.get('is_external', False),
                department=user_data.get('department'),
                job_title=user_data.get('job_title'),
                level=user_data.get('level'),
                attributes=attrs if attrs else None,
                scope_ids=scope_ids if scope_ids else None,
            )
            created_count += 1
        except Exception as e:
            logger.error(f"Error creating user {username}: {str(e)}")

    if created_count:
        logger.info(f"Created {created_count} users from configuration")