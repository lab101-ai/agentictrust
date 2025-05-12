package agentictrust.authz
import future.keywords.if
    
import data.agentictrust.authz as helpers

# -------------------------------------------------------------
#  Ticket read permissions
# -------------------------------------------------------------

# 1. Anyone can list public tickets
allow if {
    input.path == ["public_tickets"]
    input.method == "GET"
}

# 2. Authenticated user reading own ticket
allow if {
    input.path == ["tickets", ticket_id]
    input.method == "GET"
    ticket := data.tickets[ticket_id]
    input.user.id == ticket.user_id
}

# 3. Executive reading ticket in same company
allow if {
    input.path == ["tickets", ticket_id]
    input.method == "GET"
    ticket := data.tickets[ticket_id]
    helpers.has_role(input.user, "executive")
    helpers.same_company(input.user, ticket)
}
