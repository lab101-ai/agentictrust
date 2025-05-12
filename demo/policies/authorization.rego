package demo.authz

default allow = false

# Allow anyone to list public tickets
allow {
    input.path == ["public_tickets"]
    input.method == "GET"
}

# Allow authenticated users to list own tickets
allow {
    input.path == ["tickets"]
    input.method == "GET"
    input.user != null
} 