from pydantic import BaseModel
from typing import Optional, List, Dict, Any

class CreateToolRequest(BaseModel):
    name: str
    description: Optional[str] = None
    category: Optional[str] = None
    permissions_required: Optional[List[str]] = []
    input_schema: Optional[Dict[str, Any]] = {}

class UpdateToolRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    permissions_required: Optional[List[str]] = None
    input_schema: Optional[Dict[str, Any]] = None
