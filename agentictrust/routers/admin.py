from fastapi import APIRouter, HTTPException, Query, Body
from typing import Dict, Any, List, Optional
from agentictrust.core.admin import (
    dashboard_stats as core_dashboard_stats,
    get_dashboard_stats as core_get_dashboard_stats,
    audit_logs as core_audit_logs,
    list_tokens as core_list_tokens,
    get_token as core_get_token,
    revoke_token as core_revoke_token,
    introspect_token as core_introspect_token,
    get_task_history as core_get_task_history,
    get_task_chain as core_get_task_chain
)
from sqlalchemy.exc import SQLAlchemyError
from agentictrust.utils.logger import logger

# Create router with prefix and tags
router = APIRouter(prefix="/api/admin", tags=["admin"])

# TODO: Add authentication requirement for admin endpoints

@router.get("/dashboard")
async def dashboard_stats() -> Dict[str, Any]:
    """Get admin dashboard statistics."""
    try:
        return core_dashboard_stats()
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to get dashboard statistics")

@router.get("/stats/dashboard")
async def get_dashboard_stats() -> Dict[str, Any]:
    """Get dashboard statistics (legacy endpoint)."""
    try:
        return core_get_dashboard_stats()
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to fetch dashboard statistics")

@router.get("/audit/logs")
async def audit_logs(
    page: Optional[int] = Query(1, description="Page number, starting from 1"),
    page_size: Optional[int] = Query(20, description="Number of items per page"),
    agent_id: Optional[str] = Query(None, description="Filter logs by agent ID"),
    token_id: Optional[str] = Query(None, description="Filter logs by token ID"),
    task_id: Optional[str] = Query(None, description="Filter logs by task ID"),
    event_type: Optional[str] = Query(None, description="Filter logs by event type"),
    status: Optional[str] = Query(None, description="Filter logs by status"),
    limit: Optional[int] = Query(100, description="Maximum number of logs to return")
) -> Dict[str, Any]:
    """Get audit logs with pagination and filtering."""
    try:
        return core_audit_logs(page, page_size, agent_id, token_id, task_id, event_type, status, limit)
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to get audit logs")

@router.get("/tokens")
async def list_tokens(
    page: Optional[int] = Query(1, description="Page number, starting from 1"),
    page_size: Optional[int] = Query(20, description="Number of items per page"),
    agent_id: Optional[str] = Query(None, description="Filter tokens by agent ID"),
    include_expired: Optional[bool] = Query(False, description="Include expired tokens"),
    include_revoked: Optional[bool] = Query(True, description="Include revoked tokens"),
    task_id: Optional[str] = Query(None, description="Filter tokens by task ID"),
    parent_task_id: Optional[str] = Query(None, description="Filter tokens by parent task ID"),
    is_valid: Optional[bool] = Query(None, description="Filter tokens by validity")
) -> Dict[str, Any]:
    """List tokens with pagination and filtering."""
    logger.info(f"Received request for /tokens: page={page}, page_size={page_size}, agent_id={agent_id}, include_expired={include_expired}, include_revoked={include_revoked}, is_valid={is_valid}")
    try:
        result = core_list_tokens(
            page=page,
            page_size=page_size,
            agent_id=agent_id,
            include_expired=include_expired,
            include_revoked=include_revoked,
            task_id=task_id,
            parent_task_id=parent_task_id,
            is_valid=is_valid
        )
        logger.info(f"Successfully listed tokens. Page: {page}, Count: {len(result.get('tokens', []))}")
        return result
    except SQLAlchemyError as db_err:
        logger.error(f"Database error during token listing: {db_err}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Database error: {db_err}")
    except AttributeError as attr_err:
        logger.error(f"Attribute error during token listing: {attr_err}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal processing error (Attribute): {attr_err}")
    except Exception as e:
        logger.error(f"Unexpected error listing tokens: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to list tokens due to an unexpected error.")

@router.get("/tokens/{token_id}")
async def get_token(
    token_id: str,
    include_children: bool = Query(False, description="Include child tokens in response")
) -> Dict[str, Any]:
    """Get token details by token ID."""
    try:
        return core_get_token(token_id, include_children)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to get token")

@router.post("/tokens/{token_id}/revoke")
async def revoke_token(token_id: str, data: Optional[Dict[str, Any]] = Body(None)) -> Dict[str, Any]:
    """Revoke a token by token ID."""
    try:
        return core_revoke_token(token_id, data.get("reason") if data else None)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to revoke token")

@router.get("/audit/task/{task_id}")
async def get_task_history(task_id: str) -> Dict[str, Any]:
    """Get the full history of a specific task."""
    try:
        return core_get_task_history(task_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to get task history")

@router.get("/audit/task-chain/{task_id}")
async def get_task_chain(
    task_id: str,
    include_events: bool = Query(True, description="Include detailed events for each task")
) -> Dict[str, Any]:
    """Get the full chain of related tasks for a specific task."""
    try:
        return core_get_task_chain(task_id, include_events)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to get task chain")

# ---------------------------------------------------------------------------
# New helper to introspect tokens via OAuthEngine
# ---------------------------------------------------------------------------

@router.post("/tokens/introspect")
async def introspect_token(body: Dict[str, Any] = Body(...)):
    token = body.get("token")
    if not token:
        raise HTTPException(status_code=400, detail="token is required")
    try:
        return core_introspect_token(token)
    except Exception as e:
        logger.error(f"Introspect error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to introspect token")
