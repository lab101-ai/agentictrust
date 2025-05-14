# Human-to-Agent Delegation in AgenticTrust

This document describes how to use the human-to-agent delegation features in AgenticTrust.

## Overview

AgenticTrust supports delegation of tokens from human users to AI agents, allowing agents to act on behalf of users with appropriate permissions and constraints. This delegation is secured through:

1. User-Agent Authorization model
2. Policy-based authorization
3. Multi-factor authentication for critical operations
4. Comprehensive audit logging

## User-Agent Authorization

Before an agent can receive delegated tokens from a user, the user must explicitly authorize the agent:

```python
# Create user-agent authorization
authorization = UserAgentAuthorization.create(
    user_id="user-123",
    agent_id="agent-456",
    scopes=["read:data", "write:data"],
    constraints={"time_restrictions": {"start_hour": 9, "end_hour": 17}},
    ttl_days=30
)
```

## Delegating Tokens

Once authorized, tokens can be delegated from a human user to an agent:

```python
# Request delegated token
response = requests.post(
    "https://api.example.com/oauth/delegate",
    json={
        "client_id": "agent-456",
        "delegation_type": "human_to_agent",
        "delegator_token": "user-auth0-token",
        "scope": ["read:data"],
        "task_description": "Analyze user data",
        "task_id": "task-789",
        "purpose": "Data analysis"
    }
)

# Use delegated token
delegated_token = response.json()["access_token"]
```

## MFA for Critical Operations

For sensitive operations, multi-factor authentication can be required:

```python
# Create MFA challenge
challenge_response = requests.post(
    "https://api.example.com/users/user-123/mfa/challenge",
    params={"operation_type": "token_delegation"}
)

challenge_id = challenge_response.json()["challenge_id"]

# Verify MFA challenge
requests.post(
    "https://api.example.com/users/user-123/mfa/challenge/verify",
    json={
        "challenge_id": challenge_id,
        "code": "123456"  # TOTP code from authenticator app
    }
)

# Request delegated token with MFA
response = requests.post(
    "https://api.example.com/oauth/delegate/mfa",
    json={
        "client_id": "agent-456",
        "delegation_type": "human_to_agent",
        "delegator_token": "user-auth0-token",
        "scope": ["read:data", "write:data"],
        "task_description": "Update user data",
        "task_id": "task-789",
        "purpose": "Data update"
    },
    params={
        "mfa_challenge_id": challenge_id,
        "mfa_code": "123456"
    }
)
```

## Audit Logging

All delegation events are logged and can be retrieved:

```python
# Get delegation chain for a token
response = requests.get(
    "https://api.example.com/api/audit/delegation/token-123/chain"
)

# Get delegation activity for a user
response = requests.get(
    "https://api.example.com/api/audit/delegation/user/user-123"
)
```

## Role-Based Access Control

Agents can be assigned roles with specific permissions:

```python
# Create role
role = Role.create(
    name="data_analyst",
    description="Can analyze user data"
)

# Create permission
permission = Permission.create(
    name="read_user_data",
    resource="user_data",
    action="read",
    description="Can read user data"
)

# Add permission to role
role.add_permission(permission)

# Assign role to agent
agent = Agent.query.get("agent-456")
agent.roles.append(role)
db_session.commit()
```

## Policy-Based Authorization

Policies control when and how agents can act on behalf of users:

```rego
# Example policy in Rego (OPA)
package agentictrust.delegation

allow if {
    # Check if user has authorized this agent
    input.authorization.is_active == true
    
    # Check if requested scopes are subset of authorized scopes
    is_scope_subset(input.requested_scopes, input.authorization.scopes)
}
```

## Integration with Auth0

AgenticTrust can use Auth0 for human user authentication:

```python
# Login with Auth0
response = requests.get("https://api.example.com/login/auth0")
# User is redirected to Auth0 for authentication

# Exchange Auth0 token for AgenticTrust token
response = requests.post(
    "https://api.example.com/auth0/token",
    json={"auth0_token": "user-auth0-token"}
)
```
