from fastapi import APIRouter, HTTPException, Body
from typing import Dict, Any
from app.core import get_user_engine

router = APIRouter(prefix="/api/users", tags=["users"])
engine = get_user_engine()

@router.post("", status_code=201)
async def create_user(data: dict = Body(...)) -> Dict[str, Any]:
    try:
        user = engine.create_user(
            username=data.get("username"),
            email=data.get("email"),
            full_name=data.get("full_name"),
            hashed_password=data.get("hashed_password"),
            is_external=data.get("is_external", False),
            department=data.get("department"),
            job_title=data.get("job_title"),
            level=data.get("level"),
            scopes=data.get("scopes", []),
            policies=data.get("policies", []),
        )
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
        return {"message": "User updated successfully", "user": updated}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to update user")

@router.delete("/{user_id}")
async def delete_user(user_id: str) -> Dict[str, Any]:
    try:
        engine.delete_user(user_id)
        return {"message": "User deleted successfully"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to delete user")
