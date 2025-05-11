package agentictrust.authz
import future.keywords.if

default allow = false

# Top-level allow: all category checks must pass
allow if {
    allow_agent
    allow_scope
    allow_tool
    allow_delegation
}