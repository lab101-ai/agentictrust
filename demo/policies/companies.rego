package agentictrust.authz
import future.keywords.if

import data.agentictrust.authz as helpers

# -------------------------------------------------------------
#  Company management (admin only)
# -------------------------------------------------------------

# List companies
allow if {
    input.path == ["companies"]
    input.method == "GET"
    helpers.is_admin(input.user)
}

# Create company
allow if {
    input.path == ["companies"]
    input.method == "POST"
    helpers.is_admin(input.user)
}

# Update / delete specific company
allow if {
    count(input.path) == 2
    input.path[0] == "companies"
    input.method == "PATCH"  # or PUT
    helpers.is_admin(input.user)
}

allow if {
    count(input.path) == 2
    input.path[0] == "companies"
    input.method == "DELETE"
    helpers.is_admin(input.user)
}
