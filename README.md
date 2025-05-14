# AgenticTrust API - Secure Authorization for AI Agents

AgenticTrust is a secure authorization framework designed for AI agent ecosystems. It enables safe and controlled interactions between agents and tools by implementing robust authentication, authorization, and policy enforcement mechanisms.

## Current State

AgenticTrust currently provides:

- **OAuth 2.1 compliance** with mandatory PKCE for all flows
- **Authorization Code Flow** with PKCE for web and mobile apps
- **Client Credentials Flow** with PKCE for machine-to-machine authentication
- **Refresh Token** support with PKCE verification
- **Dynamic Client Registration** support
- **Task-aware tokens** with parent-child lineage verification
- **Scope inheritance** from parent to child tasks
- **OIDC-A claims** for agent identity and capabilities
- **Policy-based authorization** using Open Policy Agent (OPA)
- **Comprehensive audit logging** for all token operations

The framework is designed to ensure that AI agents operate within well-defined boundaries, with fine-grained access control for tools and resources through policy-based authorization.

## Planned Auth0 Integration

We are working to make AgenticTrust compatible with Auth0 for agents, implementing features such as:

1. **Human User Model and Authentication**
   - Create user model with authentication fields
   - Implement user registration and login endpoints
   - Add user profile management

2. **User-Agent Authorization Model**
   - Create relationship model between users and agents
   - Implement endpoints to manage user-agent authorizations
   - Add UI components for authorization management

3. **Human-to-Agent Token Delegation**
   - Implement token delegation from human users to agents
   - Create delegation verification mechanisms
   - Add delegation-specific claims to tokens

4. **Policy-Based Authorization for Delegated Tokens**
   - Create human delegation policies in OPA
   - Implement policy checks for delegation
   - Add policy enforcement for resource access

5. **Enhanced Audit Logging for Delegation**
   - Add delegation-specific audit events
   - Implement user activity tracking
   - Create delegation chain visualization

6. **Role-Based Access Control for Agents**
   - Implement RBAC for agent-specific roles
   - Add permission checks to resource access
   - Create role management UI

7. **Multi-Factor Authentication for Critical Operations**
   - Implement MFA for human users
   - Add MFA verification for critical agent operations
   - Create MFA policy configuration

8. **Documentation and SDK Updates**
   - Update API documentation
   - Create delegation examples
   - Update SDK with delegation support

For detailed information on the Auth0 integration plan, see [AUTH0_INTEGRATION.md](AUTH0_INTEGRATION.md).

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

- `agentictrust/`: Core framework code
  - `routers/`: API routes
    - `oauth.py`: OAuth endpoint implementations
    - `agents.py`: Agent management endpoints
    - `tools.py`: Tool management endpoints
  - `core/`: Core business logic
    - `oauth/`: OAuth implementation
      - `engine.py`: OAuth business logic
      - `token_handler.py`: Token lifecycle management
  - `db/`: Database models
    - `models/`: Data models
      - `token.py`: Token model with OIDC-A claims
      - `agent.py`: Agent model
      - `audit/`: Audit logging models
  - `schemas/`: Pydantic models for validation
    - `oauth.py`: OAuth request/response schemas
    - `agents.py`: Agent schemas
    - `tools.py`: Tool schemas
- `demo/`: Demonstration application
  - `app/`: FastAPI application
    - `agent.py`: LLM integration
    - `main.py`: FastAPI application entry point
  - `policies/`: Authorization policies in Rego
    - `authorization.rego`: Base authorization policies
    - `tickets_read.rego`: Policies for ticket read access
    - `tickets_write.rego`: Policies for ticket write access
  - `static/`: Client-side assets
  - `templates/`: HTML templates
- `platform/`: Administrative UI (Next.js)
  - `src/`: Source code
    - `app/dashboard/`: Dashboard pages
    - `components/dashboard/`: Dashboard components
- `docs/`: Documentation
  - `api/`: API documentation
    - `oauth.md`: OAuth API documentation
    - `agents.md`: Agent API documentation
    - `tools.md`: Tool API documentation
- `Makefile`: Development environment orchestration

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/lab101-ai/agentictrust.git
   cd agentictrust
   ```

2. Using Poetry (recommended):
   ```
   poetry install
   poetry shell
   ```

3. Using pip (alternative):
   ```
   pip install -r requirements.txt
   ```

## Running the Server

Using the Makefile (recommended):
```
make server
```

This will start:
- OPA server on port 8181
- AgenticTrust server on port 8000

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
- `GET /api/oauth/authorize`: Authorization endpoint

### Tools
- `POST /api/tools/register`: Register a new tool
- `GET /api/tools/list`: List all registered tools
- `GET /api/tools/<tool_id>`: Get tool details
- `DELETE /api/tools/<tool_id>`: Delete a tool

For detailed API documentation, see the `/docs/api/` directory.

## Demo Application

The project includes a customer support demo application that showcases how the framework can be used to build a secure AI-powered application with proper access controls.

To run the demo:
```
cd demo
pip install -r requirements.txt
python app/main.py
```

The demo will be available at http://localhost:8080.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT    