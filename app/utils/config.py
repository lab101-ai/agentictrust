import os
import yaml
from typing import Dict, Any, Optional

def load_config(config_name: str, environment: Optional[str] = None) -> Dict[str, Any]:
    """
    Load configuration from YAML files in the configs directory.
    
    Args:
        config_name: Name of the config file without extension (e.g., 'logging', 'flask')
        environment: Environment to load (development, testing, production)
                     If None, uses the FLASK_ENV environment variable or defaults to 'development'
    
    Returns:
        Dict containing the merged configuration
    """
    if environment is None:
        environment = os.environ.get('FLASK_ENV', 'development')
    
    config_path = os.path.join(os.getcwd(), 'configs', f'{config_name}.yml')
    
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