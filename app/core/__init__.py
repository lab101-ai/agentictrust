# Core package initializer
"""Core package.

Provides helpers to access singleton instances of core engines.
"""

from .registry import (
    get_scope_engine,
    get_policy_engine,
    get_oauth_engine,
    get_delegation_engine,
    get_agent_engine,
    get_tool_engine,
    get_user_engine,
    initialize_core_engines  # noqa: F401   
)

__all__ = [
    "get_scope_engine",
    "get_policy_engine",
    "get_oauth_engine",
    "get_delegation_engine",
    "get_agent_engine",
    "get_tool_engine",
    "get_user_engine",
    "initialize_core_engines"
]