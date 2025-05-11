package agentictrust.authz
import future.keywords.if

# -----------------------------------------------------------------------------
# Decision-point rules (placeholder logic, refine later)
# Each rule evaluates to a single boolean so it can be queried via
#   /v1/data/agentictrust/authz/<rule>
# -----------------------------------------------------------------------------

# 1. Scope expansion: allow implied scope unless we explicitly deny
#    Example input: {"requested": "read:basic", "implied": "read:extended", "context": {...}}
#    TODO: refine with subset logic or configurable mapping
default allow_scope_expansion = true

# 2. Human-in-the-loop requirement: default to false (no approval needed)
#    Example input: {"client_id": "abc", "scopes": ["write"], "response_type": "code"}
#    TODO: add conditions (e.g. destructive scopes)
default requires_human_approval = false

# 3. Token issuance (generic gate called by all grant handlers)
#    Input should contain grant_type, agent metadata, requested scopes, etc.
#    Default allow.
default allow_token_issue = true

# 4. Refresh token grant
default allow_refresh = true

# 5. Auth-code exchange
default allow_auth_code = true

# 6. Delegation is already handled by allow_delegation rule in delegation_policies.rego
#    but we expose an alias for clarity (returns same result).
# allow_delegation := allow_delegation  # no-op alias; existing rule already defined 