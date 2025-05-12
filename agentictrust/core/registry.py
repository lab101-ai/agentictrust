"""Core engine registry for singleton instances.

This module lazily creates and returns singleton instances of core engines
(e.g., ScopeEngine).  It also provides an `initialize_core_engines()` helper
that can be invoked after the database has been initialised (e.g., in the
FastAPI lifespan hook) so that all engines are created eagerly once the DB is
ready.
"""
from functools import lru_cache
from typing import Any, Dict

from agentictrust.core.scope.engine import ScopeEngine
from agentictrust.core.oauth.engine import OAuthEngine
from agentictrust.core.delegation.engine import DelegationEngine
from agentictrust.core.agents.engine import AgentEngine
from agentictrust.core.tools.engine import ToolEngine
from agentictrust.core.users.engine import UserEngine

# ---------------------------------------------------------------------------
# Lazy-singleton helpers
# ---------------------------------------------------------------------------

@lru_cache(maxsize=None)
def get_scope_engine() -> ScopeEngine:  # pragma: no cover
    """Return a singleton :class:`ScopeEngine` instance.

    The first call will create the engine; subsequent calls return the same
    instance thanks to ``functools.lru_cache``.
    """
    return ScopeEngine()

# Lazy-singleton helper for OAuthEngine
@lru_cache(maxsize=None)
def get_oauth_engine() -> OAuthEngine:
    """Return a singleton :class:`OAuthEngine` instance."""
    return OAuthEngine()

# Lazy-singleton helper for DelegationEngine
@lru_cache(maxsize=None)
def get_delegation_engine() -> DelegationEngine:
    """Return a singleton :class:`DelegationEngine` instance."""
    return DelegationEngine()

# Lazy-singleton helper for AgentEngine
@lru_cache(maxsize=None)
def get_agent_engine() -> AgentEngine:
    """Return a singleton :class:`AgentEngine` instance."""
    return AgentEngine()

# Lazy-singleton helper for ToolEngine
@lru_cache(maxsize=None)
def get_tool_engine() -> ToolEngine:
    """Return a singleton :class:`ToolEngine` instance."""
    return ToolEngine()

# Lazy-singleton helper for UserEngine
@lru_cache(maxsize=None)
def get_user_engine() -> UserEngine:
    """Return a singleton :class:`UserEngine` instance."""
    return UserEngine()

# If additional engines are introduced (e.g., AgentEngine), create
# similar `get_..._engine` helpers here and add them to ``_ALL_ENGINE_GETTERS``.

_ALL_ENGINE_GETTERS = [
    get_scope_engine,
    get_oauth_engine,
    get_delegation_engine,
    get_agent_engine,
    get_tool_engine,
    get_user_engine,
]

# ---------------------------------------------------------------------------
# Eager initialisation helper
# ---------------------------------------------------------------------------

def initialize_core_engines() -> Dict[str, Any]:  # pragma: no cover
    """Eagerly instantiate and return all core engines.

    Call this **after** the database has been initialised to ensure engines
    that touch the DB during their constructor (e.g., to seed data) have the
    required tables available.
    """
    instances: Dict[str, Any] = {}
    for getter in _ALL_ENGINE_GETTERS:
        inst = getter()
        instances[getter.__name__.replace("get_", "")] = inst
    return instances
