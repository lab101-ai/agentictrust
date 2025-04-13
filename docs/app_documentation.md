# AgenticTrust Flask Application Documentation

## Overview

The AgenticTrust application is a secure OAuth 2.1-based system designed specifically for LLM-based agents. It provides a comprehensive framework for agent authentication, authorization, and task management with a strong focus on security, auditability, and hierarchical token-based permissions. This system enables secure delegation of tasks between AI agents while maintaining strict scope control and comprehensive audit trails.

## Application Structure

The application follows a modular Flask structure with clear separation of concerns:

```
app/
├── __init__.py          # Application factory, middleware and error handling
├── models/              # Database models
│   ├── __init__.py      # Database initialization
│   ├── agent.py         # Agent definition and authentication
│   ├── token.py         # OAuth token management with JWT support
│   ├── audit.py         # Comprehensive task auditing system
│   └── tool.py          # Tool definitions with permission requirements
├── routes/              # API endpoints
│   ├── __init__.py      # Blueprint registration
│   ├── agents.py        # Agent management endpoints
│   ├── oauth.py         # OAuth 2.1 flow endpoints with PKCE
│   ├── admin.py         # Admin dashboard endpoints
│   └── tools.py         # Tool management endpoints
└── utils/               # Utility functions
    ├── __init__.py      # Utility initialization and shared functions
    ├── config.py        # YAML-based configuration loader
    ├── logger.py        # Structured logging system
    └── oauth.py         # OAuth utility functions and token verification
```

## Core Components

### Application Factory

The application uses a factory pattern defined in `app/__init__.py`, which enables flexible configuration, testing environments, and proper dependency initialization.

```python
def create_app(config=None):
    app = Flask(__name__, static_folder=None, template_folder=None)
    
    # Load configuration from YAML file with fallback mechanism
    try:
        from app.utils.config import load_config
        flask_config = load_config("flask")
        app.config.update(flask_config)
    except (ImportError, FileNotFoundError):
        # Fallback to old configuration method
        app.config.from_object('config.Config')
    
    # Override with environment-specific config
    if config:
        app.config.update(config)
    
    # Configure database URI
    if "DATABASE_URI" in app.config:
        app.config["SQLALCHEMY_DATABASE_URI"] = app.config["DATABASE_URI"]
        app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    
    # Initialize extensions with app
    db.init_app(app)
    migrate.init_app(app, db)
    
    # Configure CORS based on settings
    cors_origins = app.config.get("CORS_ORIGINS", "*")
    CORS(app, resources={r"/*": {"origins": cors_origins}})
    
    # Request logging middleware setup
    @app.before_request
    def before_request():
        request_id = request.headers.get('X-Request-ID', str(uuid.uuid4()))
        request.request_id = request_id
        request.start_time = time.time()
        logger.bind(request_id=request_id).info(
            f"Request started: {request.method} {request.path}"
        )

    # Comprehensive error handlers for various status codes
    # Enhanced global exception handling
    
    # Register blueprints
    from app.routes.agents import agents_bp
    from app.routes.oauth import oauth_bp
    from app.routes.admin import admin_bp
    from app.routes.tools import tools_bp
    
    app.register_blueprint(agents_bp)
    app.register_blueprint(oauth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(tools_bp)
    
    return app
```

### Database Models

#### Agent

Agents represent LLM-based systems that can request access tokens:

- `client_id`: Unique identifier (UUID)
- `client_secret_hash`: Hashed authentication credential using Werkzeug security
- `agent_name`: Human-readable name
- `description`: Detailed agent purpose and capabilities
- `allowed_resources`: List of resources the agent can access (JSON array)
- `max_scope_level`: Maximum permission level (tiered access control)
- `is_active`: Whether the agent is active
- `created_at`: Timestamp of agent registration
- `registration_token`: One-time token for agent activation
- `registration_expires_at`: Expiration time for registration token

#### IssuedToken

Tokens represent authorized access credentials with JWT implementation:

- `token_id`: Unique token identifier (UUID)
- `client_id`: Associated agent (foreign key)
- `access_token_hash`: Securely hashed token value
- `refresh_token_hash`: Securely hashed refresh token
- `scope`: Permissions granted to this token (JSON array)
- `granted_tools`: Specific tools token can access (JSON array)
- `task_id`: Associated task identifier for context tracking
- `parent_task_id`: Parent task (for hierarchical workflows)
- `parent_token_id`: Parent token (for token inheritance)
- `task_description`: Human-readable description of the task
- `scope_inheritance_type`: How scope is inherited from parent ('restricted' or 'full')
- `issued_at`: Timestamp of token issuance
- `expires_at`: Token expiration time
- `is_revoked`: Revocation status
- `revoked_at`: Timestamp of revocation, if applicable
- `revocation_reason`: Reason for revocation, if any
- `code_challenge`: PKCE code challenge for authorization code flow
- `code_challenge_method`: PKCE challenge method ('plain' or 'S256')
- `authorization_code_hash`: Hashed authorization code for OAuth flow

The token model supports multiple token verification methods and implements parent-child relationships for token inheritance, enabling controlled delegation of permissions.

#### TaskAuditLog

Comprehensive audit trail for all agent actions with error handling:

- `log_id`: Unique audit log identifier (UUID)
- `client_id`: Agent that performed the action
- `token_id`: Token used for authorization (can be error token)
- `access_token_hash`: Hash of the access token used
- `task_id`: Task identifier for event context
- `parent_task_id`: Parent task (if part of a workflow)
- `event_type`: Type of action performed (token_issued, api_access, etc.)
- `timestamp`: When the event occurred
- `status`: Success/failure status of the operation
- `source_ip`: IP address source of the request
- `details`: Additional event context as JSON

The audit system includes specialized handling for errors that occur before a token exists, using synthetic error tokens to maintain the audit trail integrity.

#### Tool

Tools that agents can use to perform tasks:

- `tool_id`: Unique tool identifier (UUID)
- `name`: Tool name (must be unique)
- `description`: Detailed tool purpose and behavior
- `version`: Tool version for tracking changes
- `permissions_required`: Required OAuth scopes as JSON array
- `resources_required`: Resources needed by the tool
- `parameters`: Expected parameters schema as JSON
- `return_schema`: Expected return value schema as JSON
- `is_active`: Whether the tool is available for use
- `created_at`: When the tool was registered
- `updated_at`: When the tool was last updated
- `owner_client_id`: Agent that owns/created the tool

## API Endpoints

### Agent Management (`/api/agents/`)

- `POST /api/agents/register`: Register a new agent with name, description, allowed resources, and scope level
- `POST /api/agents/activate`: Activate an agent using its registration token
- `GET /api/agents/list`: List all registered agents (admin only)
- `GET /api/agents/<client_id>`: Get agent details by ID (admin or self)
- `GET /api/agents/me`: Get current agent details (requires authentication)
- `PUT /api/agents/<client_id>`: Update agent properties (admin only)
- `DELETE /api/agents/<client_id>`: Deactivate an agent (admin only)

### OAuth Flow (`/api/oauth/`)

- `GET /api/oauth/authorize`: OAuth 2.1 authorization endpoint with PKCE support
- `POST /api/oauth/token`: Token endpoint supporting multiple grant types:
  - `authorization_code`: Exchange code for tokens (with PKCE verification)
  - `client_credentials`: Direct client authentication flow
  - `refresh_token`: Get new access token using refresh token
- `POST /api/oauth/verify`: Verify token validity and permissions
- `POST /api/oauth/verify/tool`: Verify if token has permission to use specific tool
- `POST /api/oauth/introspect`: Get detailed token information
- `POST /api/oauth/revoke`: Revoke active tokens
- `GET /api/oauth/.well-known/oauth-authorization-server`: Metadata endpoint (RFC 8414)
- `GET /api/oauth/protected`: Example protected endpoint
- `POST /api/oauth/validation-test`: Endpoint for testing validation scenarios
- `POST /api/oauth/register-client`: Dynamic client registration endpoint

### Admin Dashboard (`/api/admin/`)

- `GET /api/admin/tokens`: List all issued tokens with filtering options
- `GET /api/admin/tokens/<token_id>`: Get detailed token information
- `GET /api/admin/tokens/revoke/<token_id>`: Revoke specific token
- `GET /api/admin/audit`: View comprehensive audit logs with filtering
- `GET /api/admin/audit/task/<task_id>`: Get audit trail for specific task
- `GET /api/admin/audit/agent/<client_id>`: Get audit logs for specific agent
- `GET /api/admin/audit/task-chain/<task_id>`: Get full task lineage (parent/child relationships)
- `GET /api/admin/dashboard`: Get system statistics and metrics

### Tool Management (`/api/tools/`)

- `GET /api/tools`: List available tools with optional filtering
- `GET /api/tools/<tool_id>`: Get detailed tool information
- `POST /api/tools`: Register a new tool with permission requirements
- `PUT /api/tools/<tool_id>`: Update tool properties
- `DELETE /api/tools/<tool_id>`: Deactivate or delete a tool
- `GET /api/tools/my-tools`: List tools available to authenticated agent
- `POST /api/tools/execute/<tool_id>`: Execute tool (if supported by implementation)

## Detailed API Reference

This section provides comprehensive documentation for each API endpoint, including request parameters, response formats, and authentication requirements.

### Authentication

Most endpoints require OAuth 2.1 token authentication, which can be provided in one of these ways:

- Bearer token in Authorization header: `Authorization: Bearer {access_token}`
- Query parameter: `?access_token={access_token}`

All authenticated requests must include task context headers:
- `X-Task-ID`: Current task identifier (UUID format)
- `X-Parent-Task-ID`: Parent task identifier if part of a workflow (UUID format)
- `X-Parent-Token`: Parent OAuth token for task delegation scenarios
- `X-Parent-Tokens`: Multiple parent tokens for complex delegation (comma-separated list)

The system implements multiple validation layers:
1. **Token validation**: Verifies the token exists and is not expired/revoked
2. **Task context validation**: Ensures proper task lineage and parent relationships
3. **Scope validation**: Checks if token has appropriate permissions
4. **Tool-specific validation**: Verifies token has permission to use specific tools
5. **Token inheritance verification**: Validates permission inheritance from parent tokens

### Agent Endpoints

#### Register a New Agent

```
POST /api/agents/register
```

Registers a new AI agent in the system.

**Request Body:**
```json
{
  "agent_name": "Example Agent",
  "description": "This agent performs analysis tasks",
  "allowed_resources": ["calendar", "email"],
  "max_scope_level": "restricted"
}
```

**Response:**
```json
{
  "client_id": "5a8e41f3-db53-4986-a60f-3c53c3522153",
  "client_secret": "randomly_generated_secret",
  "registration_token": "token_for_activation",
  "agent_name": "Example Agent",
  "description": "This agent performs analysis tasks",
  "allowed_resources": ["calendar", "email"],
  "max_scope_level": "restricted",
  "is_active": false
}
```

**Note:** The client_secret is only returned once during registration and should be securely stored.

#### List All Agents

```
GET /api/agents/list
```

Returns a list of all registered agents.

**Response:**
```json
{
  "agents": [
    {
      "client_id": "5a8e41f3-db53-4986-a60f-3c53c3522153",
      "agent_name": "Example Agent",
      "description": "This agent performs analysis tasks",
      "allowed_resources": ["calendar", "email"],
      "max_scope_level": "restricted",
      "is_active": true,
      "created_at": "2023-04-01T12:00:00Z",
      "updated_at": "2023-04-01T12:00:00Z",
      "tools": [{"tool_id": "123", "name": "calendar_reader"}]
    }
  ]
}
```

#### Get Agent Details

```
GET /api/agents/{client_id}
```

Returns details for a specific agent.

**Response:**
```json
{
  "client_id": "5a8e41f3-db53-4986-a60f-3c53c3522153",
  "agent_name": "Example Agent",
  "description": "This agent performs analysis tasks",
  "allowed_resources": ["calendar", "email"],
  "max_scope_level": "restricted",
  "is_active": true,
  "created_at": "2023-04-01T12:00:00Z",
  "updated_at": "2023-04-01T12:00:00Z",
  "tools": [{"tool_id": "123", "name": "calendar_reader"}]
}
```

#### Get Current Agent

```
GET /api/agents/me
```

Returns the details of the authenticated agent.

**Authentication Required:** Yes

**Response:** Same format as the "Get Agent Details" endpoint

### OAuth Endpoints

#### Request Access Token (Client Credentials Flow)

```
POST /api/oauth/token
```

Issues an access token using client credentials flow.

**Request Body:**
```json
{
  "client_id": "5a8e41f3-db53-4986-a60f-3c53c3522153",
  "client_secret": "your_client_secret",
  "grant_type": "client_credentials",
  "scope": ["read:calendar", "write:tasks"],
  "task_id": "task-123456",
  "parent_task_id": "parent-task-123",
  "parent_token": "parent_oauth_token",
  "task_description": "Read calendar events and create tasks"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "Bearer",
  "expires_in": 3600,
  "scope": ["read:calendar", "write:tasks"],
  "task_id": "task-123456",
  "granted_tools": ["calendar_reader", "tasks_writer"],
  "parent_task_id": "parent-task-123",
  "parent_token_id": "parent-token-uuid"
}
```

#### Refresh Token

```
POST /api/oauth/token/refresh
```

Refreshes an expired access token.

**Request Body:**
```json
{
  "client_id": "5a8e41f3-db53-4986-a60f-3c53c3522153",
  "refresh_token": "your_refresh_token",
  "grant_type": "refresh_token"
}
```

**Response:** Same format as the token endpoint response

#### Revoke Token

```
POST /api/oauth/revoke
```

Revokes an active token.

**Request Body:**
```json
{
  "token": "access_or_refresh_token",
  "token_type_hint": "access_token",
  "client_id": "5a8e41f3-db53-4986-a60f-3c53c3522153"
}
```

**Response:**
```json
{
  "message": "Token revoked successfully"
}
```

#### Protected Resource Example

```
GET /api/oauth/protected
```

Example of an endpoint that requires valid token authentication and task context verification.

**Authentication Required:** Yes

**Response:**
```json
{
  "message": "Access granted to protected resource",
  "agent": {
    "client_id": "5a8e41f3-db53-4986-a60f-3c53c3522153",
    "agent_name": "Example Agent"
  },
  "token": {
    "token_id": "token-uuid",
    "scope": ["read:calendar"],
    "task_id": "task-123456"
  }
}
```

### Admin Endpoints

#### List All Tokens

```
GET /api/admin/tokens
```

Returns a list of all issued tokens.

**Response:**
```json
{
  "tokens": [
    {
      "token_id": "token-uuid",
      "client_id": "5a8e41f3-db53-4986-a60f-3c53c3522153",
      "scope": ["read:calendar"],
      "task_id": "task-123456",
      "parent_task_id": "parent-task-123",
      "issued_at": "2023-04-01T12:00:00Z",
      "expires_at": "2023-04-01T13:00:00Z",
      "is_revoked": false,
      "is_valid": true
    }
  ]
}
```

#### Get Token Details

```
GET /api/admin/tokens/{token_id}
```

Returns details for a specific token.

**Query Parameters:**
- `include_children`: Boolean to include child tokens (default: false)

**Response:**
```json
{
  "token_id": "token-uuid",
  "client_id": "5a8e41f3-db53-4986-a60f-3c53c3522153",
  "scope": ["read:calendar"],
  "granted_tools": ["calendar_reader"],
  "granted_resources": ["calendar"],
  "task_id": "task-123456",
  "parent_task_id": "parent-task-123",
  "parent_token_id": "parent-token-uuid",
  "task_description": "Read calendar events",
  "scope_inheritance_type": "restricted",
  "issued_at": "2023-04-01T12:00:00Z",
  "expires_at": "2023-04-01T13:00:00Z",
  "is_revoked": false,
  "is_valid": true,
  "child_tokens": []
}
```

#### View Audit Logs

```
GET /api/admin/audit
```

Returns the audit logs for monitoring agent activity.

**Query Parameters:**
- `client_id`: Filter by agent
- `task_id`: Filter by task
- `event_type`: Filter by event type
- `status`: Filter by status
- `from_date`: Filter by date range start
- `to_date`: Filter by date range end

**Response:**
```json
{
  "logs": [
    {
      "log_id": "log-uuid",
      "client_id": "5a8e41f3-db53-4986-a60f-3c53c3522153",
      "token_id": "token-uuid",
      "task_id": "task-123456",
      "parent_task_id": "parent-task-123",
      "event_type": "api_call",
      "timestamp": "2023-04-01T12:05:00Z",
      "status": "success",
      "source_ip": "192.168.1.1",
      "details": {
        "endpoint": "/api/calendar/events",
        "method": "GET"
      }
    }
  ]
}
```

### Tool Endpoints

#### List Tools

```
GET /api/tools
```

Returns a list of available tools.

**Query Parameters:**
- `category`: Filter by tool category
- `is_active`: Filter by active status

**Response:**
```json
{
  "tools": [
    {
      "tool_id": "tool-uuid",
      "name": "calendar_reader",
      "description": "Reads calendar events",
      "category": "calendar",
      "permissions_required": ["read:calendar"],
      "inputSchema": {
        "type": "object",
        "properties": {
          "start_date": {
            "type": "string",
            "format": "date",
            "required": true
          },
          "end_date": {
            "type": "string",
            "format": "date",
            "required": true
          }
        }
      },
      "is_active": true,
      "created_at": "2023-03-01T12:00:00Z",
      "updated_at": "2023-03-01T12:00:00Z"
    }
  ]
}
```

#### Get Tool Details

```
GET /api/tools/{tool_id}
```

Returns details for a specific tool.

**Response:**
```json
{
  "tool_id": "tool-uuid",
  "name": "calendar_reader",
  "description": "Reads calendar events",
  "category": "calendar",
  "permissions_required": ["read:calendar"],
  "inputSchema": {
    "type": "object",
    "properties": {
      "start_date": {
        "type": "string",
        "format": "date",
        "required": true
      },
      "end_date": {
        "type": "string",
        "format": "date",
        "required": true
      }
    }
  },
  "is_active": true,
  "created_at": "2023-03-01T12:00:00Z",
  "updated_at": "2023-03-01T12:00:00Z"
}
```

#### Register a New Tool

```
POST /api/tools
```

Registers a new tool in the system.

**Request Body:**
```json
{
  "name": "email_sender",
  "description": "Sends emails on behalf of the user",
  "category": "communication",
  "permissions_required": ["write:email"],
  "inputSchema": {
    "type": "object",
    "properties": {
      "recipient": {
        "type": "string",
        "description": "email"
      },
      "subject": {
        "type": "string"
      },
      "body": {
        "type": "string"
      }
    },
    "required": ["recipient", "subject", "body"]
  }
}
```

**Response:**
```json
{
  "message": "Tool registered successfully",
  "tool": {
    "tool_id": "new-tool-uuid",
    "name": "email_sender",
    "description": "Sends emails on behalf of the user",
    "category": "communication",
    "permissions_required": ["write:email"],
    "inputSchema": {
      "type": "object",
      "properties": {
        "recipient": {
          "type": "string",
          "description": "email"
        },
        "subject": {
          "type": "string"
        },
        "body": {
          "type": "string"
        }
      },
      "required": ["recipient", "subject", "body"]
    },
    "is_active": true,
    "created_at": "2023-04-01T12:00:00Z",
    "updated_at": "2023-04-01T12:00:00Z"
  }
}
```

**Note:** The API supports both `inputSchema` and `parameters` field names, with `inputSchema` taking precedence if both are provided. In responses, the field is always returned as `inputSchema`.

#### Delete a Tool

```
DELETE /api/tools/{tool_id}
```

Deletes a tool from the system.

**Response:**
```json
{
  "message": "Tool deleted successfully"
}
```

### Tool Schema Format

The `inputSchema` field uses JSON Schema format to define the input structure for the tool. The following is supported:

- **Basic Types:** string, number, boolean, integer, object, array
- **Validation Keywords:** required, description, enum
- **Complex Structures:** anyOf, oneOf, allOf

#### Example Schemas

**Simple Command Execution:**
```json
{
  "type": "object",
  "properties": {
    "command": { "type": "string" },
    "args": { "type": "array", "items": { "type": "string" } }
  },
  "required": ["command"]
}
```

**Data Analysis Tool:**
```json
{
  "type": "object",
  "properties": {
    "filepath": { "type": "string" },
    "operations": {
      "type": "array",
      "items": {
        "enum": ["sum", "average", "count"]
      }
    }
  },
  "required": ["filepath"]
}
```

**Calculator:**
```json
{
  "type": "object",
  "properties": {
    "a": { "type": "number" },
    "b": { "type": "number" }
  },
  "required": ["a", "b"]
}
```

## Error Handling

All API endpoints return standard HTTP status codes and a JSON error object:

**Error Response Format:**
```json
{
  "error": "error_code",
  "message": "Human-readable error message",
  "details": {
    "additional": "error details"
  }
}
```

**Common Error Codes:**

| HTTP Status | Error Code | Description |
|-------------|------------|-------------|
| 400 | invalid_request | The request is malformed or missing required parameters |
| 401 | unauthorized | Authentication is required or credentials are invalid |
| 403 | forbidden | The authenticated agent lacks sufficient permissions |
| 404 | not_found | The requested resource does not exist |
| 409 | conflict | The request conflicts with the current state |
| 429 | too_many_requests | The agent has exceeded rate limits |
| 500 | server_error | An unexpected server error occurred |

## Security Features

### JWT-Based Tokens with Enhanced Verification

The system uses JWT (JSON Web Tokens) with multiple security layers:

- Tokens contain embedded metadata (token_id, client_id, task context, scope)
- Server-side token hashing prevents token reuse after revocation
- Expiration times are enforced both at JWT level and database level
- PKCE (Proof Key for Code Exchange) implementation for authorization code flow
- Multiple token verification methods for flexibility and security

### Hierarchical Token Delegation with Scope Restriction

The system supports hierarchical token delegation where parent tokens can create child tokens with equal or reduced scope. This ensures that permissions can be delegated safely without escalation.

- Child tokens must have scope ⊆ parent scope (strictly enforced)
- Task lineage is maintained through the entire delegation chain
- Token chain verification prevents permission bypass attacks
- Support for multiple parent tokens for complex delegation scenarios
- Two scope inheritance types: 'restricted' (default) and 'full'

### Task Context Validation and Lineage Tracking

Every authenticated API request requires comprehensive task context:

- Task ID uniquely identifies the specific operation
- Parent task ID maintains hierarchical workflow relationships
- System validates that token was issued specifically for the claimed task
- Complete task lineage tracking for auditing entire process chains
- Parent-child task relationship validation to prevent context manipulation

### Tool-Specific Authorization

The system implements fine-grained tool-based authorization:

- Tools define required permissions (scopes) and resources
- Token validation includes tool-specific permission checks
- Tool execution is controlled based on token permissions
- Comprehensive tool metadata including parameter schemas

### Comprehensive Audit System with Error Handling

All operations are comprehensively logged with specialized error handling:

- Token issuance, validation, and revocation events
- All API access attempts (both successful and failed)
- Permission checks and access control decisions
- Complete task chain tracking for process lineage
- Error handling to capture authentication failures before token issuance
- Synthetic error tokens to maintain audit trail integrity
- IP address tracking and request context preservation

### Request Logging and Middleware

All requests are automatically logged with:

- Request ID (UUID for traceability)
- Method and path
- Duration for performance monitoring
- Status code and response information
- Error details when applicable

The application implements middleware for:

- Structured request logging
- Flexible CORS configuration
- Multi-layer authentication verification
- Complete task context validation
- Global exception handling with detailed error responses

## Deployment and Implementation Details

### Configuration System

The application uses a flexible YAML-based configuration system:

```yaml
flask:
  SECRET_KEY: your-secure-random-key
  DATABASE_URI: sqlite:///app.db  # For development
  # DATABASE_URI: postgresql://user:password@localhost/agentictrust  # For production
  DEBUG: false
  ACCESS_TOKEN_EXPIRY: 3600  # seconds
  REFRESH_TOKEN_EXPIRY: 2592000  # 30 days in seconds
  AUTHORIZATION_CODE_EXPIRY: 600  # 10 minutes in seconds
  CORS_ORIGINS: "*"  # Set to specific domains in production
  LOG_LEVEL: "INFO"
  MAX_TOKEN_DEPTH: 5  # Maximum depth of token delegation chain
```

Configuration loading is implemented with fallback mechanisms:
1. First attempts to load from YAML files in the config directory
2. Falls back to Python-based config if YAML loading fails
3. Supports environment-specific overrides

### Database Setup and Migration

The application uses Flask-SQLAlchemy and Flask-Migrate for database management:

```bash
# Initialize the migration repository
flask db init

# Create initial migration
flask db migrate -m "Initial schema"

# Apply migrations to the database
flask db upgrade
```

Database models support both SQLite (development) and PostgreSQL (production) with JSON field types.

### Request Logging and Error Handling

The application implements comprehensive request logging and error handling:

- Every request receives a unique request_id for traceability
- Request duration is captured for performance monitoring
- Structured logging with contextual information
- Enhanced error responses with detailed information for OAuth errors
- Global exception handler for consistent error reporting

### Security Recommendations

For production deployments:

- **Transport Security**:
  - Use HTTPS with valid TLS certificates
  - Implement strict transport security headers
  - Configure proper CORS settings for allowed origins

- **Secret Management**:
  - Set a strong SECRET_KEY using a cryptographically secure generator
  - Use environment variables for sensitive configuration
  - Rotate secrets periodically

- **Access Control**:
  - Implement IP-based access restrictions for admin endpoints
  - Use rate limiting to prevent abuse
  - Regularly audit issued tokens and agent permissions

- **Database Security**:
  - Use PostgreSQL in production for better security and performance
  - Implement database connection pooling
  - Configure proper database user permissions

- **Monitoring and Alerting**:
  - Set up alerts for suspicious token issuance patterns
  - Monitor failed authentication attempts
  - Track token usage patterns for anomaly detection

## Running the Application

The application can be started using:

```python
# run.py
from app import create_app, db
app = create_app()

if __name__ == '__main__':
    host = app.config.get('HOST', '127.0.0.1')
    port = app.config.get('PORT', 5001)
    debug = app.config.get('DEBUG', True)
    
    with app.app_context():
        db.create_all()
        
    app.run(host=host, port=port, debug=debug)
```

## Environment Variables and Configuration

The application can be configured using environment variables or YAML configuration:

### Core Environment Variables

- `FLASK_APP`: Entry point (default: app:create_app())
- `FLASK_ENV`: Environment (development, production)
- `SECRET_KEY`: Secret key for sessions and tokens
- `DATABASE_URI`: Database connection string
- `LOG_LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR)
- `PORT`: Application port

### Advanced Configuration

- `CORS_ORIGINS`: Comma-separated list of allowed origins for CORS
- `ACCESS_TOKEN_EXPIRY`: Access token lifetime in seconds (default: 3600)
- `REFRESH_TOKEN_EXPIRY`: Refresh token lifetime in seconds (default: 2592000)
- `AUTHORIZATION_CODE_EXPIRY`: Authorization code lifetime in seconds (default: 600)
- `MAX_TOKEN_DEPTH`: Maximum depth for token delegation chain (default: 5)
- `ENABLE_JWT_COMPRESSION`: Enable/disable JWT compression (default: false)
- `JWT_ALGORITHM`: Algorithm for JWT tokens (default: HS256)
- `ENABLE_DYNAMIC_CLIENT_REGISTRATION`: Enable dynamic client registration (default: false)

### Configuration Precedence

The system loads configuration in this order of precedence:

1. Environment variables (highest priority)
2. YAML configuration files
3. Default application settings

This allows for flexible configuration across different deployment environments while maintaining consistency. 