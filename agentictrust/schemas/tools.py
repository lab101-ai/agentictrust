from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class CreateToolRequest(BaseModel):
    name: str
    description: Optional[str] = None
    category: Optional[str] = None
    permissions_required: List[str] = Field(default_factory=list)
    input_schema: Dict[str, Any] = Field(default_factory=dict)

class UpdateToolRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    permissions_required: Optional[List[str]] = None
    input_schema: Optional[Dict[str, Any]] = None
