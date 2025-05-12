"""
Operations for scope expansion and helpers.
"""
from typing import List, Set
from agentictrust.db.models.scope import Scope
from agentictrust.core.scope.enum import ScopeAction


def expand_implied_scopes(scopes: List[str]) -> Set[str]:
    """
    Given a list of scope names, return the set including implied scopes
    based on qualifiers and action hierarchy.
    """
    # Load all registered scope names from DB
    all_scope_names = [s.name for s in Scope.query.all()]
    implied = set(scopes)
    for scope in scopes:
        parts = scope.split(':')
        if len(parts) < 2:
            continue
        resource, action = parts[0], parts[1]
        qualifiers = parts[2:]
        # Qualifier implication: broader implies more specific
        if not qualifiers:
            prefix = f"{resource}:{action}:"
            for name in all_scope_names:
                if name.startswith(prefix):
                    implied.add(name)
        # Action implication: ADMIN implies all other actions
        if action == ScopeAction.ADMIN.value:
            for action_enum in ScopeAction:
                if action_enum != ScopeAction.ADMIN:
                    new_name = ':'.join([resource, action_enum.value] + qualifiers)
                    if new_name in all_scope_names:
                        implied.add(new_name)
    return implied
