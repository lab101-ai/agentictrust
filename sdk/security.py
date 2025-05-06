"""
Security decorators for Agents and Tools.
This module re-exports secure_agent and secure_tool decorators and related utilities
from the SDK security modules.
"""
import os
import sys
# Ensure project root in path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import from SDK modules
from sdk.security.agent_security import (
    secure_agent,
    generate_code_verifier,
    generate_code_challenge,
    get_registered_agent,
    list_registered_agents,
)
from sdk.security.tool_security import (
    secure_tool,
    register_tool_with_client,
    get_registered_tools,
)

__all__ = [
    'secure_agent',
    'generate_code_verifier',
    'generate_code_challenge',
    'get_registered_agent',
    'list_registered_agents',
    'secure_tool',
    'register_tool_with_client',
    'get_registered_tools',
]
