# Human-to-Agent Token Delegation API

## Delegation Endpoints

All endpoints below are prefixed with `/api/delegations`.

### 1. Create Delegation

|| Method | Path | Auth |
||--------|------|------|
|| `POST` | `/` | Protected |

#### Request Body (`DelegationCreate`)
```jsonc
{
  "principal_type": "user",
  "principal_id": "user_uuid",
  "delegate_id": "agent_uuid",
  "scope": ["read:data", "write:tasks"],
  "max_depth": 1,
  "constraints": {
    "time_restrictions": {
      "start_hour": 9,
      "end_hour": 17
    }
  },
  "ttl_hours": 24
}
```

#### Response — `201 Created`
```jsonc
{
  "grant_id": "uuid",
  "principal_type": "user",
  "principal_id": "user_uuid",
  "delegate_id": "agent_uuid",
  "scope": ["read:data", "write:tasks"],
  "max_depth": 1,
  "constraints": {
    "time_restrictions": {
      "start_hour": 9,
      "end_hour": 17
    }
  },
  "created_at": "ISO-8601",
  "expires_at": "ISO-8601"
}
```

### 2. Get Delegation

|| Method | Path | Auth |
||--------|------|------|
|| `GET` | `/{grant_id}` | Protected |

#### Response
```jsonc
{
  "grant_id": "uuid",
  "principal_type": "user",
  "principal_id": "user_uuid",
  "delegate_id": "agent_uuid",
  "scope": ["read:data", "write:tasks"],
  "max_depth": 1,
  "constraints": {
    "time_restrictions": {
      "start_hour": 9,
      "end_hour": 17
    }
  },
  "created_at": "ISO-8601",
  "expires_at": "ISO-8601"
}
```

### 3. List Principal Delegations

|| Method | Path | Auth |
||--------|------|------|
|| `GET` | `/principal/{principal_id}` | Protected |

#### Response
```jsonc
[
  {
    "grant_id": "uuid",
    "principal_type": "user",
    "principal_id": "user_uuid",
    "delegate_id": "agent_uuid",
    "scope": ["read:data"],
    "created_at": "ISO-8601"
  }
]
```

### 4. Revoke Delegation

|| Method | Path | Auth |
||--------|------|------|
|| `DELETE` | `/{grant_id}` | Protected |

#### Response — `200 OK`
```jsonc
{
  "message": "revoked"
}
```

## OAuth Delegation Endpoints

All endpoints below are prefixed with `/api/oauth/delegate`.

### 1. Delegate Token

|| Method | Path | Auth |
||--------|------|------|
|| `POST` | `/` | Protected |

#### Request Body (`DelegateTokenRequest`)
```jsonc
{
  "delegator_token": "original_user_token",
  "agent_id": "uuid",
  "scopes": ["read:data"],
  "task_description": "Analyze customer support tickets",
  "task_id": "uuid",
  "purpose": "Customer support analysis"
}
```

#### Response — `200 OK`
```jsonc
{
  "access_token": "delegated_agent_token",
  "token_id": "uuid",
  "task_id": "uuid",
  "expires_in": 3600,
  "scopes": ["read:data"],
  "delegation_details": {
    "delegator_id": "user_uuid",
    "agent_id": "agent_uuid",
    "delegation_time": "ISO-8601"
  }
}
```

## Notes
- Delegation is subject to User-Agent Authorization policies
- Tokens can be further restricted compared to original authorization
- Delegation chain provides full audit trail
- OPA policies are enforced before delegation is created
