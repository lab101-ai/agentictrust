from sqlalchemy import Column, String, ForeignKey, JSON, and_
from sqlalchemy.orm import Query
from agentictrust.db.models.audit.audit_base import BaseAuditLog
from agentictrust.db import db_session
from agentictrust.utils.logger import logger
from typing import List, Dict, Any, Optional
import json

class DelegationAuditLog(BaseAuditLog):
    """Audit log rows for delegation-grant lifecycle and delegated token issuance."""
    __tablename__ = 'delegation_audit_logs'

    grant_id = Column(String(36), ForeignKey('delegation_grants.grant_id'), nullable=True)
    principal_id = Column(String(36), nullable=True)
    delegate_id = Column(String(36), nullable=True)
    token_id = Column(String(36), nullable=True, index=True)
    action = Column(String(50), nullable=False)  # created | revoked | token_issued | validation_failed
    scope = Column(JSON, nullable=True)
    details = Column(JSON, nullable=True)

    @classmethod
    def log_event(cls, *, grant_id: str | None, action: str, principal_id: str | None = None,
                  delegate_id: str | None = None, token_id: str | None = None,
                  scope: list[str] | None = None, details: dict | None = None):
        try:
            row = cls(
                grant_id=grant_id,
                principal_id=principal_id,
                delegate_id=delegate_id,
                token_id=token_id,
                action=action,
                scope=scope or [],
                details=details or {},
            )
            db_session.add(row)
            db_session.commit()
            return row
        except Exception as e:
            logger.error(f"Failed to insert DelegationAuditLog: {e}")
            db_session.rollback()
            return None

    def to_dict(self):
        base = super().to_dict()
        base.update({
            'grant_id': self.grant_id,
            'principal_id': self.principal_id,
            'delegate_id': self.delegate_id,
            'token_id': self.token_id,
            'action': self.action,
            'scope': self.scope,
            'details': self.details or {},
        })
        return base
        
    @classmethod
    def get_delegation_chain(cls, token_id: str) -> Dict[str, Any]:
        """Get the delegation chain for a token."""
        try:
            from agentictrust.db.models import IssuedToken
            token = IssuedToken.query.get(token_id)
            if not token:
                logger.error(f"Token not found: {token_id}")
                return {}
            
            chain = []
            if token.delegation_chain:
                try:
                    if isinstance(token.delegation_chain, str):
                        chain = json.loads(token.delegation_chain)
                    else:
                        chain = token.delegation_chain
                except Exception as e:
                    logger.error(f"Error parsing delegation chain for token {token_id}: {str(e)}")
            
            logs = cls.query.filter_by(token_id=token_id).all()
            
            response = {
                'token_id': token_id,
                'delegator_sub': token.delegator_sub,
                'delegation_purpose': token.delegation_purpose,
                'delegation_chain': chain,
                'audit_logs': [log.to_dict() for log in logs]
            }
            
            return response
        except Exception as e:
            logger.error(f"Error getting delegation chain: {str(e)}")
            return {}
    
    @classmethod
    def get_user_delegation_activity(cls, user_id: str) -> Dict[str, Any]:
        """Get delegation activity for a user."""
        try:
            principal_logs = cls.query.filter_by(principal_id=user_id).all()
            
            delegate_logs = cls.query.filter_by(delegate_id=user_id).all()
            
            from agentictrust.db.models import IssuedToken
            tokens = IssuedToken.query.filter_by(delegator_sub=user_id).all()
            
            response = {
                'user_id': user_id,
                'delegations_as_principal': [log.to_dict() for log in principal_logs],
                'delegations_as_delegate': [log.to_dict() for log in delegate_logs],
                'delegated_tokens': [
                    {
                        'token_id': token.token_id,
                        'client_id': token.client_id,
                        'issued_at': token.issued_at.isoformat() if token.issued_at else None,
                        'expires_at': token.expires_at.isoformat() if token.expires_at else None,
                        'is_revoked': token.is_revoked,
                        'scopes': token.scopes.split(' ') if isinstance(token.scopes, str) else token.scopes,
                        'task_id': token.task_id,
                        'task_description': token.task_description
                    }
                    for token in tokens
                ]
            }
            
            return response
        except Exception as e:
            logger.error(f"Error getting user delegation activity: {str(e)}")
            return {'user_id': user_id, 'error': str(e)}     