package agentictrust.authz
import future.keywords.if

# Allow anyone to list public tickets
allow if {
    input.path == ["public_tickets"]
    input.method == "GET"
}

# Allow authenticated users to list own tickets
allow if {
    input.path == ["tickets"]
    input.method == "GET"
    input.user != null
} 