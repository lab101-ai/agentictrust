package agentictrust.authz
import future.keywords.if

# Legacy mapping: External agents cannot use internal tools

denied_tool if {
    input.agent.agent_trust_level == "external"
    input.tool.classification == "internal"
}

allow_tool if not denied_tool 