from fastapi import APIRouter, HTTPException, Body, Request, Response, Depends
from typing import Dict, Any, List
from agentictrust.core import get_user_engine
from agentictrust.core.policy.opa_client import opa_client
from agentictrust.schemas.users import TokenResponse, UserProfile
from agentictrust.core.users.engine import UserEngine
from agentictrust.db.models import User
from agentictrust.utils.logger import logger
import json
import uuid
from datetime import datetime

router = APIRouter(prefix="/api/users", tags=["users"])
engine = get_user_engine()

@router.post("", status_code=201)
async def create_user(data: dict = Body(...)) -> Dict[str, Any]:
    try:
        if not data.get("username") or not data.get("email"):
            raise ValueError("Username and email are required")
            
        user = engine.create_user(
            username=str(data.get("username")),
            email=str(data.get("email")),
            full_name=data.get("full_name"),
            hashed_password=data.get("hashed_password"),
            is_external=data.get("is_external", False),
            department=data.get("department"),
            job_title=data.get("job_title"),
            level=data.get("level"),
            scopes=data.get("scopes", []),
        )
        # Add OPA sync for new user
        try:
            opa_client.put_data(f"runtime/users/{user['user_id']}", user)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"OPA sync failed: {e}")
        return {"message": "User created successfully", "user": user}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to create user")

@router.get("")
async def list_users() -> Dict[str, Any]:
    try:
        users = engine.list_users()
        return {"users": users}
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to list users")

@router.get("/{user_id}")
async def get_user(user_id: str) -> Dict[str, Any]:
    try:
        return engine.get_user(user_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to get user")

@router.put("/{user_id}")
async def update_user(user_id: str, data: dict = Body(...)) -> Dict[str, Any]:
    try:
        updated = engine.update_user(user_id, data)
        # Add OPA sync for updated user
        try:
            opa_client.put_data(f"runtime/users/{user_id}", updated)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"OPA sync failed: {e}")
        return {"message": "User updated successfully", "user": updated}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to update user")

@router.delete("/{user_id}")
async def delete_user(user_id: str) -> Dict[str, Any]:
    try:
        engine.delete_user(user_id)
        # Add OPA delete for removed user
        try:
            opa_client.delete_data(f"runtime/users/{user_id}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"OPA delete failed: {e}")
        return {"message": "User deleted successfully"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to delete user")



@router.get("/profile")
async def get_user_profile(request: Request):
    """Get user profile using token."""
    try:
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            raise HTTPException(status_code=401, detail="Invalid authentication credentials")
        
        token = auth_header.split(' ')[1]
        
        from agentictrust.core.oauth.utils import verify_token
        token_obj = verify_token(token)
        
        if not token_obj:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        user_id = token_obj.delegator_sub
        user = User.get_by_id(user_id)
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        return UserProfile(
            user_id=user.user_id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            department=user.department,
            job_title=user.job_title,
            is_external=user.is_external,
            scopes=[scope.scope_id for scope in user.scopes],
            picture=None
        )
    except Exception as e:
        logger.error(f"Error getting user profile: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
