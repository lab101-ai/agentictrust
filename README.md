# AgenticTrust API - OAuth 2.1 Implementation

This project implements a secure OAuth 2.1 authentication and authorization system for LLM-based agents.

## Features

- **OAuth 2.1 compliance** with mandatory PKCE for all flows
- **Authorization Code Flow** with PKCE for web and mobile apps
- **Client Credentials Flow** with PKCE for machine-to-machine authentication
- **Refresh Token** support with PKCE verification
- **Dynamic Client Registration** support
- **Authorization Server Metadata** endpoint
- **Task-aware tokens** with parent-child lineage verification
- **Scope inheritance** from parent to child tasks

## Authentication Flows

### Authorization Code Flow with PKCE

1. Generate a code verifier and code challenge
2. Request an authorization code with the code challenge
3. Exchange the authorization code with the code verifier for tokens

```
# Step 1: Generate code verifier and challenge (client-side)
code_verifier = generate_random_string(64)
code_challenge = base64_url_encode(SHA256(code_verifier))

# Step 2: Get authorization code
GET /api/oauth/authorize?
  response_type=code&
  client_id=CLIENT_ID&
  redirect_uri=REDIRECT_URI&
  scope=SCOPE&
  state=STATE&
  code_challenge=CODE_CHALLENGE&
  code_challenge_method=S256

# Step 3: Exchange code for tokens
POST /api/oauth/token
Content-Type: application/x-www-form-urlencoded

grant_type=authorization_code&
code=AUTHORIZATION_CODE&
client_id=CLIENT_ID&
redirect_uri=REDIRECT_URI&
code_verifier=CODE_VERIFIER
```

### Client Credentials Flow with PKCE

```
POST /api/oauth/token
Content-Type: application/json

{
  "grant_type": "client_credentials",
  "client_id": "CLIENT_ID",
  "client_secret": "CLIENT_SECRET",
  "scope": "SCOPE",
  "code_challenge": "CODE_CHALLENGE",
  "code_challenge_method": "S256",
  "task_id": "TASK_ID",
  "task_description": "TASK_DESCRIPTION"
}
```

## Task-Aware Authentication

Each token is associated with a task, and tokens can have parent-child relationships:

```
POST /api/oauth/token
Content-Type: application/json

{
  "grant_type": "client_credentials",
  "client_id": "CLIENT_ID",
  "client_secret": "CLIENT_SECRET",
  "scope": "SCOPE",
  "code_challenge": "CODE_CHALLENGE",
  "code_challenge_method": "S256",
  "task_id": "SUBTASK_ID",
  "task_description": "Subtask execution",
  "parent_task_id": "PARENT_TASK_ID",
  "parent_token": "PARENT_TOKEN"
}
```

## Dynamic Client Registration

```
POST /api/oauth/register
Content-Type: application/json

{
  "client_name": "My Agent",
  "client_uri": "https://example.com/agent",
  "redirect_uris": ["https://example.com/callback"],
  "grant_types": ["authorization_code", "client_credentials"],
  "response_types": ["code"],
  "token_endpoint_auth_method": "client_secret_basic"
}
```

## Server Metadata

The server publishes its configuration at:

```
GET /.well-known/oauth-authorization-server
```

## Security Considerations

- PKCE is mandatory for all grant types
- Tokens are short-lived by default
- All token usage is logged for audit
- Task lineage is verified for child tokens
- Scope inheritance follows the principle of least privilege

## Project Structure

- `app/`: Flask application (OAuth server)
  - `models/`: Database models
  - `routes/`: API routes
  - `utils/`: Utility functions
    - `logger.py`: Centralized logging configuration
- `sdk/`: Python SDK for agents
  - `agentictrust/`: SDK package
  - `examples/`: Example usage with CrewAI
- `docs/`: Documentation
- `tests/`: Tests for both app and SDK
- `logs/`: Application logs (created at runtime)

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/agentictrust.git
   cd agentictrust
   ```

2. Using Poetry (recommended):
   ```
   ./scripts/setup-poetry.sh
   poetry shell
   ```

3. Using venv (alternative):
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

## Running the OAuth Server

Using Poetry:
```
poetry run python run.py
```

Using venv:
```
python run.py
```

The server will be available at http://localhost:5000.

## Logging

This application uses Loguru for structured logging with the following features:

- Console logging with colored output
- File logging with rotation (logs/app.log)
- Dedicated error logs (logs/error.log)
- Specialized OAuth operation logs (logs/oauth.log)
- Agent action logs (logs/agent_actions.log)

Log levels can be configured via the LOG_LEVEL environment variable (default: INFO).

## Using the SDK

Here's a simple example of using the SDK:

```python
from sdk.agentictrust import AgenticTrustClient

# Initialize client
client = AgenticTrustClient(base_url="http://localhost:5000")

# Register an agent
response = client.agent.register(
    agent_name="ExampleAgent",
    description="An example agent",
    allowed_tools=["web_search", "document_retrieval"],
    allowed_resources=["search_engine", "document_store"]
)

# Store credentials
client_id = response["credentials"]["client_id"]
client_secret = response["credentials"]["client_secret"]
registration_token = response["credentials"]["registration_token"]

# Activate the agent
client.agent.activate(registration_token)

# Request a token for a task
token_response = client.token.request(
    client_id=client_id,
    client_secret=client_secret,
    scope=["read:web", "execute:task"],
    task_description="Search for information about OAuth",
    required_tools=["web_search"],
    required_resources=["search_engine"]
)

# Use the token to access a protected resource
result = client.token.call_protected_endpoint()
print(result)

# Revoke the token when done
client.token.revoke(reason="Task completed")
```

## CrewAI Integration Example

For a complete example of integration with CrewAI, see the example in `sdk/examples/crewai_example.py`.

## API Endpoints

### Agent Management
- `POST /api/agents/register`: Register a new agent
- `POST /api/agents/activate`: Activate a registered agent
- `GET /api/agents/list`: List all registered agents
- `GET /api/agents/<client_id>`: Get agent details
- `DELETE /api/agents/<client_id>`: Delete an agent

### OAuth
- `POST /api/oauth/token`: Issue a new token
- `POST /api/oauth/verify`: Verify a token
- `POST /api/oauth/introspect`: Introspect a token
- `POST /api/oauth/revoke`: Revoke a token
- `GET /api/oauth/protected`: Example protected endpoint

### Admin
- `GET /api/admin/tokens`: List all tokens
- `GET /api/admin/tokens/<token_id>`: Get token details
- `POST /api/admin/tokens/<token_id>/revoke`: Revoke a token
- `GET /api/admin/tokens/search`: Search tokens
- `GET /api/admin/audit/logs`: List audit logs
- `GET /api/admin/audit/task/<task_id>`: Get task history
- `GET /api/admin/audit/task-chain/<task_id>`: Get task chain

## License

MIT

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. 