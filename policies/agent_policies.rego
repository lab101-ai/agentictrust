package agentictrust.authz
import future.keywords.if

# Legacy mapping: Only active agents are allowed to proceed
# (In Python PolicyEngine, policies or engine logic skip inactive agents)
allow_agent if input.agent.status == "active" 