from fastapi import FastAPI, Body, Depends, HTTPException, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sdk.client import AgenticTrustClient
import os
import sys
from fastapi.responses import JSONResponse
import importlib

# Add project root to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

app = FastAPI()

# OAuth server URL for token introspection
OAUTH_SERVER_URL = os.getenv("OAUTH_SERVER_URL", "http://localhost:8000")
trust_client = AgenticTrustClient(api_base=OAUTH_SERVER_URL)
auth_scheme = HTTPBearer()

# --- Load tool implementations --------------------------------------------------
# Ensure demo.support_tools is imported so decorators run
support_tools_mod = importlib.import_module("demo.support_tools".replace("/", ".")) if "demo.support_tools" not in sys.modules else sys.modules["demo.support_tools"]

# Build mapping: tool name -> callable
TOOLS_BY_NAME = {
    fn._tool_metadata["name"]: fn
    for fn in support_tools_mod.__dict__.values()
    if callable(fn) and hasattr(fn, "_tool_metadata")
}

def _call_tool(tool_name: str, params: dict):
    tool_fn = TOOLS_BY_NAME.get(tool_name)
    if not tool_fn:
        raise HTTPException(status_code=404, detail=f"Tool '{tool_name}' not found")
    try:
        return tool_fn(**params)
    except TypeError as te:
        # Parameter mismatch
        raise HTTPException(status_code=400, detail=str(te))

async def authorize_tool(tool_name: str, credentials: HTTPAuthorizationCredentials = Depends(auth_scheme)):
    if not credentials or not credentials.credentials:
        raise HTTPException(status_code=401, detail="Missing or invalid authorization credentials")
    token = credentials.credentials
    try:
        print(f"[SUPPORT_SERVER] Verifying access to tool: {tool_name} with token: {token[:10]}...")
        # Try introspecting token to permit if this tool is granted directly
        introspect_resp = trust_client.token.introspect(token)
        granted = introspect_resp.get('granted_tools') or introspect_resp.get('granted_tools', [])
        if isinstance(granted, list) and tool_name in granted:
            print(f"[SUPPORT_SERVER] Tool '{tool_name}' is granted on token via introspection, allowing access")
            return credentials
        # Enforce tool-level authorisation using OAuth verify-tool-access endpoint
        trust_client.token.verify_tool_access(tool_name=tool_name, token=token)
    except Exception as e:
        print(f"[SUPPORT_SERVER] Access denied for tool '{tool_name}': {str(e)}")
        raise HTTPException(status_code=403, detail=f"Access denied for tool '{tool_name}'") 
    return credentials

@app.get("/{tool_name}", dependencies=[Depends(authorize_tool)])
async def support_read(request: Request, tool_name: str):
    """Handle GET requests for support tool by dispatching to implementation."""
    params = dict(request.query_params)
    result = _call_tool(tool_name, params)
    return JSONResponse(content=result)

@app.post("/{tool_name}", dependencies=[Depends(authorize_tool)])
async def support_write(tool_name: str, body: dict = Body(...)):
    """Handle POST requests for support tool by dispatching to implementation."""
    result = _call_tool(tool_name, body or {})
    return JSONResponse(content=result)

@app.get("/{tool_name}/admin", dependencies=[Depends(authorize_tool)])
async def support_admin_read(tool_name: str, issue: str = None, action: str = None):
    """Handle GET requests for admin support tool."""
    return {"tool": tool_name, "admin": True, "issue": issue, "action": action}

@app.post("/{tool_name}/admin", dependencies=[Depends(authorize_tool)])
async def support_admin_write(tool_name: str, body: dict = Body(...)):
    """Handle POST requests for admin support tool."""
    return {"tool": tool_name, "admin": True, "body": body}
