import os
from datetime import timedelta

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
        from app.utils.config import load_config as yaml_loader
        return yaml_loader(name, environment)