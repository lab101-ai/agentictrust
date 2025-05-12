import os
from datetime import timedelta
import pathlib
import yaml

class Config:
    # Basic Flask configuration
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    DEBUG = os.environ.get('DEBUG') == 'True'
    
    # Ensure local database directory exists
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
    db_dir = os.path.join(base_dir, '.agentictrust', 'db')
    os.makedirs(db_dir, exist_ok=True)
    
    # Database configuration
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or f"sqlite:///{os.path.join(db_dir, 'agentictrust.db')}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Token settings
    ACCESS_TOKEN_EXPIRY = timedelta(minutes=3)  # Default 3 minutes for access tokens
    REFRESH_TOKEN_EXPIRY = timedelta(days=7)  # Default 7 days for refresh tokens
    
    # OAuth settings
    DEFAULT_SCOPES = ['read:basic']

    # Server settings
    HOST = os.environ.get("HOST", "127.0.0.1")
    PORT = int(os.environ.get("PORT", 5001))
    # OIDC Discovery and Key Management
    ISSUER = os.environ.get("OIDC_ISSUER", f"http://{HOST}:{PORT}")
    KEY_DIR = os.environ.get("OIDC_KEY_DIR", os.path.join(base_dir, '.agentictrust', 'keys'))
    PRIVATE_KEY_FILENAME = os.environ.get("OIDC_PRIVATE_KEY_FILENAME", 'private.pem')
    PUBLIC_KEY_FILENAME = os.environ.get("OIDC_PUBLIC_KEY_FILENAME", 'public.pem')
    JWKS_KID = os.environ.get("OIDC_JWKS_KID", 'agentictrust-key')
    # Allowed client IDs for system_job launch_reason
    SYSTEM_CLIENT_IDS = os.environ.get("SYSTEM_CLIENT_IDS", "").split(",")

    # CORS settings
    CORS_ORIGINS = os.environ.get("CORS_ORIGINS", "*").split(",")

    # Scope Expansion Policy
    SCOPE_EXPANSION_POLICY = "standard"

    # OPA integration settings
    # Feature flag to enable/disable OPA policy enforcement
    ENABLE_OPA_POLICIES = os.environ.get('ENABLE_OPA_POLICIES', 'False') == 'True'
    # OPA server connection details and policy path
    OPA_HOST = os.environ.get('OPA_HOST', 'http://localhost')
    OPA_PORT = int(os.environ.get('OPA_PORT', 8181))
    OPA_POLICY_PATH = os.environ.get('OPA_POLICY_PATH', 'agentictrust/authz/allow')

    @staticmethod
    def load_yaml(name, environment=None):
        """Load a YAML config by name using the util loader"""
        if environment is None:
            environment = os.environ.get('APP_ENV', 'development')
        
        # Find the project root directory (parent directory of the app package)
        app_dir = pathlib.Path(__file__).parent.parent  # utils -> app
        project_root = app_dir.parent  # app -> project_root
        
        # Use absolute path to configs directory
        config_path = os.path.join(project_root, 'configs', f'{name}.yml')
        
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