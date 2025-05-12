from pydantic import BaseModel
from typing import Optional, List

class CreateUserRequest(BaseModel):
    username: str
    email: str
    full_name: Optional[str] = None
    hashed_password: str
    is_external: Optional[bool] = False
    department: Optional[str] = None
    job_title: Optional[str] = None
    level: Optional[str] = None
    scopes: Optional[List[str]] = []

class UpdateUserRequest(BaseModel):
    username: Optional[str] = None
    email: Optional[str] = None
    full_name: Optional[str] = None
    hashed_password: Optional[str] = None
    is_external: Optional[bool] = None
    department: Optional[str] = None
    job_title: Optional[str] = None
    level: Optional[str] = None
    scopes: Optional[List[str]] = None
