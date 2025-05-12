"""
Core admin management logic abstracted for reuse in routers and services
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
from sqlalchemy.sql import func
from agentictrust.db.models import Agent, IssuedToken, TaskAuditLog, Tool, User
from agentictrust.db.models.audit import PolicyAuditLog, ScopeAuditLog
from agentictrust.db.models.audit.token_audit import TokenAuditLog
from agentictrust.utils.logger import logger

def dashboard_stats() -> Dict[str, Any]:
    """Get admin dashboard statistics (counts and recent activity)."""
    agent_count = Agent.query.count()
    token_count = IssuedToken.query.count()
    tool_count = Tool.query.count()
    active_tokens = IssuedToken.query.filter(
        IssuedToken.is_revoked == False,
        IssuedToken.expires_at > func.now()
    ).count()
    recent_logs = TaskAuditLog.query.order_by(
        TaskAuditLog.timestamp.desc()
    ).limit(10).all()
    return {
        'stats': {
            'agents': agent_count,
            'tokens': token_count,
            'active_tokens': active_tokens,
            'tools': tool_count
        },
        'recent_activity': [log.to_dict() for log in recent_logs]
    }


def get_dashboard_stats() -> Dict[str, Any]:
    """Get legacy dashboard statistics."""
    agents_count = Agent.query.count()
    tools_count = Tool.query.count()
    tokens_count = IssuedToken.query.count()
    active_tokens_count = IssuedToken.query.filter(
        (IssuedToken.is_revoked == False) &
        (IssuedToken.expires_at > datetime.utcnow())
    ).count()
    # Additional metrics
    users_count = User.query.count()
    return {
        'agents_count': agents_count,
        'tools_count': tools_count,
        'tokens_count': tokens_count,
        'active_tokens_count': active_tokens_count,
        'users_count': users_count,
    }


def audit_logs(
    page: int = 1,
    page_size: int = 20,
    agent_id: Optional[str] = None,
    token_id: Optional[str] = None,
    task_id: Optional[str] = None,
    event_type: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 100
) -> Dict[str, Any]:
    """Get audit logs with pagination and filtering."""
    query = TaskAuditLog.query
    if agent_id:
        from agentictrust.db.models import Agent as _Agent
        query = query.join(IssuedToken).join(_Agent).filter(_Agent.client_id == agent_id)
    if token_id:
        query = query.filter(TaskAuditLog.token_id == token_id)
    if task_id:
        query = query.filter(TaskAuditLog.task_id == task_id)
    if event_type:
        query = query.filter(TaskAuditLog.event_type == event_type)
    if status:
        query = query.filter(TaskAuditLog.status == status)
    total = query.count()
    logs = query.order_by(TaskAuditLog.timestamp.desc())\
               .offset((page - 1) * page_size)\
               .limit(min(page_size, limit))\
               .all()
    pages = (total + page_size - 1) // page_size
    return {
        'logs': [log.to_dict() for log in logs],
        'pagination': {
            'page': page,
            'page_size': page_size,
            'total': total,
            'pages': pages
        }
    }


def list_tokens(
    page: int = 1,
    page_size: int = 20,
    agent_id: Optional[str] = None,
    include_expired: bool = False,
    include_revoked: bool = True,
    task_id: Optional[str] = None,
    parent_task_id: Optional[str] = None,
    is_valid: Optional[bool] = None
) -> Dict[str, Any]:
    """List tokens with pagination and filtering."""
    logger.debug(f"Entering list_tokens: page={page}, page_size={page_size}, agent_id={agent_id}, include_expired={include_expired}, include_revoked={include_revoked}, task_id={task_id}, parent_task_id={parent_task_id}, is_valid={is_valid}")
    try:
        query = IssuedToken.query
        logger.debug("Initial query created.")
        if agent_id:
            query = query.filter(IssuedToken.client_id == agent_id)
        if task_id:
            query = query.filter(IssuedToken.task_id == task_id)
        if parent_task_id:
            query = query.filter(IssuedToken.parent_task_id == parent_task_id)
        if is_valid is not None:
            if is_valid:
                query = query.filter(
                    (IssuedToken.is_revoked == False) &
                    (IssuedToken.expires_at > datetime.utcnow())
                )
            else:
                query = query.filter(
                    (IssuedToken.is_revoked == True) |
                    (IssuedToken.expires_at <= datetime.utcnow())
                )
        if not include_expired:
            query = query.filter(IssuedToken.expires_at > datetime.utcnow())
        if not include_revoked:
            query = query.filter(IssuedToken.is_revoked == False)
            logger.debug("Filtering out revoked tokens")

        logger.debug("Counting total tokens...")
        total = query.count()
        logger.debug(f"Total tokens found: {total}")

        logger.debug("Executing query to fetch tokens...")
        tokens = query.order_by(IssuedToken.issued_at.desc())\
                       .offset((page - 1) * page_size)\
                       .limit(page_size)\
                       .all()
        logger.debug(f"Fetched {len(tokens)} tokens for page {page}.")

        token_dicts = []
        logger.debug("Serializing tokens to dictionary...")
        for token in tokens:
            try:
                token_dict = token.to_dict()
                token_dicts.append(token_dict)
            except Exception as e_serialize:
                logger.error(f"Error serializing token {getattr(token, 'token_id', 'UNKNOWN_ID')}: {e_serialize}", exc_info=True)
                # Optionally skip this token or add placeholder
                token_dicts.append({'error': 'Serialization failed', 'token_id': getattr(token, 'token_id', 'UNKNOWN_ID')})

        pages = (total + page_size - 1) // page_size
        logger.debug("Serialization complete. Returning token list.")
        return {
            'tokens': token_dicts, 
            'pagination': {
                'page': page,
                'page_size': page_size,
                'total': total,
                'pages': pages
            }
        }
    except Exception as e_core: 
        logger.error(f"Error during list_tokens execution: {e_core}", exc_info=True)
        raise 


def get_token(token_id: str, include_children: bool = False) -> Dict[str, Any]:
    """Get token details by ID."""
    if not token_id:
        raise ValueError("token_id is required")
    token = IssuedToken.query.get(token_id)
    if not token:
        raise ValueError("Token not found")
    return token.to_dict(include_children=include_children)


def revoke_token(token_id: str, reason: Optional[str] = None) -> Dict[str, Any]:
    """Revoke a token (and optionally its children) via OAuthEngine."""
    from agentictrust.core.registry import get_oauth_engine
    engine = get_oauth_engine()
    try:
        engine.revoke(token_id, revoke_children=True)
        return {
            "message": "Token revoked successfully (including children)",
            "token_id": token_id,
        }
    except ValueError as ve:
        raise
    except Exception as e:
        logger.error(f"Admin revoke_token error: {e}", exc_info=True)
        raise


def introspect_token(access_token: str) -> Dict[str, Any]:
    """Wrapper around OAuthEngine.introspect for admin tooling."""
    from agentictrust.core.registry import get_oauth_engine
    engine = get_oauth_engine()
    tok = engine.introspect(access_token)
    if not tok or not tok.is_valid():
        return {"active": False}
    return tok.to_dict()


def get_task_history(task_id: str) -> Dict[str, Any]:
    """Get the full history of a specific task."""
    logs = TaskAuditLog.get_task_history(task_id)
    return {
        'task_id': task_id,
        'history': [log.to_dict() for log in logs]
    }


def get_task_chain(task_id: str, include_events: bool = True) -> Dict[str, Any]:
    """
    Get the full chain of related tasks.
    For each task in the chain, return a dict with all audit logs (policy, scope, token, events) as flat entries,
    merged and sorted by timestamp, and with a 'type' field indicating the log type.
    """
    chain = TaskAuditLog.get_task_chain(task_id)
    task_details: List[List[Dict[str, Any]]] = []

    for cid in chain:
        # Fetch all logs for this task
        logs = TaskAuditLog.get_task_history(cid) if include_events else []
        policy_logs = PolicyAuditLog.query.filter(
            PolicyAuditLog.task_id == cid
        ).order_by(PolicyAuditLog.timestamp).all()
        scope_logs = ScopeAuditLog.query.filter(
            ScopeAuditLog.task_id == cid
        ).order_by(ScopeAuditLog.timestamp).all()
        token_logs = TokenAuditLog.query.filter(
            TokenAuditLog.task_id == cid
        ).order_by(TokenAuditLog.timestamp).all()

        # Merge all logs into a single list with type annotation
        combined = []
        if include_events:
            combined.extend([{'type': 'task', **log.to_dict(), 'timestamp': log.timestamp} for log in logs])
        combined.extend([{'type': 'policy', **pl.to_dict(), 'timestamp': pl.timestamp} for pl in policy_logs])
        combined.extend([{'type': 'scope', **sl.to_dict(), 'timestamp': sl.timestamp} for sl in scope_logs])
        combined.extend([{'type': 'token', **tl.to_dict(), 'timestamp': tl.timestamp} for tl in token_logs])

        # Sort all logs by timestamp
        combined.sort(key=lambda entry: entry['timestamp'] if entry['timestamp'] else '')

        # Remove the 'timestamp' key from each entry if not needed in the output
        for entry in combined:
            if isinstance(entry.get('timestamp'), (str, type(None))):
                continue
            entry['timestamp'] = entry['timestamp'].isoformat() if entry['timestamp'] else None

        task_details.append(combined)

    return {
        'root_task_id': task_id,
        'task_chain': chain,
        'task_details': task_details
    }
