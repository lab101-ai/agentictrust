# OAuth Flow Diagrams

## Agent Registration Flow

```
┌──────────┐                                  ┌──────────────┐                              ┌─────────────┐
│          │                                  │              │                              │             │
│  Admin/  │                                  │ AgenticTrust │                              │  Agent      │
│  Owner   │                                  │ OAuth Server │                              │  Registry   │
│          │                                  │              │                              │             │
└────┬─────┘                                  └──────┬───────┘                              └──────┬──────┘
     │                                               │                                             │
     │  1. Register Agent                            │                                             │
     │  (agent_name, description,                    │                                             │
     │   allowed_tools: ["file_read",                │                                             │
     │    "db_query", "api_call"],                   │                                             │
     │   resource_access: ["github",                 │                                             │
     │    "jira", "s3"],                             │                                             │
     │   max_scope_level: "restricted")              │                                             │
     │ ──────────────────────────────────────────►   │                                             │
     │                                               │                                             │
     │                                               │  2. Validate Registration                   │
     │                                               │  & Generate Credentials                     │
     │                                               │ ◄─────────┐                                 │
     │                                               │           │                                 │
     │                                               │  3. Store Agent Profile                     │
     │                                               │ ──────────────────────────────────────────► │
     │                                               │           │                                 │
     │                                               │           │                                 │
     │  4. Return Agent Credentials                  │           │                                 │
     │  (client_id, client_secret,                   │           │                                 │
     │   allowed_scopes,                             │           │                                 │
     │   registration_token)                         │           │                                 │
     │ ◄──────────────────────────────────────────   │           │                                 │
     │                                               │           │                                 │
     │  5. Confirm Registration                      │           │                                 │
     │  (registration_token)                         │           │                                 │
     │ ──────────────────────────────────────────►   │           │                                 │
     │                                               │           │                                 │
     │                                               │  6. Activate Agent                          │
     │                                               │ ──────────────────────────────────────────► │
     │                                               │           │                                 │
     │  7. Return Activation Status                  │           │                                 │
     │ ◄──────────────────────────────────────────   │           │                                 │
     │                                               │           │                                 │
     ▼                                               ▼           ▼                                 ▼
```

## Basic Client Credentials Flow

```
┌──────────┐                                  ┌──────────────┐                              ┌─────────────┐
│          │                                  │              │                              │             │
│  Agent   │                                  │ AgenticTrust │                              │  Protected  │
│  Client  │                                  │ OAuth Server │                              │  Resource   │
│          │                                  │              │                              │             │
└────┬─────┘                                  └──────┬───────┘                              └──────┬──────┘
     │                                               │                                             │
     │  1. Request Token                             │                                             │
     │  (client_id, client_secret, scope,            │                                             │
     │   task_id, task_description)                  │                                             │
     │ ──────────────────────────────────────────►   │                                             │
     │                                               │                                             │
     │                                               │  2. Validate Client                         │
     │                                               │  & Check Scopes                             │
     │                                               │  & Verify Task Context                      │
     │                                               │ ◄─────────┐                                 │
     │                                               │           │                                 │
     │                                               │           │                                 │
     │  3. Return Access Token                       │           │                                 │
     │  (access_token, refresh_token, scope,         │           │                                 │
     │   task_id, task_bound: true)                  │           │                                 │
     │ ◄──────────────────────────────────────────   │           │                                 │
     │                                               │           │                                 │
     │                                               │           │                                 │
     │  4. Request Resource                          │           │                                 │
     │  (Bearer access_token, task_id)               │           │                                 │
     │ ──────────────────────────────────────────────────────────────────────────────────────►     │
     │                                               │           │                                 │
     │                                               │           │                                 │
     │                                               │  5. Verify Token                            │
     │                                               │  & Task Context                             │
     │                                               │ ◄────────────────────────────────────────── │
     │                                               │           │                                 │
     │                                               │           │                                 │
     │                                               │  6. Confirm                                 │
     │                                               │  Token & Task Validity                      │
     │                                               │ ──────────────────────────────────────────► │
     │                                               │           │                                 │
     │                                               │           │                                 │
     │  7. Return Resource                           │           │                                 │
     │ ◄────────────────────────────────────────────────────────────────────────────────────────── │
     │                                               │           │                                 │
     ▼                                               ▼           ▼                                 ▼
```

## Task-Level Verification with Token Lineage

```
┌──────────┐                                  ┌──────────────┐                              ┌─────────────┐
│          │                                  │              │                              │             │
│  Parent  │                                  │ AgenticTrust │                              │  Agent      │
│  Agent   │                                  │ OAuth Server │                              │  Registry   │
│          │                                  │              │                              │             │
└────┬─────┘                                  └──────┬───────┘                              └──────┬──────┘
     │                                               │                                             │
     │  1. Request Parent Token                      │                                             │
     │  (client_id, client_secret,                   │                                             │
     │   scope: ["file_read:github"],                │                                             │
     │   task_id=parent_task_id,                     │                                             │
     │   task_description: "Code Review",            │                                             │
     │   required_tools: ["file_read"],              │                                             │
     │   required_resources: ["github"])             │                                             │
     │ ──────────────────────────────────────────►   │                                             │
     │                                               │                                             │
     │                                               │  2. Verify Agent Registration               │
     │                                               │  & Allowed Capabilities                     │
     │                                               │  (Check against registered                  │
     │                                               │   tools and resources)                      │
     │                                               │ ──────────────────────────────────────────► │
     │                                               │                                             │
     │                                               │  3. Return Agent Profile                    │
     │                                               │  (max_scope_level,                          │
     │                                               │   allowed_tools,                            │
     │                                               │   allowed_resources)                        │
     │                                               │ ◄────────────────────────────────────────── │
     │                                               │                                             │
     │                                               │  4. Validate Request                        │
     │                                               │  Against Profile                            │
     │                                               │ ◄─────────┐                                 │
     │                                               │           │                                 │
     │  5. Return Parent Token                       │           │                                 │
     │  (access_token, refresh_token,                │           │                                 │
     │   scope: ["file_read:github"],                │           │                                 │
     │   task_id=parent_task_id,                     │           │                                 │
     │   allowed_tools: ["file_read"],               │           │                                 │
     │   allowed_resources: ["github"])              │           │                                 │
     │ ◄──────────────────────────────────────────   │           │                                 │
     │                                               │           │                                 │
     ▼                                               │           │                                 │
                                                     │           │                                 │
┌──────────┐                                         │           │                                 │
│          │                                         │           │                                 │
│  Child   │                                         │           │                                 │
│  Agent   │                                         │           │                                 │
│          │                                         │           │                                 │
└────┬─────┘                                         │           │                                 │
     │                                               │           │                                 │
     │  6. Request Child Token                       │           │                                 │
     │  (client_id, client_secret,                   │           │                                 │
     │   scope: ["file_read:github/specific"],       │           │                                 │
     │   task_id=child_task_id,                      │           │                                 │
     │   parent_task_id, parent_token,               │           │                                 │
     │   task_description: "Review File",            │           │                                 │
     │   required_tools: ["file_read"],              │           │                                 │
     │   required_resources: ["github"])             │           │                                 │
     │ ──────────────────────────────────────────►   │           │                                 │
     │                                               │           │                                 │
     │                                               │  7. Verify Agent & Parent                   │
     │                                               │  Token Lineage                              │
     │                                               │ ──────────────────────────────────────────► │
     │                                               │                                             │
     │                                               │  8. Validate Scope                          │
     │                                               │  Inheritance & Restrictions                 │
     │                                               │  (Check if child scope                      │
     │                                               │   subset of parent)                         │
     │                                               │ ◄─────────┐                                 │
     │                                               │           │                                 │
     │  9. Return Child Token                        │           │                                 │
     │  (access_token, refresh_token,                │           │                                 │
     │   scope: ["file_read:github/specific"],       │           │                                 │
     │   task_id=child_task_id,                      │           │                                 │
     │   parent_task_id,                             │           │                                 │
     │   allowed_tools: ["file_read"],               │           │                                 │
     │   allowed_resources: ["github"],              │           │                                 │
     │   scope_inheritance: "restricted")            │           │                                 │
     │ ◄──────────────────────────────────────────   │           │                                 │
     │                                               │           │                                 │
     ▼                                               ▼           ▼                                 ▼
```

## Token Verification Process

```
┌──────────┐                                  ┌──────────────┐                              ┌─────────────┐
│          │                                  │              │                              │             │
│  Agent   │                                  │ AgenticTrust │                              │  Audit Log  │
│  Client  │                                  │ OAuth Server │                              │  System     │
│          │                                  │              │                              │             │
└────┬─────┘                                  └──────┬───────┘                              └──────┬──────┘
     │                                               │                                             │
     │  1. Verify Token                              │                                             │
     │  (token, scope: ["file_read:github"],         │                                             │
     │   task_id, parent_task_id,                    │                                             │
     │   task_description: "Review PR",              │                                             │
     │   required_tools: ["file_read"])              │                                             │
     │ ──────────────────────────────────────────►   │                                             │
     │                                               │                                             │
     │                                               │  2. Decode Token                            │
     │                                               │  & Extract Task Context                     │
     │                                               │ ◄─────────┐                                 │
     │                                               │           │                                 │
     │                                               │  3. Check Historical                        │
     │                                               │  Task Execution                             │
     │                                               │ ──────────────────────────────────────────► │
     │                                               │                                             │
     │                                               │  4. Return Task History                     │
     │                                               │  (previous_tasks,                           │
     │                                               │   execution_patterns)                       │
     │                                               │ ◄────────────────────────────────────────── │
     │                                               │                                             │
     │                                               │  5. Verify Token Status                     │
     │                                               │  & Task Lineage                             │
     │                                               │ ◄─────────┐                                 │
     │                                               │           │                                 │
     │                                               │  6. Analyze Task                            │
     │                                               │  Context & History                          │
     │                                               │ ◄─────────┘                                 │
     │                                               │                                             │
     │                                               │  7. Log Verification                        │
     │                                               │  with Task Context                          │
     │                                               │ ──────────────────────────────────────────► │
     │                                               │                                             │
     │  8. Return Verification Result                │                                             │
     │  (is_valid: true,                             │                                             │
     │   scope: ["file_read:github"],                │                                             │
     │   task_context_valid: true,                   │                                             │
     │   historical_pattern_match: true)             │                                             │
     │ ◄──────────────────────────────────────────   │                                             │
     │                                               │                                             │
     ▼                                               ▼                                             ▼
```

## Token Introspection and Revocation

```
┌──────────┐                                  ┌──────────────┐                              ┌─────────────┐
│          │                                  │              │                              │             │
│  Admin   │                                  │ AgenticTrust │                              │  Audit Log  │
│  Client  │                                  │ OAuth Server │                              │  System     │
│          │                                  │              │                              │             │
└────┬─────┘                                  └──────┬───────┘                              └──────┬──────┘
     │                                               │                                             │
     │  1. Introspect Token                          │                                             │
     │  (token, include_task_history: true)          │                                             │
     │ ──────────────────────────────────────────►   │                                             │
     │                                               │                                             │
     │                                               │  2. Check Token                             │
     │                                               │  in Database                                │
     │                                               │ ◄─────────┐                                 │
     │                                               │           │                                 │
     │                                               │  3. Fetch Task History                      │
     │                                               │ ──────────────────────────────────────────► │
     │                                               │                                             │
     │                                               │  4. Return Task History                     │
     │                                               │  (task_chain, execution_logs)              │
     │                                               │ ◄────────────────────────────────────────── │
     │                                               │                                             │
     │                                               │  5. Analyze Token Usage                     │
     │                                               │  & Task Patterns                            │
     │                                               │ ◄─────────┐                                 │
     │                                               │           │                                 │
     │  6. Return Token Details                      │           │                                 │
     │  (active: true,                               │           │                                 │
     │   scope: ["file_read:github"],                │           │                                 │
     │   client_id: "agent_123",                     │           │                                 │
     │   exp: 1234567890,                            │           │                                 │
     │   task_history: {                             │           │                                 │
     │     current_task: "Review PR",                │           │                                 │
     │     parent_tasks: ["Code Review"],            │           │                                 │
     │     execution_pattern: "normal",              │           │                                 │
     │     risk_assessment: "low"                    │           │                                 │
     │   })                                          │           │                                 │
     │ ◄──────────────────────────────────────────   │           │                                 │
     │                                               │           │                                 │
     │  7. Revoke Token                              │           │                                 │
     │  (token,                                      │           │                                 │
     │   reason: "suspicious_task_pattern",          │           │                                 │
     │   affected_task_chain: ["task1", "task2"])    │           │                                 │
     │ ──────────────────────────────────────────►   │           │                                 │
     │                                               │           │                                 │
     │                                               │  8. Mark Token as Revoked                   │
     │                                               │  & Update Task Status                       │
     │                                               │ ◄─────────┐                                 │
     │                                               │           │                                 │
     │                                               │  9. Log Revocation                          │
     │                                               │  with Task Context                          │
     │                                               │ ──────────────────────────────────────────► │
     │                                               │                                             │
     │  10. Return Revocation Status                 │                                             │
     │  (revoked: true,                              │                                             │
     │   affected_tasks_terminated: true)            │                                             │
     │ ◄──────────────────────────────────────────   │                                             │
     │                                               │                                             │
     ▼                                               ▼                                             ▼
```

## Parent-Child Token Lineage Database Model

```
┌───────────────────────────┐       ┌────────────────────────────┐       ┌────────────────────────────┐
│         Agents            │       │      IssuedTokens          │       │      TaskAuditLog          │
├───────────────────────────┤       ├────────────────────────────┤       ├────────────────────────────┤
│ client_id (PK)            │       │ token_id (PK)              │       │ log_id (PK)                │
│ client_secret_hash        │       │ client_id (FK)             │◄──────┤ client_id                  │
│ agent_name                │       │ access_token_hash          │       │ token_id (FK)              │
│ description               │       │ refresh_token_hash         │       │ access_token_hash          │
│ registered_allowed_tools  │       │ scope                      │       │ task_id                    │
│ registered_allowed_res    │       │ granted_tools              │       │ parent_task_id             │
│ max_scope_level           │       │ granted_resources          │       │ event_type                 │
│ registration_token        │       │ task_id                    │       │ timestamp                  │
│ is_active                 │       │ parent_task_id             │       │ status                     │
│ created_at                │       │ parent_token_id (FK)       │       │ source_ip                  │
│ updated_at                │       │ task_description           │       │ details (JSONB)            │
└─────────┬─────────────────┘       │ scope_inheritance_type     │       └────────────────────────────┘
          │                         │ issued_at                  │                     ▲
          │                         │ expires_at                 │                     │
          │                         │ is_revoked                 │                     │
          │                         │ revoked_at                 │                     │
          │                         │ revocation_reason          │                     │
          │                         └──────────┬─────────────────┘                     │
          │                                    │                                       │
          └────────────────────────────────────┼───────────────────────────────────────┘
                                               │
                                               │
                                               ▼
                                       ┌─────────────────┐
                                       │  Self-Reference │
                                       │  parent_token   │
                                       └─────────────────┘
```

## Task Verification Decision Flow

```
┌──────────┐                                  ┌──────────────┐                              ┌─────────────┐
│          │                                  │              │                              │             │
│ Agent/   │                                  │ AgenticTrust │                              │ Database &  │
│ Resource │                                  │ OAuth Server │                              │  Audit Log  │
│          │                                  │              │                              │             │
└────┬─────┘                                  └──────┬───────┘                              └──────┬──────┘
     │                                               │                                             │
     │  1. Verify Token Request                      │                                             │
     │  (access_token, required_scope,               │                                             │
     │   task_id, context)                           │                                             │
     │ ──────────────────────────────────────────►   │                                             │
     │                                               │                                             │
     │                                               │  2. Initial Token Validation                │
     │                                               │  - Find token by hash                       │
     │                                               │  - Check revocation                         │
     │                                               │  - Check expiration                         │
     │                                               │ ──────────────────────────────────────────► │
     │                                               │                                             │
     │                                               │  3. Return Token Record                     │
     │                                               │  (scope, task_id, lineage)                  │
     │                                               │ ◄────────────────────────────────────────── │
     │                                               │                                             │
     │                                               │  4. Scope & Task Validation                 │
     │                                               │  - Verify scope subset                      │
     │                                               │  - Match task_id                            │
     │                                               │ ◄─────────┐                                 │
     │                                               │           │                                 │
     │                                               │  5. Lineage Validation                      │
     │                                               │  - Check parent token                       │
     │                                               │  - Verify inheritance                       │
     │                                               │ ──────────────────────────────────────────► │
     │                                               │                                             │
     │                                               │  6. Return Parent Token                     │
     │                                               │  & Audit History                            │
     │                                               │ ◄────────────────────────────────────────── │
     │                                               │                                             │
     │                                               │  7. Risk Assessment                         │
     │                                               │  - Analyze patterns                         │
     │                                               │  - Check violations                         │
     │                                               │ ◄─────────┐                                 │
     │                                               │           │                                 │
     │                                               │  8. Log Verification                        │
     │                                               │  Result & Context                           │
     │                                               │ ──────────────────────────────────────────► │
     │                                               │                                             │
     │  9. Return Verification Result                │                                             │
     │  (status, context, risk_level)                │                                             │
     │ ◄──────────────────────────────────────────── │                                             │
     │                                               │                                             │
     ▼                                               ▼                                             ▼
``` 