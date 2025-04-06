# AgenticTrust OAuth Server Documentation

This documentation provides information about the AgenticTrust OAuth Server, a secure OAuth 2.1-based authentication and authorization framework specifically designed for LLM-based agents.

## Table of Contents

1. [Introduction](#introduction)
2. [Architecture](#architecture)
3. [Key Features](#key-features)
4. [Authentication Flows](#authentication-flows)
5. [Authorization and Scope Control](#authorization-and-scope-control)
6. [Task-Level OAuth Verification](#task-level-oauth-verification)
7. [API Reference](#api-reference)
8. [Security Considerations](#security-considerations)
9. [Audit Logging](#audit-logging)

## Introduction

The AgenticTrust OAuth Server is designed to provide a secure authentication and authorization framework for LLM-based agents (e.g., Operators, LangChain agents). It ensures that each agent action is traceable, scope-constrained, and verified through parent-child OAuth context.

The server implements OAuth 2.1 standards with enhancements specifically tailored for AI agent needs, including task-level verification, hierarchical token lineage, and comprehensive audit logging.

## Architecture

The AgenticTrust OAuth Server is built using FastAPI, a modern Python web framework, and SQLAlchemy for database operations. It follows a modular architecture with the following components:

- **Authentication Module**: Handles token generation, validation, and revocation.
- **Authorization Module**: Manages scopes and permissions.
- **Audit Module**: Records all authentication and authorization activities.
- **Database Layer**: Stores users, clients, tokens, and audit logs.

## Key Features

### Authentication Mechanisms

- **OAuth 2.1 Client Credentials Grant**: For machine-to-machine authentication between agents and services.
- **Password Grant**: For user-based authentication.
- **Refresh Token Flow**: For obtaining new access tokens without re-authentication.
- **Token Introspection**: For validating tokens and obtaining token information.
- **Token Revocation**: For invalidating tokens when they are no longer needed.

### Security Features

- **Short-lived Tokens**: Default 1-hour expiration for access tokens.
- **Refresh Tokens**: For maintaining long-lived sessions without compromising security.
- **Secure Password Hashing**: Using bcrypt for password storage.
- **Rate Limiting**: Configurable rate limits to prevent abuse.

## Authentication Flows

### Client Credentials Flow

The Client Credentials flow is used for machine-to-machine authentication, where a client authenticates with its client ID and client secret to obtain an access token.

```
POST /auth/token
Content-Type: application/x-www-form-urlencoded

grant_type=client_credentials
&client_id=YOUR_CLIENT_ID
&client_secret=YOUR_CLIENT_SECRET
&scope=read:calendar read:inventory
&task_id=TASK_ID
&parent_task_id=PARENT_TASK_ID
&parent_token=PARENT_TOKEN
```

Response:

```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer",
  "expires_in": 3600,
  "refresh_token": "def502009a9a212..",
  "scope": "read:calendar read:inventory"
}
```

### Password Flow

The Password flow is used when an application exchanges a user's credentials for an access token.

```
POST /auth/token
Content-Type: application/x-www-form-urlencoded

grant_type=password
&client_id=YOUR_CLIENT_ID
&client_secret=YOUR_CLIENT_SECRET
&username=user@example.com
&password=user_password
&scope=read:calendar read:inventory
```

Response:

```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer",
  "expires_in": 3600,
  "refresh_token": "def502009a9a212..",
  "scope": "read:calendar read:inventory"
}
```

## Authorization and Scope Control

Scopes are used to define the permissions that an access token grants. The AgenticTrust OAuth Server supports fine-grained scope control with the following predefined scopes:

- `read:calendar`: Read calendar events
- `write:calendar`: Create or modify calendar events
- `read:inventory`: Read inventory data
- `write:inventory`: Modify inventory data
- `admin`: Full administrative access

Clients are assigned specific scopes when they are created, and tokens can only be issued with scopes that the client has been authorized to use.

## Task-Level OAuth Verification

A unique feature of the AgenticTrust OAuth Server is task-level OAuth verification. This allows tokens to be bound to specific tasks and their parent tasks, creating a hierarchical token lineage that can be verified.

When a token is requested for a subtask, the parent task's token must be provided for verification. This ensures that tokens are only used within their intended execution flow and improves traceability.

### Token Verification

```
POST /auth/verify
Content-Type: application/json

{
  "token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "scopes": ["read:calendar"],
  "task_id": "subtask-123",
  "parent_task_id": "parent-task-456",
  "parent_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

Response:

```json
{
  "is_valid": true,
  "scopes": ["read:calendar", "read:inventory"],
  "user_id": 1,
  "client_id": "client-123",
  "expires_at": "2023-04-01T12:00:00"
}
```

## API Reference

### Authentication Endpoints

#### POST /auth/token

Create a new access token.

Parameters:
- `grant_type` (required): The grant type (client_credentials, password, refresh_token)
- `client_id` (required): The client ID
- `client_secret` (required for client_credentials): The client secret
- `username` (required for password): The username
- `password` (required for password): The password
- `refresh_token` (required for refresh_token): The refresh token
- `scope` (optional): Space-delimited list of requested scopes
- `task_id` (optional): The current task ID
- `parent_task_id` (optional): The parent task ID
- `parent_token` (optional): The parent token

#### POST /auth/verify

Verify a token and check if it has the required scopes.

Parameters:
- `token` (required): The token to verify
- `scopes` (optional): List of scopes to check
- `task_id` (optional): The current task ID
- `parent_task_id` (optional): The parent task ID
- `parent_token` (optional): The parent token

#### POST /auth/introspect

Get detailed information about a token.

Parameters:
- `token` (required): The token to introspect

#### POST /auth/revoke

Revoke a token.

Parameters:
- `token` (required): The token to revoke
- `token_type_hint` (optional): The type of token to revoke (access_token, refresh_token)

## Security Considerations

### Token Storage

Access tokens and refresh tokens should be stored securely. Access tokens should be stored in memory when possible, while refresh tokens may be stored in secure HTTP-only cookies or encrypted storage.

### Token Transmission

Tokens should only be transmitted over HTTPS to prevent interception.

### Token Expiration

Access tokens have a default expiration of 1 hour. This can be configured in the settings.

### Client Secret Protection

Client secrets should be protected and never exposed to users or in client-side code.

## Audit Logging

The AgenticTrust OAuth Server logs all authentication and authorization events for auditing purposes. Audit logs include:

- Timestamp
- User ID
- Client ID
- Action (token.create, token.verify, token.introspect, token.revoke)
- Resource
- Task ID
- Parent Task ID
- Scopes
- Status (success, failure)
- IP Address
- User Agent
- Details

Audit logs are stored in both the database and a log file for redundancy. 