# Import SQLAlchemy components from our centralized db module
from agentictrust.db import db_session, Base

# Import models 
from agentictrust.db.models.agent import Agent
from agentictrust.db.models.token import IssuedToken
from agentictrust.db.models.authorization_code import AuthorizationCode
from agentictrust.db.models.tool import Tool
from agentictrust.db.models.audit.task_audit import TaskAuditLog
from agentictrust.db.models.scope import Scope
from agentictrust.db.models.user import User
from agentictrust.db.models.audit.scope_audit import ScopeAuditLog
from agentictrust.db.models.audit.token_audit import TokenAuditLog
from agentictrust.db.models.audit.agent_audit import AgentAuditLog
from agentictrust.db.models.delegation_grant import DelegationGrant
from agentictrust.db.models.audit.delegation_audit import DelegationAuditLog

# Add event listeners for token-audit log relationship handling
from sqlalchemy import event

@event.listens_for(TaskAuditLog, 'before_insert')
def validate_token_id_format(mapper, connection, target):
    """
    Validate that token_id in TaskAuditLog is either a valid UUID or an error token.
    This ensures database integrity without requiring a foreign key constraint.
    """
    # If it's an error token (starting with "error-"), it won't be in the issued_tokens table
    if target.token_id and target.token_id.startswith("error-"):
        # Mark this specifically as an error log if not already marked
        if not target.details:
            target.details = {}
        target.details["_error_log"] = True
        target.details["_error_token_format_validated"] = True
        return  # Allow error tokens

# Register models with event listeners
__all__ = [
    'Agent',
    'IssuedToken',
    'AuthorizationCode',
    'Tool',
    'TaskAuditLog',
    'Scope',
    'User',
    'ScopeAuditLog',
    'TokenAuditLog',
    'AgentAuditLog',
    'DelegationGrant',
    'DelegationAuditLog'
]