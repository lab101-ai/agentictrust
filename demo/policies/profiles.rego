package demo.authz

import data.demo.authz as helpers

# -------------------------------------------------------------
#  User profile access
# -------------------------------------------------------------

# Self-read / self-update
allow {
    input.path == ["profiles", profile_id]
    input.method == "GET"
    profile := data.profiles[profile_id]
    input.user.id == profile.user_id
}

allow {
    input.path == ["profiles", profile_id]
    input.method == "PATCH"
    profile := data.profiles[profile_id]
    input.user.id == profile.user_id
}

# Company executives can read all profiles in their company
allow {
    input.path == ["profiles", profile_id]
    input.method == "GET"
    profile := data.profiles[profile_id]
    helpers.has_role(input.user, "executive")
    helpers.same_company(input.user, profile)
}
