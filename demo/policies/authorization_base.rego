package demo.authz

# -------------------------------------------------------------
#  Base policy helpers & global admin override
# -------------------------------------------------------------

# Deny everything unless an `allow` rule evaluates to true.
# NOTE: Only this file defines the default for `allow` so that
# other modules can simply add more `allow` rules.
default allow = false

# -------------------------------------------------------------
#  Helper rules / predicates
# -------------------------------------------------------------

# Ticket is explicitly marked public
is_public_ticket(ticket) {
    ticket.public == true
}

# User and resource share the same company (multi-tenant isolation)
same_company(user, resource) {
    user.company_id == resource.company_id
}

# Check user role string equality
has_role(user, role) {
    user.role == role
}

# Re-usable admin test
is_admin(user) {
    has_role(user, "admin")
}

# Global override – admins may do anything
allow {
    is_admin(input.user)
}
