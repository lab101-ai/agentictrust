# OAuth & OIDC-A API

All endpoints below are prefixed with `/api/oauth` unless otherwise noted.

This service implements a subset of [RFC 6749 OAuth 2.0] flows plus agent-specific extensions ("OIDC-A") used by **Agents**, **Users**, and **Tools** in the Agentic Trust ecosystem.

---

## 1. Authorization Code (PKCE) Flow

> **Browser / interactive login for *users or human-controlled agents*.**

### 1.1 `GET /authorize`

| Query Param | Required | Description |
|-------------|----------|-------------|
| `response_type` | Yes | Must be `code` |
| `client_id` | Yes | Agent `client_id` obtained during registration |
| `redirect_uri` | Yes | One of the URIs whitelisted for the agent |
| `scope` | Optional | Space-separated scopes (e.g. `read:tools write:tasks`) |
| `state` | Recommended |  Opaque value returned unchanged to client |
| `code_challenge` | Yes | [RFC 7636] PKCE code challenge (Base64URL-encoded SHA-256 of verifier) |
| `code_challenge_method` | Optional | `S256` *(default)* or `plain` |

Successful requests **302 Redirect** the browser to:

```
{redirect_uri}?code={authorization_code}&state={state}
```

If user consent is required, the endpoint returns:

```jsonc
{
  "consent_required": true,
  "client_id": "...",
  "requested_scopes": ["read:tools"],
  "user": { "user_id": "uuid", "username": "alice" }
}
```

The front-end should render a consent UI, then call `POST /authorize/decision` *(future)*.

---

## 2. Token Endpoint

`POST /token` — single endpoint implementing **three** grant types.

### 2.1 Client Credentials (`grant_type = client_credentials`)

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `grant_type` | string | Yes | Must be `client_credentials` |
| `client_id` | string | Yes | Agent `client_id` |
| `client_secret` | string | Yes | Agent secret |
| `scope` | string | Optional | Space-separated list; omitted → default scopes |
| `task_description` | string | Optional | Text stored in audit log |
| `required_tools` | string[] | Optional | Tool IDs that **must** be granted or request fails |
| `agent_type, agent_model, ...` | string | **✅ Required** by OIDC-A (§2.1) |

Example request:
```jsonc
{
  "grant_type": "client_credentials",
  "client_id": "2297b07d-…",
  "client_secret": "****",
  "scope": "read:tools write:tasks",
  "agent_type": "assistant",
  "agent_model": "gpt-4o",
  "agent_provider": "OpenAI"
}
```

Successful **200 OK** response:
```jsonc
{
  "access_token": "eyJhbGciOiJI…",
  "refresh_token": "dGVsOjEyMzQ…",
  "token_type": "Bearer",
  "expires_in": 3600,
  "scope": ["read:tools", "write:tasks"],
  "token_id": "uuid",
  "task_id": "uuid"
}
```

| Status | Reason |
|--------|--------|
| `400` | Invalid credentials, invalid parameters |
| `403` | Scope or tool not allowed by policy |
| `500` | Server error |

---

### 2.2 Authorization Code Exchange (`grant_type = authorization_code`)

```jsonc
{
  "grant_type": "authorization_code",
  "code": "{authorization_code}",
  "client_id": "…",
  "redirect_uri": "https://example.com/callback",
  "code_verifier": "{original PKCE verifier}"
}
```

Response equals *Client Credentials* format.

| Status | Reason |
|--------|--------|
| `400` | Invalid code / mismatch |
| `500` | Server error |

---

### 2.3 Refresh Token (`grant_type = refresh_token`)

```jsonc
{
  "grant_type": "refresh_token",
  "refresh_token": "<refresh>…",
  "scope": "read:tools" // optional — may further narrow scopes
}
```

Returns new access + refresh pair. Errors mimic 2.1.

---

## 3. Token Introspection

`POST /introspect`

```jsonc
{ "token": "<access|refresh token>" }
```

### Response
```jsonc
{
  "active": true,
  "token_id": "uuid",
  "client_id": "uuid",
  "exp": 1715630112,
  "iat": 1715626512,
  "scope": ["read:tools"],
  "agent": {
    "agent_type": "assistant",
    "agent_model": "gpt-4o",
    "agent_trust_level": "medium"
  },
  "task_id": "uuid",
  "parent_task_id": null
}
```
Inactive / expired tokens return `{ "active": false }`.

---

## 4. Token Revocation

`POST /revoke`

```jsonc
{ "token": "<access or refresh token>", "revoke_children": true }
```

Always replies **200 OK** *(per RFC 7009)*:
```jsonc
{ "message": "Token revoked successfully" }
```

---

## 5. Token Verification Helper

`POST /verify`

A convenience endpoint that wraps `introspect` + lineage validation.

Request:
```jsonc
{
  "token": "<access token>",
  "task_id": "uuid",              // optional expected task
  "parent_token": "<token>",      // optional ancestor validation
  "allow_clock_skew": true,
  "max_clock_skew_seconds": 86400
}
```

Successful **200 OK**:
```jsonc
{ "verified": true, "token_id": "uuid", "task_id": "uuid" }
```

Error codes:
| Status | Detail |
|--------|--------|
| `401` | `invalid_token` / `invalid_parent_token` |
| `403` | `task_lineage_invalid` |

---

## 6. Tool-Access Checks

### 6.1 `POST /check_token_access`
*Lightweight check; returns `access: true/false`*

```jsonc
{ "token": "<access>", "tool_id": "uuid" }
```

### 6.2 `POST /verify-tool-access`
*Strict check combining verification + OPA policy enforcement.*

```jsonc
{
  "token": "<access>",
  "tool_name": "summarize_text",
  "task_id": "uuid",
  "parent_token": "<token>" // optional
}
```

Successful **200 OK**: `{ "verified": true }`

| Status | Reason |
|--------|--------|
| `401` | Invalid / expired token |
| `403` | Tool not in scope or denied by policy |

---

## 7. Well-Known Discovery

Outside of `/api/oauth` prefix:

`GET /.well-known/openid-configuration`

Returns OIDC Discovery document pointing to `jwks_uri`, `token_endpoint`, etc.

---

## 8. Error Handling Summary

| Status | Meaning |
|--------|---------|
| `400` | Missing / invalid parameters |
| `401` | Invalid credentials / token |
| `403` | Denied by policy (OPA) |
| `404` | Resource not found (e.g. tool) |
| `500` | Internal server error |

---

### Notes & Best Practices

1. **Bearer tokens** must be sent using `Authorization: Bearer <token>` header on protected Agent & Tool endpoints.
2. Always store refresh tokens securely; they can mint new access tokens.
3. Scopes and tool grants are enforced by OPA; requesting unauthorized scopes returns `403`.
4. Timestamps in responses follow ISO-8601 UTC.

---

© 2025 Agentic Trust — OAuth & OIDC-A specification (draft)
