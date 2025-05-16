# Policy-Based Authorization API

All endpoints below are prefixed with `/api/policies`.

## 1. Create Policy

|| Method | Path | Auth |
||--------|------|------|
|| `POST` | `/` | Protected |

### Request Body (`CreatePolicyRequest`)
```jsonc
{
  "name": "Customer Support Policy",
  "description": "Policy for customer support agents",
  "scopes": ["read:tickets", "update:tickets"],
  "effect": "allow",
  "priority": 100,
  "conditions": {
    "user": {
      "department": "Support",
      "role": "Agent"
    },
    "resource": {
      "type": "ticket",
      "status": ["open", "pending"]
    }
  }
}
```

### Response — `201 Created`
```jsonc
{
  "message": "Policy created successfully",
  "policy": {
    "policy_id": "uuid",
    "name": "Customer Support Policy",
    "description": "Policy for customer support agents",
    "scopes": ["read:tickets", "update:tickets"],
    "effect": "allow",
    "priority": 100,
    "conditions": {
      "user": {
        "department": "Support",
        "role": "Agent"
      },
      "resource": {
        "type": "ticket",
        "status": ["open", "pending"]
      }
    }
  }
}
```

## 2. List Policies

|| Method | Path | Auth |
||--------|------|------|
|| `GET` | `/` | Protected |

### Response
```jsonc
{
  "policies": [
    {
      "policy_id": "uuid",
      "name": "Customer Support Policy",
      "description": "Policy for customer support agents",
      "scopes": ["read:tickets", "update:tickets"],
      "effect": "allow",
      "priority": 100
    }
  ]
}
```

## 3. Get Policy

|| Method | Path | Auth |
||--------|------|------|
|| `GET` | `/{policy_id}` | Protected |

### Response
```jsonc
{
  "policy_id": "uuid",
  "name": "Customer Support Policy",
  "description": "Policy for customer support agents",
  "scopes": ["read:tickets", "update:tickets"],
  "effect": "allow",
  "priority": 100,
  "conditions": {
    "user": {
      "department": "Support",
      "role": "Agent"
    },
    "resource": {
      "type": "ticket",
      "status": ["open", "pending"]
    }
  }
}
```

## 4. Update Policy

|| Method | Path | Auth |
||--------|------|------|
|| `PUT` | `/{policy_id}` | Protected |

### Request Body (`UpdatePolicyRequest`)
```jsonc
{
  "name": "Updated Support Policy",
  "description": "Updated policy for customer support agents",
  "scopes": ["read:tickets", "update:tickets", "delete:tickets"],
  "effect": "allow",
  "priority": 200,
  "conditions": {
    "user": {
      "department": "Support",
      "role": ["Agent", "Manager"]
    }
  }
}
```

### Response
```jsonc
{
  "message": "Policy updated successfully",
  "policy": {
    "policy_id": "uuid",
    "name": "Updated Support Policy",
    "description": "Updated policy for customer support agents",
    "scopes": ["read:tickets", "update:tickets", "delete:tickets"],
    "effect": "allow",
    "priority": 200,
    "conditions": {
      "user": {
        "department": "Support",
        "role": ["Agent", "Manager"]
      }
    }
  }
}
```

## 5. Delete Policy

|| Method | Path | Auth |
||--------|------|------|
|| `DELETE` | `/{policy_id}` | Protected |

### Response — `200 OK`
```jsonc
{
  "message": "Policy deleted successfully"
}
```

## 6. Check Policy

|| Method | Path | Auth |
||--------|------|------|
|| `POST` | `/check` | Protected |

### Request Body (`PolicyCheckRequest`)
```jsonc
{
  "auth": {
    "user_id": "uuid",
    "username": "john.doe",
    "department": "Support",
    "partner": "acme",
    "scopes": ["read:tickets", "update:tickets"],
    "token_id": "uuid",
    "parent_token_id": "uuid"
  },
  "request": {
    "action": "read",
    "resource": {
      "type": "ticket",
      "id": "ticket-123",
      "status": "open"
    }
  }
}
```

### Response
```jsonc
{
  "allowed": true,
  "message": "Access granted",
  "decision_id": "uuid"
}
```

## Notes
- Policies define complex authorization rules
- Can restrict access based on user attributes, resource types, and actions
- Integrated with Open Policy Agent (OPA) for enforcement
- Policy priority determines evaluation order (higher priority policies are evaluated first)
- Effect can be "allow" or "deny"
