from fastapi import APIRouter, HTTPException, Query, Body
from typing import Any, Dict, Optional
from agentictrust.core import get_tool_engine
from agentictrust.core.policy.opa_client import opa_client
from agentictrust.schemas.tools import CreateToolRequest, UpdateToolRequest

# Create router with prefix and tags
router = APIRouter(prefix="/api/tools", tags=["tools"])
engine = get_tool_engine()

@router.post("", status_code=201)
async def create_tool(data: CreateToolRequest = Body(...)) -> Dict[str, Any]:
    try:
        tool = engine.create_tool_record(
            name=data.name,
            description=data.description,
            category=data.category,
            permissions_required=data.permissions_required,
            parameters=data.input_schema
        )
        tool_obj = engine.get_tool(tool.tool_id)
        # Add OPA sync for new tool
        try:
            opa_client.put_data(f"runtime/tools/{tool.tool_id}", tool_obj)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"OPA sync failed: {e}")
        return {'message': 'Tool created successfully', 'tool': tool_obj}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail='Failed to create tool')

@router.get("")
async def list_tools(
    category: Optional[str] = None,
    is_active: Optional[bool] = None
) -> Dict[str, Any]:
    try:
        tools = engine.list_tools(category=category, is_active=is_active)
        return {'tools': tools}
    except Exception:
        raise HTTPException(status_code=500, detail='Failed to list tools')

@router.get("/{tool_id}")
async def get_tool(tool_id: str) -> Dict[str, Any]:
    try:
        return engine.get_tool(tool_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail='Failed to get tool')

@router.put("/{tool_id}")
async def update_tool(tool_id: str, data: UpdateToolRequest = Body(...)) -> Dict[str, Any]:
    try:
        payload = data.dict(exclude_unset=True)
        # map request field to engine alias
        if 'input_schema' in payload:
            payload['inputSchema'] = payload.pop('input_schema')
        updated = engine.update_tool(tool_id, payload)
        # Add OPA sync for updated tool
        try:
            opa_client.put_data(f"runtime/tools/{tool_id}", updated)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"OPA sync failed: {e}")
        return {'message': 'Tool updated successfully', 'tool': updated}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail='Failed to update tool')

@router.delete("/{tool_id}")
async def delete_tool(tool_id: str) -> Dict[str, Any]:
    try:
        engine.delete_tool(tool_id)
        # Add OPA delete for removed tool
        try:
            opa_client.delete_data(f"runtime/tools/{tool_id}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"OPA delete failed: {e}")
        return {'message': 'Tool deleted successfully'}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail='Failed to delete tool')

@router.post("/{tool_id}/activate")
async def activate_tool(tool_id: str) -> Dict[str, Any]:
    try:
        tool = engine.activate_tool(tool_id)
        # Add OPA sync for activated tool
        try:
            opa_client.put_data(f"runtime/tools/{tool_id}", tool)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"OPA sync failed: {e}")
        return {'message': 'Tool activated successfully', 'tool': tool}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail='Failed to activate tool')

@router.post("/{tool_id}/deactivate")
async def deactivate_tool(tool_id: str) -> Dict[str, Any]:
    try:
        tool = engine.deactivate_tool(tool_id)
        # Add OPA sync for deactivated tool
        try:
            opa_client.put_data(f"runtime/tools/{tool_id}", tool)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"OPA sync failed: {e}")
        return {'message': 'Tool deactivated successfully', 'tool': tool}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail='Failed to deactivate tool')
