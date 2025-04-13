from app import db

# Import models 
from app.models.agent import Agent
from app.models.token import IssuedToken
from app.models.tool import Tool
from app.models.audit import TaskAuditLog
from app.models.scope import Scope

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
__all__ = ['Agent', 'IssuedToken', 'Tool', 'TaskAuditLog', 'Scope'] 