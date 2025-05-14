package agentictrust.rbac

import future.keywords.if
import future.keywords.in

# Default deny
default allow := false

# Allow access if agent has a role with the required permission
allow if {
    # Get agent roles
    roles := input.agent.roles
    
    # Get required permission
    required_resource := input.resource
    required_action := input.action
    
    # Check if any role has the required permission
    some role in roles
    some permission in role.permissions
    permission.resource == required_resource
    permission.action == required_action
}

# Allow access for specific role names
allow if {
    # Get agent roles
    roles := input.agent.roles
    
    # Get required permission
    required_resource := input.resource
    required_action := input.action
    
    # Check for admin role (admins can do anything)
    some role in roles
    role.name == "admin"
}

# Allow access based on resource-specific rules
allow if {
    # Get agent roles
    roles := input.agent.roles
    
    # Get required permission
    required_resource := input.resource
    required_action := input.action
    
    # Special case for read-only resources
    required_action == "read"
    required_resource in ["public_data", "documentation", "schema"]
    
    # Any authenticated agent can read these resources
    count(roles) > 0
}
