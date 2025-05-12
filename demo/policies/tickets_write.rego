package demo.authz

import data.demo.authz as helpers

# -------------------------------------------------------------
#  Ticket write permissions
# -------------------------------------------------------------

# Create ticket – any authenticated user (company derived in API layer)
allow {
    input.path == ["tickets"]
    input.method == "POST"
    input.user != null
}

# Update / close / delete own ticket
allow {
    input.path == ["tickets", ticket_id]
    input.method == "PATCH"
    ticket := data.tickets[ticket_id]
    input.user.id == ticket.user_id
}

allow {
    input.path == ["tickets", ticket_id]
    input.method == "DELETE"
    ticket := data.tickets[ticket_id]
    input.user.id == ticket.user_id
}

# Executive can update/delete tickets in same company
allow {
    input.path == ["tickets", ticket_id]
    input.method == "PATCH"
    ticket := data.tickets[ticket_id]
    helpers.has_role(input.user, "executive")
    helpers.same_company(input.user, ticket)
}

allow {
    input.path == ["tickets", ticket_id]
    input.method == "DELETE"
    ticket := data.tickets[ticket_id]
    helpers.has_role(input.user, "executive")
    helpers.same_company(input.user, ticket)
}
