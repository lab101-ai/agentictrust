from fastapi import APIRouter, HTTPException, Body
from typing import Dict, List, Any, Optional
from agentictrust.core import get_agent_engine
from agentictrust.core.policy.opa_client import opa_client

# Create router with prefix and tags
router = APIRouter(prefix="/api/agents", tags=["agents"])
engine = get_agent_engine()

@router.post("/register", status_code=201)
async def register_agent(data: dict = Body(...)) -> Dict[str, Any]:
    try:
        result = engine.register_agent(
            agent_name=data.get('agent_name'),
            description=data.get('description'),
            max_scope_level=data.get('max_scope_level', 'restricted'),
            tool_ids=data.get('tool_ids', [])
        )
        # Add OPA sync for new agent
        agent = result.get('agent')
        if agent:
            try:
                opa_client.put_data(f"runtime/agents/{agent['client_id']}", agent)
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"OPA sync failed: {e}")
        return {'message': 'Agent registered successfully', **result}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to register agent")

@router.post("/activate")
async def activate_agent(data: dict = Body(...)) -> Dict[str, Any]:
    try:
        result = engine.activate_agent(data.get('registration_token'))
        return {'message': 'Agent activated successfully', **result}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to activate agent")

@router.get("/list")
async def list_agents() -> Dict[str, Any]:
    try:
        agents = engine.list_agents()
        return {'agents': agents}
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to list agents")

@router.get("/{client_id}")
async def get_agent(client_id: str) -> Dict[str, Any]:
    try:
        return engine.get_agent(client_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to get agent")

@router.delete("/{client_id}")
async def delete_agent(client_id: str) -> Dict[str, Any]:
    try:
        engine.delete_agent(client_id)
        # Add OPA delete for removed agent
        try:
            opa_client.delete_data(f"runtime/agents/{client_id}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"OPA delete failed: {e}")
        return {'message': 'Agent deleted successfully'}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to delete agent")

@router.get("/me")
async def get_current_agent():  # -> Dict[str, Any]
    """Get the current agent's details (using token authentication)."""
    # TODO: Implement auth dependency using the get_current_agent dependency
    # This will need to be updated once the FastAPI auth system is implemented
    # For now, returning not implemented to maintain API compatibility
    raise HTTPException(status_code=501, detail="Not implemented")

@router.get("/{client_id}/tools")
async def get_agent_tools(client_id: str) -> Dict[str, Any]:
    try:
        tools = engine.get_agent_tools(client_id)
        return {'tools': tools}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to get agent tools")

@router.post("/{client_id}/tools/{tool_id}")
async def add_tool_to_agent(client_id: str, tool_id: str) -> Dict[str, Any]:
    try:
        engine.add_tool_to_agent(client_id, tool_id)
        return {'message': 'Tool added to agent successfully'}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to add tool to agent")

@router.delete("/{client_id}/tools/{tool_id}")
async def remove_tool_from_agent(client_id: str, tool_id: str) -> Dict[str, Any]:
    try:
        engine.remove_tool_from_agent(client_id, tool_id)
        return {'message': 'Tool removed from agent successfully'}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to remove tool from agent")

@router.put("/{client_id}")
async def update_agent(client_id: str, data: dict = Body(...)) -> Dict[str, Any]:
    try:
        result = engine.update_agent(client_id, data)
        # Add OPA sync for updated agent
        agent = result.get('agent')
        if agent:
            try:
                opa_client.put_data(f"runtime/agents/{client_id}", agent)
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"OPA sync failed: {e}")
        return {'message': 'Agent updated successfully', **result}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to update agent")
