"""
Utilities for scope name validation.
"""
import re
from agentictrust.core.scope.enum import ScopeAction

# Build regex dynamically from enum values
actions_regex = '|'.join([action.value for action in ScopeAction])
SCOPE_PATTERN = re.compile(rf'^[a-z]+:(?:{actions_regex})(?::[a-z]+)*$')

def validate_scope_name(name: str) -> None:
    """
    Raises ValueError if the scope name does not follow the convention.
    """
    if not SCOPE_PATTERN.match(name):
        raise ValueError(f"Invalid scope format: {name}")
