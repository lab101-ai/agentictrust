from fastapi import APIRouter, HTTPException
from agentictrust.db.models.audit.delegation_audit import DelegationAuditLog
from agentictrust.db.models import IssuedToken
from agentictrust.utils.logger import logger
from agentictrust.db import db_session
from typing import List, Dict, Any, Optional
from sqlalchemy import func
import json

router = APIRouter(prefix="/api/audit", tags=["audit"])

@router.get("/delegation/{token_id}/chain")
async def get_delegation_chain(token_id: str):
    """Get the delegation chain for a token."""
    try:
        chain = DelegationAuditLog.get_delegation_chain(token_id)
        
        if not chain:
            raise HTTPException(status_code=404, detail="Token not found or has no delegation chain")
        
        return chain
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting delegation chain: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/delegation/user/{user_id}")
async def get_user_delegation_activity(user_id: str):
    """Get delegation activity for a user."""
    try:
        activity = DelegationAuditLog.get_user_delegation_activity(user_id)
        
        if 'error' in activity:
            raise HTTPException(status_code=500, detail=activity['error'])
        
        return activity
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user delegation activity: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/delegation/stats")
async def get_delegation_stats():
    """Get delegation statistics."""
    try:
        total_delegations = DelegationAuditLog.query.filter_by(action="token_issued").count()
        
        active_tokens = IssuedToken.query.filter(
            IssuedToken.delegator_sub.isnot(None),
            IssuedToken.is_revoked == False
        ).count()
        
        revoked_tokens = IssuedToken.query.filter(
            IssuedToken.delegator_sub.isnot(None),
            IssuedToken.is_revoked == True
        ).count()
        
        from sqlalchemy import func
        top_delegators_query = db_session.query(
            DelegationAuditLog.principal_id,
            func.count(DelegationAuditLog.principal_id).label('count')
        ).filter(
            DelegationAuditLog.action == "token_issued",
            DelegationAuditLog.principal_id.isnot(None)
        ).group_by(
            DelegationAuditLog.principal_id
        ).order_by(
            func.count(DelegationAuditLog.principal_id).desc()
        ).limit(5)
        
        top_delegators = [
            {'user_id': row.principal_id, 'delegation_count': row.count}
            for row in top_delegators_query
        ]
        
        top_delegates_query = db_session.query(
            DelegationAuditLog.delegate_id,
            func.count(DelegationAuditLog.delegate_id).label('count')
        ).filter(
            DelegationAuditLog.action == "token_issued",
            DelegationAuditLog.delegate_id.isnot(None)
        ).group_by(
            DelegationAuditLog.delegate_id
        ).order_by(
            func.count(DelegationAuditLog.delegate_id).desc()
        ).limit(5)
        
        top_delegates = [
            {'agent_id': row.delegate_id, 'delegation_count': row.count}
            for row in top_delegates_query
        ]
        
        return {
            'total_delegations': total_delegations,
            'active_delegated_tokens': active_tokens,
            'revoked_delegated_tokens': revoked_tokens,
            'top_delegators': top_delegators,
            'top_delegates': top_delegates
        }
    except Exception as e:
        logger.error(f"Error getting delegation stats: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
