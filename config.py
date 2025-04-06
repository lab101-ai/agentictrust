import os
from datetime import timedelta

class Config:
    # Basic Flask configuration
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    DEBUG = os.environ.get('DEBUG') == 'True'
    
    # Database configuration
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///agentictrust.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Token settings
    ACCESS_TOKEN_EXPIRY = timedelta(hours=1)  # Default 1 hour for access tokens
    REFRESH_TOKEN_EXPIRY = timedelta(days=30)  # Default 30 days for refresh tokens
    
    # OAuth settings
    DEFAULT_SCOPES = ['read:basic'] 