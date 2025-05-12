package agentictrust.authz
import future.keywords.if

default allow := false

is_public_ticket(ticket) if {
    ticket.public
}
same_company(user, resource) if {
    user.company_id == resource.company_id
}
has_role(user, role) if {
    user.role == role
}
is_admin(user) if {
    has_role(user, "admin")
}
allow if {
    is_admin(input.user)
}
