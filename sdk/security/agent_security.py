"""
Security decorators for Agents.

This implementation was originally in demo/agent_security.py but has been
moved into the SDK so that external callers can simply do:

    from sdk.security.agent_security import secure_agent

without relying on demo modules.  All logic is unchanged except we removed
sys.path hacks and made the import of the Agent class tolerant of the class
living outside the SDK package.
"""

import uuid
import base64
import hashlib
import functools
import secrets
from typing import Optional, Dict, List, Union, Any
from contextlib import contextmanager
from .task_context import task_context

from sdk.client import AgenticTrustClient

try:
    # The reference implementation of `Agent` still lives in the demo package.
    from agent import Agent  # type: ignore
except ModuleNotFoundError:
    # Minimal fallback so that type annotations do not break importers even if
    # the demo package is not present.  This should never be used at runtime –
    # it only satisfies static type-checkers.
    class Agent:  # pylint: disable=too-few-public-methods
        pass

# =====================================================================================
# Internal registries shared across helper functions
# =====================================================================================

_REGISTERED_AGENTS: Dict[str, 'Agent'] = {}
# Per-agent security / OAuth state
_AGENT_SECURITY_STATE: Dict[str, Dict[str, Union[str, List[str], AgenticTrustClient]]] = {}

# =====================================================================================
# Public decorator
# =====================================================================================

def secure_agent(*, max_scope_level: str = "restricted", client: Optional[AgenticTrustClient] = None):
    """Decorator to transparently register an :class:`~demo.agent.Agent` with
    AgenticTrust and wrap its ``execute_task`` method so that each invocation
    automatically:

    1. Requests a scoped, short-lived OAuth token
    2. Executes the remote tool call with that token
    3. Immediately revokes the token afterwards

    The decorator can be applied to:

    • A *subclass* of ``Agent``
    • A *factory function* that returns an ``Agent`` instance
    • An *instance* of ``Agent`` directly
    """

    def decorator(cls_or_func_or_instance):  # noqa: C901  — kept original complexity
        agent_class = None
        agent_factory = None
        agent_instance = None

        # --- Figure out what we have been applied to ---------------------------------
        if isinstance(cls_or_func_or_instance, type) and issubclass(cls_or_func_or_instance, Agent):
            agent_class = cls_or_func_or_instance
        elif callable(cls_or_func_or_instance) and not isinstance(cls_or_func_or_instance, Agent):
            agent_factory = cls_or_func_or_instance
        elif isinstance(cls_or_func_or_instance, Agent):
            agent_instance = cls_or_func_or_instance
        else:
            raise TypeError(
                "@secure_agent must decorate an Agent subclass, a factory function that "
                "returns an Agent, or an Agent instance"
            )

        # -----------------------------------------------------------------------------
        def _secure_agent_instance(instance: 'Agent', current_client: Optional[AgenticTrustClient], scope_level: str):
            """Attach security state and replace ``execute_task`` on *instance*."""

            name = instance.name
            instructions = instance.role
            tools = instance.allowed_tools

            # ------------------------------------------------------------------ Tools
            if current_client and tools:
                tool_list = current_client.tool.list()
                for t in tool_list.get("tools", []):
                    t_name = t.get("name")
                    if t_name in tools:
                        state = _AGENT_SECURITY_STATE.setdefault(name, {})
                        # Store mapping from tool name to tool ID
                        state.setdefault("tool_ids", {})[t_name] = t.get("tool_id")
                # Save client in state for later use
                state.setdefault("client", current_client)

            # -------------------------------------------------------------- Registration
            if current_client:
                client = current_client  # alias for brevity

                try:
                    existing = client.agent.list(name_filter=name, active_only=False)
                    agents = existing.get("agents") or existing.get("data") or []
                    match = next((a for a in agents if (a.get("agent_name") or a.get("name")) == name), None)
                except Exception:
                    match = None

                creds: Dict[str, Any] = {}
                if match:
                    agent_id = match.get("agent_id") or match.get("id")
                    client_id_val = match.get("client_id") or match.get("clientId")
                    if agent_id and client_id_val:
                        try:
                            secret_resp: Dict[str, Any] = client.agent.regenerate_secret(agent_id)
                            client_secret_val = secret_resp.get("client_secret") or secret_resp.get("clientSecret")
                            if client_secret_val:
                                creds = {"client_id": client_id_val, "client_secret": client_secret_val}
                        except Exception:
                            # Could not regenerate; will register anew
                            creds = {}

                if not creds:
                    # Map tool names to IDs if available
                    tool_ids_list = []
                    if tools:
                        tool_lookup = {t.get("name"): t.get("tool_id") for t in client.tool.list().get("tools", [])}
                        tool_ids_list = [tool_lookup[n] for n in tools if n in tool_lookup]

                    resp = client.agent.register(
                        agent_name=name,
                        description=instructions,
                        allowed_tools=tools,
                        max_scope_level=scope_level,
                        tool_ids=tool_ids_list,
                    )
                    creds = resp.get("credentials", {})

                state = _AGENT_SECURITY_STATE.setdefault(name, {})
                state.update(
                    {
                        "client": client,
                        "client_id": creds.get("client_id"),
                        "client_secret": creds.get("client_secret"),
                        "token_stack": [],    # Full lineage stack [{token, task_id}, …]
                    }
                )

                # Activate only if this is a fresh registration and activation token
                activation_token = creds.get("activation_token")
                if activation_token:
                    client.agent.activate(activation_token)
                print(f"Agent '{name}' registered and credentials refreshed")
            # ------------------------------------------------------ execute_task wrapper (parent-token)
            if hasattr(instance, "execute_task"):
                original_execute = instance.execute_task

                @functools.wraps(original_execute)
                def secure_execute_task(*args, **kwargs):
                    """Fetch parent token, set context, invoke task, then revoke and cleanup."""
                    inst = args[0]
                    # extract payload and tool_name
                    payload = args[1] if len(args) > 1 else kwargs.get('payload')
                    tool_name = args[2] if len(args) > 2 else kwargs.get('tool_name')
                    # pop parameters
                    scope_val = kwargs.pop('scope', None)
                    token_desc_val = kwargs.pop('token_desc', None)
                    # prepare OIDC-A claims
                    agent_type_val = inst.name
                    agent_model_val = inst.__class__.__name__
                    agent_provider_val = inst.__class__.__module__
                    agent_instance_id_val = inst.name
                    delegator_sub_val = inst.name
                    # client credentials
                    state = _AGENT_SECURITY_STATE.get(inst.name, {})
                    client = state.get('client')
                    client_id_val = state.get('client_id')
                    client_secret_val = state.get('client_secret')
                    # request parent token
                    token_resp = client.token.request(
                        client_id=client_id_val,
                        client_secret=client_secret_val,
                        scope=scope_val or [tool_name],
                        task_description=token_desc_val or f"Agent '{inst.name}' executing '{tool_name}'",
                        agent_type=agent_type_val,
                        agent_model=agent_model_val,
                        agent_provider=agent_provider_val,
                        agent_instance_id=agent_instance_id_val,
                        delegator_sub=delegator_sub_val,
                    )
                    parent_token = token_resp.get('access_token')
                    parent_task_id = token_resp.get('task_id')
                    # set parent context
                    token_var = task_context.set({
                        'parent_token': parent_token,
                        'parent_task_id': parent_task_id,
                        'client': client,
                    })
                    try:
                        return original_execute(*args, oauth_token=parent_token, **kwargs)
                    finally:
                        try:
                            client.token.revoke(parent_token)
                        finally:
                            task_context.reset(token_var)

                instance.execute_task = secure_execute_task  # type: ignore[attr-defined]

            _REGISTERED_AGENTS[instance.name] = instance

        # --------------------------------------------------------------------- Wrappers
        if agent_instance is not None:
            _secure_agent_instance(agent_instance, client, max_scope_level)
            return agent_instance

        @functools.wraps(cls_or_func_or_instance)
        def wrapper(*args, **kwargs):
            current_client = client or kwargs.pop("client", None)
            if agent_class is not None:
                created_instance = agent_class(*args, **kwargs)
            else:
                created_instance = agent_factory(*args, **kwargs)  # type: ignore[misc]
            created_instance.client = current_client  # type: ignore[attr-defined]
            _secure_agent_instance(created_instance, current_client, max_scope_level)
            return created_instance

        wrapper._agent_metadata = {}  # type: ignore[attr-defined]
        return wrapper

    return decorator

# =====================================================================================
# Helper / utility functions (ported verbatim)
# =====================================================================================

def get_registered_agent(name: str) -> Optional['Agent']:
    """Return an *already instantiated* secure agent by *name*."""
    return _REGISTERED_AGENTS.get(name)


def list_registered_agents() -> Dict[str, 'Agent']:
    """Return a *copy* of the internal registry mapping name -> Agent."""
    return _REGISTERED_AGENTS.copy()

# ------------------------------- PKCE helpers ----------------------------------------

def generate_code_verifier(length: int = 128) -> str:
    code_verifier = base64.urlsafe_b64encode(secrets.token_bytes(96)).decode("utf-8").rstrip("=")
    return code_verifier[:length]


def generate_code_challenge(verifier: str) -> str:
    digest = hashlib.sha256(verifier.encode("utf-8")).digest()
    return base64.urlsafe_b64encode(digest).decode("utf-8").rstrip("=")

# --------------------------- start_task context manager ---------------------------
@contextmanager
def start_task(agent: 'Agent', *, scope: Optional[List[str]] = None,
               description: str = "parent task", client: Optional[AgenticTrustClient] = None,
               **claims):
    """Issue a *parent* token for *agent* and make it available to secure tools.

    Usage::
        with start_task(bot, scope=["search:*"], description="answer user"):
            bot.execute_task({...}, tool_name="web_search")

    The token is revoked automatically when the block exits.
    """
    state = _AGENT_SECURITY_STATE.get(agent.name)
    if state is None:
        raise ValueError(f"Agent {agent.name!r} not registered via secure_agent")

    at_client = client or state.get("client")
    if at_client is None:
        raise RuntimeError("No AgenticTrustClient associated with agent")

    client_id_val = state.get("client_id")
    client_secret_val = state.get("client_secret")
    if not (client_id_val and client_secret_val):
        raise RuntimeError("Missing client credentials for agent")

    # default OIDC-A claims
    default_claims = {
        'agent_type': agent.name,
        'agent_model': agent.__class__.__name__,
        'agent_provider': agent.__class__.__module__,
        'agent_instance_id': agent.name,
        'delegator_sub': agent.name,
    }
    # merge with any overrides
    req_claims = {**default_claims, **claims}
    token_resp = at_client.token.request(
        client_id=client_id_val,
        client_secret=client_secret_val,
        scope=scope or agent.allowed_tools,
        task_description=description,
        **req_claims,
    )
    parent_token = token_resp["access_token"]
    parent_task_id = token_resp["task_id"]

    token_var = task_context.set({
        "parent_token": parent_token,
        "parent_task_id": parent_task_id,
        "client": at_client,
        "agent_name": agent.name,
    })
    try:
        yield
    finally:
        try:
            at_client.token.revoke(parent_token)
        finally:
            task_context.reset(token_var)

# ----------------------------- Server interactions -----------------------------------

def register_agent(agent: 'Agent', client: AgenticTrustClient, *, description: Optional[str] = None,
                   max_scope_level: str = "restricted") -> 'Agent':
    if agent.allowed_tools:
        tool_list = client.tool.list()
        registered_names = {t["name"] for t in tool_list.get("tools", [])}
        missing = [t for t in agent.allowed_tools if t not in registered_names]
        if missing:
            raise ValueError(
                f"Cannot register agent '{agent.name}' because these tools are not registered: {', '.join(missing)}"
            )

    tool_ids = []
    if agent.allowed_tools:
        tool_lookup = {t["name"]: t["tool_id"] for t in client.tool.list().get("tools", [])}
        tool_ids = [tool_lookup[n] for n in agent.allowed_tools if n in tool_lookup]

    # ------------------------------------------------------------------
    # Reuse existing agent registration if it already exists so that the
    # same ``client_id`` is preserved across multiple runs instead of
    # creating a brand-new client on every invocation.
    # ------------------------------------------------------------------
    try:
        existing = client.agent.list(name_filter=agent.name, active_only=False)
        agents = existing.get("agents") or existing.get("data") or []
        match = next((a for a in agents if (a.get("agent_name") or a.get("name")) == agent.name), None)
    except Exception:
        match = None

    creds: Dict[str, Any] = {}
    if match:
        agent_id = match.get("agent_id") or match.get("id")
        client_id_val = match.get("client_id") or match.get("clientId")
        if agent_id and client_id_val:
            try:
                secret_resp: Dict[str, Any] = client.agent.regenerate_secret(agent_id)
                client_secret_val = secret_resp.get("client_secret") or secret_resp.get("clientSecret")
                if client_secret_val:
                    creds = {"client_id": client_id_val, "client_secret": client_secret_val}
            except Exception:
                # Could not regenerate; will register anew
                creds = {}

    if not creds:
        resp = client.agent.register(
            agent_name=agent.name,
            description=description or agent.role,
            allowed_tools=agent.allowed_tools,
            max_scope_level=max_scope_level,
            tool_ids=tool_ids,
        )
        creds = resp.get("credentials", {})

    state = _AGENT_SECURITY_STATE.setdefault(agent.name, {})
    state.update(
        {
            "client": client,
            "client_id": creds.get("client_id"),
            "client_secret": creds.get("client_secret"),
            "token_stack": [],    # Full lineage stack [{token, task_id}, …]
        }
    )

    # Activate only if this is a fresh registration and activation token
    activation_token = creds.get("activation_token")
    if activation_token:
        client.agent.activate(activation_token)
    return agent


def fetch_token(
    agent: 'Agent',
    client: AgenticTrustClient,
    *,
    required_tools: Optional[List[str]] = None,
    scope: Union[List[str], str],
    task_description: str,
    code_challenge: str | None = None,
    code_challenge_method: str = "S256",
    parent_token: str | None = None,
    parent_task_id: str | None = None,
    scope_inheritance_type: str = "restricted",
    # Launch context
    launch_reason: str = "user_interactive",
    launched_by: Optional[str] = None,
    # OIDC-A Claims (arguments take precedence)
    agent_instance_id: Optional[str] = None,
    agent_type: Optional[str] = None,
    agent_model: Optional[str] = None,
    agent_version: Optional[str] = None,
    agent_provider: Optional[str] = None,
    agent_trust_level: Optional[str] = None,
    agent_context_id: Optional[str] = None,
    delegator_sub: Optional[str] = None,
    delegation_purpose: Optional[str] = None,
    delegation_chain: Optional[List[str]] = None,
    delegation_constraints: Optional[Dict] = None,
    agent_capabilities: Optional[List[str]] = None,
    agent_attestation: Optional[Dict] = None,
) -> Dict[str, Any]:
    """Request a short-lived OAuth token for a specific task."""
    state = _AGENT_SECURITY_STATE.get(agent.name)
    if state is None:
        raise ValueError(f"Agent {agent.name} is not registered")

    # --- Populate required OIDC-A claims from agent if not provided ---
    # Assuming agent object has these attributes. Adjust if needed.
    final_agent_instance_id = agent_instance_id or getattr(agent, 'instance_id', state.get('client_id')) # Use client_id as fallback
    final_agent_type = agent_type or getattr(agent, 'agent_type', 'unknown_type')
    final_agent_model = agent_model or getattr(agent, 'agent_model', 'unknown_model')
    final_agent_provider = agent_provider or getattr(agent, 'agent_provider', 'unknown_provider')
    # Use agent's client_id as the default delegator if not specified
    final_delegator_sub = delegator_sub or state.get('client_id')
    # Optional claims from agent if not passed
    final_agent_version = agent_version or getattr(agent, 'agent_version', None)
    final_agent_trust_level = agent_trust_level or getattr(agent, 'agent_trust_level', None)
    final_agent_context_id = agent_context_id or getattr(agent, 'agent_context_id', None)
    final_delegation_purpose = delegation_purpose or getattr(agent, 'delegation_purpose', None)
    final_agent_capabilities = agent_capabilities or getattr(agent, 'agent_capabilities', None)

    task_id = str(uuid.uuid4())
    try:
        token_resp = client.token.request(
            client_id=state["client_id"],
            client_secret=state["client_secret"],
            scope=scope,
            task_id=task_id,
            task_description=task_description,
            required_tools=required_tools,
            code_challenge=code_challenge,
            code_challenge_method=code_challenge_method,
            parent_token=parent_token,
            parent_task_id=parent_task_id,
            scope_inheritance_type=scope_inheritance_type,
            launch_reason=launch_reason,
            launched_by=launched_by,
            # Pass populated OIDC-A claims
            agent_instance_id=final_agent_instance_id,
            agent_type=final_agent_type,
            agent_model=final_agent_model,
            agent_version=final_agent_version, # Pass optional version if available
            agent_provider=final_agent_provider,
            agent_trust_level=final_agent_trust_level, # Pass optional trust level
            agent_context_id=final_agent_context_id, # Pass optional context id
            delegator_sub=final_delegator_sub,
            delegation_purpose=final_delegation_purpose, # Pass optional purpose
            delegation_chain=delegation_chain, # Pass through if provided
            delegation_constraints=delegation_constraints, # Pass through if provided
            agent_capabilities=final_agent_capabilities, # Pass optional capabilities
            agent_attestation=agent_attestation # Pass through if provided
        )
        return token_resp
    except Exception as exc:  # pylint: disable=broad-except
        if client and client.config.debug:
            print(f"Failed to request token: {str(exc)}", exc_info=True)
        print(f"Failed to request token: {exc}")
        return {}