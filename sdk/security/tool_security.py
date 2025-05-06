"""
Security decorators for Tools.

This implementation is migrated from demo/tool_security.py so that external
code can import directly from sdk.security.tool_security.  Logic is unchanged
except we removed demo-specific sys.path manipulation.
"""

import inspect
from typing import Optional, List, Dict, Any, Callable, get_type_hints
from .task_context import task_context

from sdk.client import AgenticTrustClient

# ---------------------------------------------------------------------------
# Internal registry of decorated tools
# ---------------------------------------------------------------------------

_REGISTERED_TOOLS: Dict[str, Callable] = {}

# ---------------------------------------------------------------------------
# Decorator
# ---------------------------------------------------------------------------

def secure_tool(
    func: Callable | None = None,
    *,
    name: Optional[str] = None,
    description: Optional[str] = None,
    category: Optional[str] = None,
    permissions_required: Optional[List[str]] = None,
    auto_register: bool = False,
    client: Optional[AgenticTrustClient] = None,
):
    """Decorator that marks a plain Python function as a *secure tool* and –
    optionally – auto-registers it with an AgenticTrust server.

    Usage examples
    --------------
    >>> @secure_tool
    ... def get_weather(city: str):
    ...     ...

    >>> @secure_tool(name="calculate_mortgage", description="Calculate payments")
    ... def calc(principal: float, rate: float, years: int) -> float:
    ...     ...
    """

    def decorator(fn: Callable):
        tool_name = name or fn.__name__
        tool_desc = description or (fn.__doc__ or f"Tool for {tool_name}")

        # Build JSON-schema input definition from type hints / signature
        sig = inspect.signature(fn)
        type_hints = get_type_hints(fn)
        properties: Dict[str, Dict[str, str]] = {}
        required: List[str] = []

        def _map_type(py_type):
            if py_type in (int, float):
                return "number"
            if py_type is bool:
                return "boolean"
            if py_type in (list, List):
                return "array"
            if py_type in (dict, Dict):
                return "object"
            return "string"

        for name_, param in sig.parameters.items():
            if name_ in ("self", "cls"):
                continue
            schema_type = _map_type(type_hints.get(name_, str))
            properties[name_] = {"type": schema_type, "description": f"Parameter {name_}"}
            if param.default is inspect.Parameter.empty:
                required.append(name_)

        input_schema: Dict[str, Any] = {"type": "object", "properties": properties}
        if required:
            input_schema["required"] = required

        fn._tool_metadata = {
            "name": tool_name,
            "description": tool_desc,
            "category": category,
            "permissions_required": permissions_required or [],
            "input_schema": input_schema,
        }

        _REGISTERED_TOOLS[tool_name] = fn

        if auto_register:
            if client is None:
                print(
                    f"WARNING: auto_register=True but no client provided for tool '{tool_name}'. "
                    "It will not be registered."
                )
            else:
                register_tool_with_client(client, fn)

        # ---------------- runtime wrapper for child-token lifecycle ----------------
        async_def = inspect.iscoroutinefunction(fn)

        def _needs_token(param_name: str = "oauth_token") -> bool:
            return param_name in sig.parameters

        async def _async_wrapper(*args, **kwargs):  # type: ignore[return-value]
            # Get task context with parent token information
            ctx = task_context.get()
            if ctx is None:
                raise RuntimeError(f"Secure tool '{tool_name}' called outside an active task context")
            
            # Extract variables from context
            at_client = ctx["client"]
            parent_token = ctx["parent_token"]
            
            # Extract agent name from the context to get credentials
            from .agent_security import _AGENT_SECURITY_STATE
            # Get agent name from saved_context or first agent found
            agent_name = ctx.get("agent_name") or next(iter(_AGENT_SECURITY_STATE.keys()), None)
            agent_state = _AGENT_SECURITY_STATE.get(agent_name, {})
            
            # Get client credentials from agent state
            client_id = agent_state.get("client_id")
            client_secret = agent_state.get("client_secret")
            
            # Add required OIDC-A claims
            agent_type = agent_name
            agent_model = agent_state.get("agent_model", agent_name)
            agent_provider = agent_state.get("agent_provider", "demo")
            agent_instance_id = agent_name
            delegator_sub = agent_name

            # Request child token with proper credentials, parent context and OIDC-A claims
            child_resp = at_client.token.request(
                client_id=client_id,
                client_secret=client_secret,
                parent_token=parent_token,
                required_tools=[tool_name],
                scope=permissions_required or [],
                task_description=f"call {tool_name}",
                # Required OIDC-A claims
                agent_type=agent_type,
                agent_model=agent_model,
                agent_provider=agent_provider,
                agent_instance_id=agent_instance_id,
                delegator_sub=delegator_sub,
            )
            child_token = child_resp.get("access_token")
            if child_token is None:
                raise RuntimeError(f"Failed to obtain child token for tool {tool_name}")
            if _needs_token():
                kwargs.setdefault("oauth_token", child_token)
            try:
                return await fn(*args, **kwargs)
            finally:
                try:
                    at_client.token.revoke(child_token)
                except Exception as exc:  # pylint: disable=broad-except
                    print(f"Failed to revoke child token for {tool_name}: {exc}")

        def _sync_wrapper(*args, **kwargs):  # type: ignore[return-value]
            # Get task context with parent token information
            ctx = task_context.get()
            if ctx is None:
                raise RuntimeError(f"Secure tool '{tool_name}' called outside an active task context")
            
            # Extract variables from context
            at_client = ctx["client"]
            parent_token = ctx["parent_token"]
            
            # Extract agent name from the context to get credentials
            from .agent_security import _AGENT_SECURITY_STATE
            # Get agent name from saved_context or first agent found
            agent_name = ctx.get("agent_name") or next(iter(_AGENT_SECURITY_STATE.keys()), None)
            agent_state = _AGENT_SECURITY_STATE.get(agent_name, {})
            
            # Get client credentials from agent state
            client_id = agent_state.get("client_id")
            client_secret = agent_state.get("client_secret")
            
            # Add required OIDC-A claims
            agent_type = agent_name
            agent_model = agent_state.get("agent_model", agent_name)
            agent_provider = agent_state.get("agent_provider", "demo")
            agent_instance_id = agent_name
            delegator_sub = agent_name

            # Request child token with proper credentials, parent context and OIDC-A claims
            child_resp = at_client.token.request(
                client_id=client_id,
                client_secret=client_secret,
                parent_token=parent_token,
                required_tools=[tool_name],
                scope=permissions_required or [],
                task_description=f"call {tool_name}",
                # Required OIDC-A claims
                agent_type=agent_type,
                agent_model=agent_model,
                agent_provider=agent_provider,
                agent_instance_id=agent_instance_id,
                delegator_sub=delegator_sub,
            )
            child_token = child_resp.get("access_token")
            if child_token is None:
                raise RuntimeError(f"Failed to obtain child token for tool {tool_name}")
            if _needs_token():
                kwargs.setdefault("oauth_token", child_token)
            try:
                return fn(*args, **kwargs)
            finally:
                try:
                    at_client.token.revoke(child_token)
                except Exception as exc:  # pylint: disable=broad-except
                    print(f"Failed to revoke child token for {tool_name}: {exc}")

        wrapped_fn = _async_wrapper if async_def else _sync_wrapper
        wrapped_fn._tool_metadata = fn._tool_metadata  # type: ignore[attr-defined]
        _REGISTERED_TOOLS[tool_name] = wrapped_fn
        return wrapped_fn

    # Allow both @secure_tool and @secure_tool(...)
    return decorator if func is None else decorator(func)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def register_tool_with_client(client: AgenticTrustClient, func: Callable) -> str:
    """Ensure *func* (decorated with @secure_tool) exists on the server and return its ``tool_id``."""

    if not hasattr(func, "_tool_metadata"):
        raise ValueError("Function is not decorated with @secure_tool")

    meta = func._tool_metadata  # type: ignore[attr-defined]

    existing = next(
        (t for t in client.tool.list().get("tools", []) if t["name"] == meta["name"]),
        None,
    )
    if existing:
        tool_id = existing["tool_id"]
        print(f"Updating existing tool {meta['name']} (ID: {tool_id[:8]}…)")
        # Update metadata on the server if already registered
        client.tool.update(
            tool_id=tool_id,
            name=meta["name"],
            description=meta["description"],
            category=meta["category"],
            permissions_required=meta["permissions_required"],
            input_schema=meta["input_schema"],
        )
        return tool_id

    # Skip registration if required scopes are not registered
    existing_scopes = [s["name"] for s in client.scopes.list()]
    missing = [p for p in meta.get("permissions_required", []) if p not in existing_scopes]
    if missing:
        print(f"Skipping registration for tool {meta['name']}: missing scopes {missing}")
        return ""

    resp = client.tool.create(
        name=meta["name"],
        description=meta["description"],
        category=meta["category"],
        permissions_required=meta["permissions_required"],
        input_schema=meta["input_schema"],
    )
    tool_id = resp["tool"]["tool_id"]
    print(f"Registered new tool {meta['name']} (ID: {tool_id[:8]}…)")
    return tool_id


def get_registered_tools() -> Dict[str, Callable]:
    """Return mapping *name -> function* for all `@secure_tool` decorated functions in memory."""
    return _REGISTERED_TOOLS.copy()