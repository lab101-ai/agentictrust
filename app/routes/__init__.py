from app.routes.agents import agents_bp
from app.routes.oauth import oauth_bp
from app.routes.admin import admin_bp
from app.routes.tools import tools_bp
from app.routes.scopes import scopes_bp

__all__ = ['agents_bp', 'oauth_bp', 'admin_bp', 'tools_bp', 'scopes_bp'] 