package demo.authz

import data.demo.authz as helpers

# -------------------------------------------------------------
#  Company management (admin only)
# -------------------------------------------------------------

# List companies
allow {
    input.path == ["companies"]
    input.method == "GET"
    helpers.is_admin(input.user)
}

# Create company
allow {
    input.path == ["companies"]
    input.method == "POST"
    helpers.is_admin(input.user)
}

# Update / delete specific company
allow {
    input.path == ["companies", _]
    input.method == "PATCH"  # or PUT
    helpers.is_admin(input.user)
}

allow {
    input.path == ["companies", _]
    input.method == "DELETE"
    helpers.is_admin(input.user)
}
