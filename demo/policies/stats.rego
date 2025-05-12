package demo.authz

import data.demo.authz as helpers

# -------------------------------------------------------------
#  Analytics / stats endpoints
# -------------------------------------------------------------

# Company-scoped stats – exec or sales inside company
allow {
    input.path == ["stats", "company"]
    input.method == "GET"
    helpers.same_company(input.user, {"company_id": input.user.company_id})
    helpers.has_role(input.user, "executive")
}

allow {
    input.path == ["stats", "company"]
    input.method == "GET"
    helpers.same_company(input.user, {"company_id": input.user.company_id})
    helpers.has_role(input.user, "sales")
}

# Global stats – admin only
allow {
    input.path == ["stats", "global"]
    input.method == "GET"
    helpers.is_admin(input.user)
}
