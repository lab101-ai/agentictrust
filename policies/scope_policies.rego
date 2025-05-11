package agentictrust.authz
import future.keywords.if

# Legacy mapping: Child token requested scopes must be a subset of parent token scopes
# allow_scope {
#     # Count of requested scopes present in parent.scopes must equal total requested count
#     count({ rs | rs := input.requested_scopes[_]; rs in input.parent.scopes }) == count(input.requested_scopes)
# }

allow_scope if count({ rs | rs := input.requested_scopes[_]; rs in input.parent.scopes }) == count(input.requested_scopes) 