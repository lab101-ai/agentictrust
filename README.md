# AgenticTrust: OAuth for AI Agents

An implementation of the AgenticTrust OAuth framework for secure authentication and authorization of AI agents. This project provides a Flask-based OAuth server and a Python SDK for use with agent frameworks like CrewAI.

## Features

- Agent registration and management
- OAuth token issuance with scope control
- Parent-child token hierarchies for delegated tasks
- Task context verification
- Token introspection and revocation
- Comprehensive audit logging
- Admin dashboard
- Python SDK for integration with AI agent frameworks
- Structured logging with Loguru

## Implementation Details

This implementation follows the OAuth flows described in the [blog post](docs/blog.md), including:

1. Agent Registration Flow
2. Basic Client Credentials Flow
3. Parent-Child Agent Hierarchies
4. Token Verification Process
5. Token Introspection and Revocation

## Project Structure

- `app/`: Flask application (OAuth server)
  - `models/`: Database models
  - `routes/`: API routes
  - `templates/`: HTML templates for UI
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
   ./setup-poetry.sh
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
- `GET /api/admin/dashboard`: Admin dashboard

## License

MIT

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. 