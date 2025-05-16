package agentictrust.delegation

import future.keywords.if
import future.keywords.in

# Default deny
default allow := false

# Allow delegation if user has explicitly authorized the agent
allow if {
    # Check if this is a human delegation request
    input.delegation_type == "human_to_agent"
    
    # Verify user has authorized this agent
    input.authorization.is_active == true
    
    # Verify authorization has not expired
    not is_expired(input.authorization.expires_at)
    
    # Verify requested scopes are subset of authorized scopes
    is_scope_subset(input.requested_scopes, input.authorization.scopes)
    
    # Verify any additional constraints
    satisfy_constraints(input.authorization.constraints)
}

# Check if authorization has expired
is_expired(expires_at) if {
    expires_at != null
    time.parse_rfc3339_ns(expires_at) < time.now_ns()
}

# Check if requested scopes are a subset of authorized scopes
is_scope_subset(requested, authorized) if {
    # Convert authorized scopes to a set
    authorized_set := { scope | scope in authorized }
    
    # Check if all requested scopes are in the authorized set
    count({ scope | scope in requested; not scope in authorized_set }) == 0
}

# Check if delegation satisfies additional constraints
satisfy_constraints(constraints) if {
    # If no constraints, automatically satisfied
    constraints == null
}

satisfy_constraints(constraints) if {
    # Time-based constraints
    constraints.time_restrictions == null
}

satisfy_constraints(constraints) if {
    # Time-based constraints
    time_restrictions := constraints.time_restrictions
    
    # Check if current time is within allowed hours
    current_hour := time.clock(time.now_ns())[0]
    current_hour >= time_restrictions.start_hour
    current_hour <= time_restrictions.end_hour
}

# Resource-specific constraints
satisfy_constraints(constraints) if {
    # Resource access constraints
    resource_constraints := constraints.resources
    
    # If no resource constraints, automatically satisfied
    resource_constraints == null
}

satisfy_constraints(constraints) if {
    # Resource access constraints
    resource_constraints := constraints.resources
    
    # Check if requested resource is allowed
    requested_resource := input.resource
    requested_resource in resource_constraints.allowed_resources
}
