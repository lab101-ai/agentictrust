"""
Pydantic models for Admin API request validation.
"""
from pydantic import BaseModel, Field
from typing import Optional

class AuditLogsQuery(BaseModel):
    page: int = Field(1, description="Page number, starting from 1")
    page_size: int = Field(20, description="Number of items per page")
    agent_id: Optional[str] = Field(None, description="Filter logs by agent ID")
    token_id: Optional[str] = Field(None, description="Filter logs by token ID")
    task_id: Optional[str] = Field(None, description="Filter logs by task ID")
    event_type: Optional[str] = Field(None, description="Filter logs by event type")
    status: Optional[str] = Field(None, description="Filter logs by status")
    limit: int = Field(100, description="Maximum number of logs to return")

class ListTokensQuery(BaseModel):
    page: int = Field(1, description="Page number, starting from 1")
    page_size: int = Field(20, description="Number of items per page")
    agent_id: Optional[str] = Field(None, description="Filter tokens by agent ID")
    include_expired: bool = Field(False, description="Include expired tokens")
    include_revoked: bool = Field(True, description="Include revoked tokens")
    task_id: Optional[str] = Field(None, description="Filter tokens by task ID")
    parent_task_id: Optional[str] = Field(None, description="Filter tokens by parent task ID")
    is_valid: Optional[bool] = Field(None, description="Filter tokens by validity")

class RevokeTokenRequest(BaseModel):
    reason: Optional[str] = Field(None, description="Reason for token revocation")

class TaskChainQuery(BaseModel):
    include_events: bool = Field(True, description="Include detailed events for each task")
