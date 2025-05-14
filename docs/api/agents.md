# Agents API

All endpoints below are prefixed with `/api/agents`.

---

## 1. Register Agent

| Method | Path | Auth |
|--------|------|------|
| `POST` | `/register` | Public |

Creates a new agent record and issues a **client ID**, **client secret**, and a one-time `registration_token` used for activation.

### Request Body (`RegisterAgentRequest`)
```jsonc
{
  "agent_name": "string, required",        // Display name
  "description": "string, optional",       // Free-form notes
  "max_scope_level": "restricted | full", // Default: restricted
  "tool_ids": ["tool-uuid", "…"],         // Tools allowed on creation
  "agent_type": "string, optional",        // OIDC-A metadata
  "agent_model": "string, optional",
  "agent_version": "string, optional",
  "agent_provider": "string, optional"
}
```

### Successful Response — `201 Created`
```jsonc
{
  "message": "Agent registered successfully",
  "agent": {
    "client_id": "uuid",
    "agent_name": "…",
    "is_active": false,
    "registration_token": "…",
    "agent_type": "…",
    "agent_model": "…",
    "agent_version": "…",
    "agent_provider": "…",
    "created_at": "ISO-8601",
    "updated_at": "ISO-8601",
    "tools": []
  },
  "credentials": {
    "client_id": "uuid",
    "client_secret": "string",
    "registration_token": "string"
  }
}
```

| Status | Reason |
|--------|--------|
| `400`  | Missing / invalid payload |
| `500`  | Server error |

---

## 2. Activate Agent

| Method | Path | Auth |
|--------|------|------|
| `POST` | `/activate` | Public |

Marks the agent as *active* using the `registration_token`.

### Request Body (`ActivateAgentRequest`)
```jsonc
{ "registration_token": "string" }
```

### Response — `200 OK`
```jsonc
{
  "message": "Agent activated successfully",
  "agent": { /* agent object with is_active=true */ }
}
```

| Status | Reason |
|--------|--------|
| `400`  | Invalid token |
| `404`  | Agent not found |
| `500`  | Server error |

---

## 3. List Agents

| Method | Path | Auth |
|--------|------|------|
| `GET` | `/list` | Protected* |

Returns an array of all agent objects.

### Response — `200 OK`
```jsonc
{ "agents": [ { /* agent */ }, … ] }
```

---

## 4. Get Agent by ID

| Method | Path | Auth |
|--------|------|------|
| `GET` | `/{client_id}` | Protected* |

Returns a single agent object by its `client_id`.

### Response — `200 OK`
```jsonc
{
  "client_id": "uuid",
  "agent_name": "…",
  "description": "…",
  "max_scope_level": "restricted",
  "is_active": true,
  "agent_type": "…",
  "agent_model": "…",
  "agent_version": "…",
  "agent_provider": "…",
  "created_at": "ISO-8601",
  "updated_at": "ISO-8601",
  "tools": [ { "tool_id": "uuid", "name": "…" } ]
}
```

| Status | Reason |
|--------|--------|
| `404`  | Agent not found |
| `500`  | Server error |

---

## 5. Update Agent

| Method | Path | Auth |
|--------|------|------|
| `PUT` | `/{client_id}` | Protected* |

Updates any mutable fields. Body matches `UpdateAgentRequest` (all fields optional).

### Request Example
```jsonc
{
  "description": "Updated description",
  "tool_ids": ["tool-uuid-1", "tool-uuid-2"]
}
```

### Response — `200 OK`
```jsonc
{
  "message": "Agent updated successfully",
  "agent": { /* updated agent object */ }
}
```

| Status | Reason |
|--------|--------|
| `400`  | Invalid payload |
| `404`  | Agent not found |
| `500`  | Server error |

---

## 6. Delete Agent

| Method | Path | Auth |
|--------|------|------|
| `DELETE` | `/{client_id}` | Protected* |

Deletes the specified agent. Associated OPA records are also removed.

### Response — `200 OK`
```jsonc
{ "message": "Agent deleted successfully" }
```

| Status | Reason |
|--------|--------|
| `404`  | Agent not found |
| `500`  | Server error |

---

## 7. Manage Agent Tools

| Action | Method & Path |
|--------|---------------|
| List tools | `GET /{client_id}/tools` |
| Add tool   | `POST /{client_id}/tools/{tool_id}` |
| Remove tool| `DELETE /{client_id}/tools/{tool_id}` |

### Responses
| Status | Meaning |
|--------|---------|
| `200` | Tool added / removed successfully |
| `404` | Agent or tool not found |
| `500` | Server error |

---

## 8. Current Agent *(TBD)*

Returns the authenticated agent’s profile once the auth layer is available.

| Method | Path | Current Behaviour |
|--------|------|------------------|
| `GET` | `/me` | `501 Not Implemented` |

### Notes
*Endpoints marked **Protected*** will require OAuth bearer tokens once the auth layer is finalized.

All timestamps are returned in ISO-8601 UTC format.
