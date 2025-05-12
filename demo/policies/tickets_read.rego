package demo.authz

import data.demo.authz as helpers

# -------------------------------------------------------------
#  Ticket read permissions
# -------------------------------------------------------------

# 1. Anyone can list public tickets
allow {
    input.path == ["public_tickets"]
    input.method == "GET"
}

# 2. Authenticated user reading own ticket
allow {
    input.path == ["tickets", ticket_id]
    input.method == "GET"
    ticket := data.tickets[ticket_id]
    input.user.id == ticket.user_id
}

# 3. Executive reading ticket in same company
allow {
    input.path == ["tickets", ticket_id]
    input.method == "GET"
    ticket := data.tickets[ticket_id]
    helpers.has_role(input.user, "executive")
    helpers.same_company(input.user, ticket)
}
