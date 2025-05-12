package agentictrust.authz
import future.keywords.if

import data.agentictrust.authz as helpers

# -------------------------------------------------------------
#  Ticket write permissions
# -------------------------------------------------------------

# Create ticket – any authenticated user (company derived in API layer)
allow if {
    input.path == ["tickets"]
    input.method == "POST"
    input.user != null
}

# Update / close / delete own ticket
allow if {
    count(input.path) == 2
    input.path[0] == "tickets"
    ticket_id := input.path[1]
    input.method == "PATCH"
    ticket := data.tickets[ticket_id]
    input.user.id == ticket.user_id
}

allow if {
    count(input.path) == 2
    input.path[0] == "tickets"
    ticket_id := input.path[1]
    input.method == "DELETE"
    ticket := data.tickets[ticket_id]
    input.user.id == ticket.user_id
}

# Executive can update/delete tickets in same company
allow if {
    count(input.path) == 2
    input.path[0] == "tickets"
    ticket_id := input.path[1]
    input.method == "PATCH"
    ticket := data.tickets[ticket_id]
    helpers.has_role(input.user, "executive")
    helpers.same_company(input.user, ticket)
}

allow if {
    count(input.path) == 2
    input.path[0] == "tickets"
    ticket_id := input.path[1]
    input.method == "DELETE"
    ticket := data.tickets[ticket_id]
    helpers.has_role(input.user, "executive")
    helpers.same_company(input.user, ticket)
}
