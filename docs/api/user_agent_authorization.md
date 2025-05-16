# User-Agent Authorization API

All endpoints below are prefixed with `/api/agents/users/{user_id}/authorizations`.

## 1. Create User-Agent Authorization

|| Method | Path | Auth |
||--------|------|------|
|| `POST` | `/` | Protected |

### Request Body (`CreateUserAgentAuthorizationRequest`)
```jsonc
{
  "agent_id": "uuid",
  "scopes": ["read:data", "write:tasks"],
  "constraints": {
    "time_restrictions": {
      "start_hour": 9,
      "end_hour": 17
    },
    "resources": {
      "allowed_resources": ["customer_data", "support_tickets"]
    }
  },
  "ttl_days": 30
}
```

### Response — `201 Created`
```jsonc
{
  "message": "User-Agent Authorization created successfully",
  "authorization": {
    "authorization_id": "uuid",
    "user_id": "uuid",
    "agent_id": "uuid",
    "scopes": ["read:data", "write:tasks"],
    "is_active": true,
    "expires_at": "ISO-8601",
    "created_at": "ISO-8601"
  }
}
```

## 2. List User-Agent Authorizations

|| Method | Path | Auth |
||--------|------|------|
|| `GET` | `/` | Protected |

### Query Parameters
- `agent_id`: Filter by specific agent
- `is_active`: Filter by active status

### Response
```jsonc
{
  "authorizations": [
    {
      "authorization_id": "uuid",
      "agent_id": "uuid",
      "scopes": ["read:data"],
      "is_active": true
    }
  ]
}
```

## 3. Get User-Agent Authorization

|| Method | Path | Auth |
||--------|------|------|
|| `GET` | `/{authorization_id}` | Protected |

### Response
```jsonc
{
  "authorization_id": "uuid",
  "user_id": "uuid",
  "agent_id": "uuid",
  "scopes": ["read:data", "write:tasks"],
  "constraints": {
    "time_restrictions": {
      "start_hour": 9,
      "end_hour": 17
    }
  },
  "is_active": true,
  "expires_at": "ISO-8601",
  "created_at": "ISO-8601"
}
```

## 4. Update User-Agent Authorization

|| Method | Path | Auth |
||--------|------|------|
|| `PUT` | `/{authorization_id}` | Protected |

### Request Body (`UpdateUserAgentAuthorizationRequest`)
```jsonc
{
  "scopes": ["read:data"],
  "constraints": {
    "time_restrictions": {
      "start_hour": 8,
      "end_hour": 18
    }
  },
  "is_active": true,
  "ttl_days": 60
}
```

### Response
```jsonc
{
  "authorization_id": "uuid",
  "user_id": "uuid",
  "agent_id": "uuid",
  "scopes": ["read:data"],
  "is_active": true,
  "updated_at": "ISO-8601"
}
```

## 5. Revoke User-Agent Authorization

|| Method | Path | Auth |
||--------|------|------|
|| `DELETE` | `/{authorization_id}` | Protected |

### Response — `200 OK`
```jsonc
{
  "message": "Authorization revoked successfully"
}
```

## Notes
- Authorizations can be time-limited and scope-restricted
- Constraints can include time restrictions and resource access limits
- Revoked authorizations immediately invalidate delegated tokens
