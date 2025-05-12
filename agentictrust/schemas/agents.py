from pydantic import BaseModel
from typing import Optional, List

class RegisterAgentRequest(BaseModel):
    agent_name: str
    description: Optional[str] = None
    max_scope_level: Optional[str] = 'restricted'
    tool_ids: Optional[List[str]] = []

class ActivateAgentRequest(BaseModel):
    registration_token: str

class UpdateAgentRequest(BaseModel):
    agent_name: Optional[str] = None
    description: Optional[str] = None
    max_scope_level: Optional[str] = None
    tool_ids: Optional[List[str]] = None
