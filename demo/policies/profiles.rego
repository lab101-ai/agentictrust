package agentictrust.authz
import future.keywords.if

import data.agentictrust.authz as helpers

# -------------------------------------------------------------
#  User profile access
# -------------------------------------------------------------

# Self-read / self-update
allow if {
    count(input.path) == 2
    input.path[0] == "profiles"
    profile_id := input.path[1]
    input.method == "GET"
    profile := data.profiles[profile_id]
    input.user.id == profile.user_id
}

allow if {
    count(input.path) == 2
    input.path[0] == "profiles"
    profile_id := input.path[1]
    input.method == "PATCH"
    profile := data.profiles[profile_id]
    input.user.id == profile.user_id
}

# Company executives can read all profiles in their company
allow if {
    count(input.path) == 2
    input.path[0] == "profiles"
    profile_id := input.path[1]
    input.method == "GET"
    profile := data.profiles[profile_id]
    helpers.has_role(input.user, "executive")
    helpers.same_company(input.user, profile)
}
