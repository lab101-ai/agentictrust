import os
import yaml
from typing import Dict, Any, Optional
import pathlib

def load_config(config_name: str, environment: Optional[str] = None) -> Dict[str, Any]:
    """
    Load configuration from YAML files in the configs directory.
    
    Args:
        config_name: Name of the config file without extension (e.g., 'logging', 'api')
        environment: Environment to load (development, testing, production)
                     If None, uses the APP_ENV environment variable or defaults to 'development'
    
    Returns:
        Dict containing the merged configuration
    """
    if environment is None:
        environment = os.environ.get('APP_ENV', 'development')
    
    # Find the project root directory (parent directory of the app package)
    app_dir = pathlib.Path(__file__).parent.parent  # utils -> app
    project_root = app_dir.parent  # app -> project_root
    
    # Use absolute path to configs directory
    config_path = os.path.join(project_root, 'configs', f'{config_name}.yml')
    
    # For debugging
    print(f"Looking for config file at: {config_path}")
    
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    
    with open(config_path, 'r') as file:
        config_data = yaml.safe_load(file)
    
    # Start with default configuration
    result = {}
    if 'default' in config_data:
        result.update(config_data['default'])
    
    # Override with environment-specific configuration
    if 'environments' in config_data and environment in config_data['environments']:
        result.update(config_data['environments'][environment])
    
    # Add other sections if they exist (e.g., 'oauth', 'loggers')
    for section in config_data:
        if section not in ('default', 'environments', 'version'):
            result[section] = config_data[section]
    
    return result 