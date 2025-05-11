package agentictrust.authz
import future.keywords.if

# Legacy mapping: Only single-level delegation is allowed
allow_delegation if input.delegation_chain == null

allow_delegation if count(input.delegation_chain) <= 1 